#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export BLENDER_SYSTEM_SCRIPTS=/home/dev/.local/sysroot/usr/share/blender/scripts
export BLENDER_SYSTEM_DATAFILES=/home/dev/.local/sysroot/usr/share/blender/datafiles
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export OMP_NUM_THREADS=10
export OPENBLAS_NUM_THREADS=1
export LP_NUM_THREADS=10
exec xvfb-run -a -s '-screen 0 1280x1600x24' blender -b -t 10 --python src/build_portrait.py -- "$@"
