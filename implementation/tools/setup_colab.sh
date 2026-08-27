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
pip install -q \
    jaxtyping \
    kornia \
    plyfile \
    splines \
    scikit-learn \
    open3d

echo
echo "--- building diff_gaussian_rasterization_ms (Mini-Splatting fork) ---"
pip install -q "$RASTERIZER"

echo "--- building simple_knn ---"
pip install -q "$SIMPLE_KNN"

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
