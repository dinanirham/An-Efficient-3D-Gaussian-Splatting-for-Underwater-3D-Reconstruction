"""M3: quantization-aware vector quantization of per-primitive attributes.

Three codebooks -- DC colour, scale, rotation.  Four departures from the
reference implementation, each forced by this baseline or by the composition:

**No SH codebook (CD-9).**  The reference groups parameters into four
codebooks, the largest covering the 45 higher-order spherical-harmonic
coefficients.  SeaSplat sets `sh_degree = 0`, so `_features_rest` is
`(N, 0, 3)` -- that block does not exist.  Per-primitive storage is 14 floats,
not 59, of which quantization can address 10; position and opacity are excluded
structurally.  The achievable ratio is therefore a factor of a few rather than
the order of magnitude the terrestrial literature reports, and any comparison
against a published figure has to be renormalised to a 14-float baseline first.

**Position and opacity are never quantized.**  Sharing positions makes distinct
primitives coincide, and opacity is a single scalar with nothing to gain.  This
is also what keeps quantization structurally isolated from the two quantities
SeaSplat's well-posedness argument depends on most -- the depth map, which
comes from position, and the opacity field that `L_op` polices.

**Quantize before activation.**  Scale is clustered pre-`exp` and rotation
pre-normalisation, so that Euclidean distance in the clustered space is
meaningful; post-activation, equal codebook error would mean wildly different
geometric error at different magnitudes.  Implemented by overriding the *raw*
parameter and letting the model's existing activation apply.

**Pruning invalidates the codebook (the QAT x simplification conflict).**  This
conflict does not exist for post-hoc quantization and is created by choosing
quantization-aware training: the assignment vector is per-primitive, so M2's
`prune_points` silently desynchronises it from the model.  Handled by
index-selecting `nn_index` alongside every other per-primitive tensor and by
forcing a full reassignment after each simplification event.
"""

from __future__ import annotations

from typing import Optional

import torch


