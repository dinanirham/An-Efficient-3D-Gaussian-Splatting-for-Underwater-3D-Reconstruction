#!/usr/bin/env bash
# Environment setup for the combined method on Colab (A100 target).
#
#   !bash implementation/tools/setup_colab.sh
#
# Builds the two CUDA extensions and installs the runtime dependencies that
# Colab does not already ship.
#
# Two deliberate choices, both to avoid fighting Colab's preinstalled stack:
#
#  1. We do NOT install SeaSplat's pinned requirements.txt.  It is a full
#     environment freeze from a 2023-era CUDA 11.8 / torch 2.1 stack and would
#     downgrade Colab's torch, which in turn breaks the CUDA extensions we are
#     about to compile against it.  Only the genuinely missing packages are
#     installed.
#
#  2. The rasterizer is built from mini-splatting's `_ms` fork, NOT from
#     SeaSplat's `dxyang/diff-gaussian-rasterization` submodule (which is
#     empty in this checkout and is not needed -- see CD-13 and
#     gaussian_renderer/__init__.py for why the `_ms` fork alone suffices).
set -euo pipefail

# Say where it died. Under `set -e` an aborted script simply stops, and the
# failure then surfaces one cell later as a missing extension -- which is what
# happened when a diagnostic that fails by design took the build down with it
# through `pipefail`. A one-line trap turns silence into a location.
trap 'echo "
!!! setup_colab.sh aborted at line $LINENO (exit $?)
    The CUDA extensions may not have been built. Nothing below this point ran." >&2' ERR

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL_ROOT="$(dirname "$HERE")"
REPO_ROOT="$(dirname "$IMPL_ROOT")"

SUBMODULES="$REPO_ROOT/mini-splatting/submodules"
RASTERIZER="$SUBMODULES/diff-gaussian-rasterization_ms"
SIMPLE_KNN="$SUBMODULES/simple-knn"

# sm_80 = A100.  Override for another device, e.g.
#   TORCH_CUDA_ARCH_LIST="8.9" bash tools/setup_colab.sh
export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.0+PTX}"

echo "=============================================================="
echo " repo root        : $REPO_ROOT"
echo " implementation   : $IMPL_ROOT"
echo " arch list        : $TORCH_CUDA_ARCH_LIST"
echo "=============================================================="

echo
echo "--- GPU ---"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || {
    echo "FATAL: no NVIDIA GPU visible." >&2
    exit 1
}

GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
if [[ "$GPU_NAME" != *"A100"* ]]; then
    echo
    echo "WARNING: GPU is '$GPU_NAME', not an A100."
    echo "  Every cell of the matrix must land on the same device or the"
    echo "  between-cell contrasts are not comparable.  Training will refuse"
    echo "  to start unless --allow_any_gpu is passed."
fi

echo
echo "--- sanity: the reference submodules must be present ---"
for d in "$RASTERIZER" "$SIMPLE_KNN" "$RASTERIZER/third_party/glm"; do
    if [[ ! -d "$d" ]] || [[ -z "$(ls -A "$d" 2>/dev/null)" ]]; then
        echo "FATAL: missing or empty: $d" >&2
        echo "  These are tracked in the repository, so a plain clone should" >&2
        echo "  contain them.  A shallow or filtered clone will not." >&2
        exit 1
    fi
    echo "  ok: $d"
done

echo
echo "--- python deps Colab does not ship ---"
# Present on Colab already: torch, torchvision, numpy, pillow, matplotlib,
# tqdm, tensorboard (via torch), scipy.
#
# open3d is deliberately absent. It is in SeaSplat's requirements.txt, but no
# module we execute imports it, and it publishes no wheel for the Python Colab
# now runs -- so listing it aborted this whole script under `set -e`, before
# either CUDA extension was built.
pip install -q \
    jaxtyping \
    kornia \
    plyfile \
    splines \
    scikit-learn

