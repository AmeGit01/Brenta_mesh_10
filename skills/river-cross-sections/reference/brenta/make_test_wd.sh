#!/bin/bash
# make_test_wd.sh <new folder> : builds a disposable Brenta working folder for regression tests of the toolkit.
#   <new folder>/rcs_config.json   copy of reference/brenta/rcs_config.json
#   <new folder>/layers/           COPIES of every *.gpkg of the Brenta project (with -wal/-shm, so unsaved QGIS edits are included);
#                                  the DTM is a symbolic link (read-only, 1.1 GB)
#   <new folder>/work/mat11_lines.json   locked wall lines (copy, if given as $2)
#   <new folder>/docs/             empty
# The real project layers are only read. Usage: bash make_test_wd.sh /path/to/scratch/wd_x [mat11_lines.json]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(cd "$HERE/../../../.." && pwd)"          # Brenta project root (skills/river-cross-sections/reference/brenta -> project)
WD="$1"; [ -n "$WD" ] || { echo "usage: $0 <new folder> [mat11_lines.json]"; exit 1; }
[ -e "$WD" ] && { echo "exists: $WD"; exit 1; }
mkdir -p "$WD/layers" "$WD/work" "$WD/docs"
cp "$HERE/rcs_config.json" "$WD/"
for f in "$PROJ"/layers/*.gpkg "$PROJ"/layers/*.gpkg-wal "$PROJ"/layers/*.gpkg-shm; do [ -e "$f" ] && cp "$f" "$WD/layers/"; done
ln -s "$PROJ/layers/DTM_finale.tif" "$WD/layers/DTM_finale.tif"
[ -n "$2" ] && cp "$2" "$WD/work/mat11_lines.json"
echo "test working folder ready: $WD"