class VectorQuantizer:
    """One K-means codebook over one parameter group."""

    def __init__(
        self,
        name: str,
        num_clusters: int,
        num_iters: int = 1,
        chunk: int = 65536,
    ) -> None:
        self.name = name
        self.num_clusters = int(num_clusters)
        self.num_iters = int(num_iters)
        self.chunk = int(chunk)
        self.centers: Optional[torch.Tensor] = None   # (K, D)
        self.nn_index: Optional[torch.Tensor] = None  # (N,)
        self.vec_dim = 0

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _flatten(feat: torch.Tensor) -> torch.Tensor:
        return feat.detach().reshape(feat.shape[0], -1)

    def _init_centers(self, feat: torch.Tensor, max_samples: int = 200_000) -> None:
        """k-means++ seeding, on a subsample when the population is large.

        The reference implementation seeds from `randperm`, i.e. uniformly at
        random.  That is a real defect rather than a stylistic difference: two
        seeds can land in the same dense region while another region gets none,
        and Lloyd iterations cannot recover from it -- the result is a centroid
        straddling two clusters and a wasted codeword.  Wasted codewords mean
        higher quantization error at identical storage, which is precisely the
        quantity this mechanism is being measured on.

        k-means++ costs O(k * m) one-off.  The subsample bounds `m` so that
        cost stays fixed as the primitive count grows; the Lloyd iterations
        afterwards still run against the full population.
        """
        n = feat.shape[0]
        k = min(self.num_clusters, n)
        if k < self.num_clusters:
            # Fewer primitives than codewords: the codebook cannot be filled,
            # and silently shrinking it would misreport the compression ratio.
            print(
                f"[vq:{self.name}] WARNING: only {n} primitives for "
                f"{self.num_clusters} clusters; using k={k}"
            )
            self.num_clusters = k

        sub = feat
        if n > max_samples:
            sub = feat[torch.randperm(n, device=feat.device)[:max_samples]]
        m = sub.shape[0]

        centers = torch.empty((k, sub.shape[1]), device=sub.device, dtype=sub.dtype)
        first = int(torch.randint(m, (1,), device=sub.device).item())
        centers[0] = sub[first]
        closest = (sub - centers[0]).pow(2).sum(dim=1)

        for i in range(1, k):
            total = closest.sum()
            if not torch.isfinite(total) or total <= 0:
                # Every remaining point coincides with a centre; the rest of
                # the codebook cannot be filled meaningfully, so fall back to
                # uniform picks rather than emitting NaNs.
                pick = int(torch.randint(m, (1,), device=sub.device).item())
            else:
                pick = int(torch.multinomial(closest, 1).item())
            centers[i] = sub[pick]
            closest = torch.minimum(closest, (sub - centers[i]).pow(2).sum(dim=1))

        self.centers = centers

    def _reseed_empty(self, feat: torch.Tensor) -> int:
        """Move unused codewords to the worst-represented points.

        An empty cluster is a codeword that costs storage and represents
        nothing.  Reseeding it at the point currently farthest from its own
        centre both reclaims the codeword and attacks the largest single
        source of quantization error.
        """
        counts = torch.bincount(self.nn_index, minlength=self.num_clusters)
        empty = (counts == 0).nonzero(as_tuple=True)[0]
        if empty.numel() == 0:
            return 0
        residual = (feat - self.centers[self.nn_index]).pow(2).sum(dim=1)
        take = min(empty.numel(), feat.shape[0])
        far = torch.topk(residual, take).indices
        self.centers[empty[:take]] = feat[far]
        return int(take)

    def _assign(self, feat: torch.Tensor) -> None:
        """Expensive half: recompute assignments (chunked to bound memory)."""
        parts = []
        for block in feat.split(self.chunk, dim=0):
            parts.append(torch.cdist(block, self.centers).argmin(dim=1))
        self.nn_index = torch.cat(parts)

    def _update_centers(self, feat: torch.Tensor) -> None:
        """Cheap half: re-average within the cached partition.

        This asymmetry is the reference method's enabling trick.  Both halves
        of K-means produce valid centroids; only the *partition* goes stale, so
        the costly reassignment can run every `t` iterations while the centres
        track the drifting parameters continuously.  It is why the training
        overhead is a small factor rather than orders of magnitude.

        Clusters emptied by pruning keep their previous centre.  They are
        unreferenced, so the value is irrelevant -- but leaving them as zeros
        or NaN would corrupt a later reassignment.
        """
        sums = torch.zeros_like(self.centers)
        counts = torch.zeros(
            self.num_clusters, device=feat.device, dtype=feat.dtype
        )
        sums.index_add_(0, self.nn_index, feat)
        counts.index_add_(0, self.nn_index, torch.ones_like(feat[:, 0]))
        nonempty = counts > 0
        if nonempty.any():
            self.centers[nonempty] = (
                sums[nonempty] / counts[nonempty].unsqueeze(-1)
            )

    # -- public ------------------------------------------------------------

    def quantize(self, param: torch.Tensor, assign: bool) -> torch.Tensor:
        """Return the straight-through quantized parameter, shaped like `param`.

        Forward yields the centroid; backward routes the gradient to `param`,
        so the optimizer keeps updating the *unquantized* values and can move
        them somewhere that quantizes well.  Clustering after training instead
        of during it has neither property, which is the failure the
        quantization-aware formulation exists to prevent.
        """
        feat = self._flatten(param)
        if self.vec_dim == 0:
            self.vec_dim = feat.shape[1]

        if self.centers is None:
            self._init_centers(feat)
            assign = True

        stale = (
            self.nn_index is None
            or self.nn_index.shape[0] != feat.shape[0]
        )
        if assign or stale:
            for _ in range(max(1, self.num_iters)):
                self._assign(feat)
                if self._reseed_empty(feat):
                    self._assign(feat)
                self._update_centers(feat)
        else:
            self._update_centers(feat)

        sampled = self.centers[self.nn_index]
        flat_param = param.reshape(param.shape[0], -1)
        # Straight-through estimator.
        q = flat_param - flat_param.detach() + sampled
        return q.reshape(param.shape)

    def prune(self, keep_mask: torch.Tensor) -> None:
        """Keep the assignment vector aligned when primitives are removed.

        Without this the codebook silently desynchronises from the model:
        `nn_index` would still have the pre-prune length, so either the gather
        raises, or -- worse, if lengths happen to line up again later -- every
        primitive renders with another primitive's colour.
        """
        if self.nn_index is not None:
            self.nn_index = self.nn_index[keep_mask]

    def invalidate(self) -> None:
        """Force a full reassignment on the next call.

        Called after a simplification event.  The reference method refreshes
        assignments every `t` iterations, but a prune is not a drift -- the
        population has changed discontinuously, so waiting up to `t` steps
        would leave the model rendering from a partition fitted to primitives
        that no longer exist.
        """
        self.nn_index = None

    def storage_bits(self, num_primitives: int) -> dict[str, int]:
        """Stored size of this codebook, in bits.

        Index width is `ceil(log2(K))`.  The reference implementation derives it
        from the primitive *count* instead, which for a million primitives
        spends 20 bits where 12 suffice -- inflating the index payload by ~1.7x
        and understating the compression it reports.
        """
        import math

        bits_per_index = max(1, math.ceil(math.log2(max(2, self.num_clusters))))
        return {
            "index_bits": bits_per_index * num_primitives,
            "codebook_bits": self.num_clusters * self.vec_dim * 32,
            "bits_per_index": bits_per_index,
            "num_clusters": self.num_clusters,
            "vec_dim": self.vec_dim,
        }