# RoMa, the dense matcher behind M1 (source/roma_init.py). Only the M1 cells
# (A1, A4, A5, A7) need it, so a failure here is a warning rather than fatal:
# A0, A2, A3 and A6 can all still run.
#
# Its full declared dependency set, minus torch and torchvision, then the
# package itself with --no-deps. RoMa asks only for torch>=2.5.1, which Colab
# already satisfies -- but leaving pip free to resolve those two risks it
# reinstalling torch from PyPI, replacing the CUDA build both extensions were
# just compiled against with a generic wheel. Everything else is installed
# normally; stripping the deps wholesale is what left loguru missing.
echo "--- RoMa (M1 only) ---"
pip install -q \
    albumentations \
    einops \
    h5py \
    loguru \
    matplotlib \
    opencv-python \
    poselib \
    timm \
    tqdm \
    wandb
pip install -q --no-deps "git+https://github.com/Parskatt/RoMa.git" || true

# RoMa's optional fused correlation kernel (Linux only). Worth having -- the
# refiner blocks call it per scale, per image pair -- but strictly a speed
# optimisation: roma_init falls back to the pure-torch correlation it
# optimises, so a failure here costs wall clock, not correctness.
#
# Installing it is not the same as it working. The published wheel carries a
# compiled extension linked against a specific CUDA runtime, and the one on
# PyPI wants libcudart.so.13 while Colab ships 12.8 -- so it imports as a
# module, satisfies any "is it installed" check, and then dies inside the
# forward pass with a missing shared object. Verify by importing, and remove it
# if it cannot load: a broken extension left in place is worse than an absent
# one, because it makes the fallback look unnecessary.
if pip install -q fused-local-corr 2>/dev/null; then
    if python -c "import local_corr" 2>/dev/null; then
        echo "    fused-local-corr ok"
    else
        echo "    fused-local-corr installed but will not load:"
        # `|| true` is load-bearing. This command fails by design -- it exists
        # to print why the import failed -- and under `set -euo pipefail` the
        # pipeline inherits its non-zero status and aborts the script. Without
        # it the diagnostic kills the build it is diagnosing, and the failure
        # surfaces one cell later as a missing extension.
        python -c "import local_corr" 2>&1 | tail -2 | sed 's/^/        /' || true
        pip uninstall -q -y fused-local-corr || true
        echo "    removed it; roma_init uses the pure-torch correlation"
        echo "    (slower, same result)"
    fi
else
    echo "    note: fused-local-corr unavailable; roma_init will use the"
    echo "          pure-torch correlation (slower, same result)"
fi

if python -c "import romatch" 2>/dev/null; then
    echo "    romatch ok"
else
    echo "    WARNING: romatch unavailable -- the M1 cells (A1/A4/A5/A7) and"
    echo "             source/roma_init.py will not run. A0/A2/A3/A6 are fine."
    echo "    the import error was:"
    python -c "import romatch" 2>&1 | tail -4 | sed 's/^/        /' || true
fi

# Quiet on success, but show the compiler output on failure. With `pip -q` a
# failed build prints "See above for output" pointing at output that -q has
# already discarded, which leaves nothing to diagnose from.
build_ext() {
    local name="$1" path="$2" out
    echo "--- building $name ---"
    if ! out="$(pip install "$path" 2>&1)"; then
        echo "$out" | tail -50
        echo
        echo "!!! $name failed to build -- see the compiler output above."
        return 1
    fi
    echo "    ok"
}

echo
build_ext "diff_gaussian_rasterization_ms (Mini-Splatting fork)" "$RASTERIZER"
build_ext "simple_knn" "$SIMPLE_KNN"

echo
echo "--- import check ---"
python - <<'PY'
import torch
print(f"torch {torch.__version__}  cuda={torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"device: {torch.cuda.get_device_name()}  "
          f"sm_{''.join(map(str, torch.cuda.get_device_capability()))}")
import diff_gaussian_rasterization_ms as r
import simple_knn
print(f"rasterizer: {r.__file__}")
PY

echo
echo "=============================================================="
echo " setup complete.  Next, run the M1 acceptance test:"
echo
echo "   cd $IMPL_ROOT && python -m tools.verify_rasterizer"
echo
echo " Do not build anything on top of the merged binding until it"
echo " passes, in particular T3 (Z_raw/alpha recovers true depth)."
echo "=============================================================="
