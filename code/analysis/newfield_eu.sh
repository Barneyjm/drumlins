#!/bin/sh
# usage: newfield_eu.sh name epsg "lonmin,latmin,lonmax,latmax" "srclon, srclat" N53_00_E015_00 ...
N=$1; E=$2; B=$3; S=$4; shift 4
D=/home/claude/$N; mkdir -p $D/data $D/check
for f in fetch_dem.py run_ny.py candidates.py detect.py spectral.py pointtest.py train.py check_sheets.py tile_morph.py flowfield.py conv_fixed.py law_test.py; do
  sed -e "s|/home/claude/ps|$D|g" -e "s|EPSG:32610|EPSG:$E|g" -e "s|transform(-122.7, 49.1)|transform($S)|" /home/claude/ps/$f > $D/$f; done
T=""; for t in "$@"; do T="$T    \"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_${t}_DEM/Copernicus_DSM_COG_10_${t}_DEM.tif\",\n"; done
python3 - "$D/fetch_dem.py" "$T" "$B" <<'PY'
import sys,re
f,t,b=sys.argv[1:]; s=open(f).read()
s=re.sub(r"TILES = \[.*?\]", "TILES = [\n"+t.replace('\\n','\n')+"]", s, flags=re.S)
s=re.sub(r"BBOX = \([^)]*\)", f"BBOX = ({b})", s)
open(f,'w').write(s)
PY
sed -i 's/for thr in (0.5, 0.9):/for thr in (0.5, 0.7, 0.9):/' $D/tile_morph.py
echo "$N ok"