class AttributeQuantizer:
    """The three codebooks, and the schedule that drives them."""

    GROUPS = ("dc", "scale", "rotation")

    def __init__(self, num_clusters: int, num_iters: int = 1) -> None:
        self.quantizers = {
            g: VectorQuantizer(g, num_clusters, num_iters) for g in self.GROUPS
        }

    def apply(self, gaussians, assign: bool) -> None:
        """Install straight-through quantized overrides on the model.

        The overrides are on the RAW parameters, so the model's own activation
        (exp for scale, normalise for rotation) applies afterwards -- which is
        what "quantize before activation" means in practice.
        """
        gaussians.set_quant_override(
            "features_dc",
            self.quantizers["dc"].quantize(gaussians._features_dc, assign),
        )
        gaussians.set_quant_override(
            "scaling",
            self.quantizers["scale"].quantize(gaussians._scaling, assign),
        )
        gaussians.set_quant_override(
            "rotation",
            self.quantizers["rotation"].quantize(gaussians._rotation, assign),
        )

    def prune(self, keep_mask: torch.Tensor) -> None:
        for q in self.quantizers.values():
            q.prune(keep_mask)

    def invalidate(self) -> None:
        for q in self.quantizers.values():
            q.invalidate()

    def storage_report(self, num_primitives: int) -> dict:
        """Bits for the quantized attributes plus the unquantized remainder.

        Reported in absolute terms alongside the per-primitive float count,
        because a compression ratio against a 59-float baseline is a different
        quantity from one against this baseline's 14.
        """
        total_index = total_codebook = 0
        per_group = {}
        for name, q in self.quantizers.items():
            rep = q.storage_bits(num_primitives)
            per_group[name] = rep
            total_index += rep["index_bits"]
            total_codebook += rep["codebook_bits"]

        # Never quantized: xyz (3 floats) and opacity (1 float).
        unquantized_bits = num_primitives * 4 * 32
        quantized_total = total_index + total_codebook + unquantized_bits
        baseline_bits = num_primitives * 14 * 32   # this baseline, sh_degree=0

        return {
            "per_group": per_group,
            "index_bits": total_index,
            "codebook_bits": total_codebook,
            "unquantized_bits": unquantized_bits,
            "total_bits": quantized_total,
            "baseline_bits_14f": baseline_bits,
            "ratio_vs_this_baseline": baseline_bits / max(1, quantized_total),
            "note": (
                "Ratio is against this baseline's 14 floats/primitive "
                "(sh_degree=0), NOT the 59 the compression literature assumes. "
                "The two are not comparable."
            ),
        }
