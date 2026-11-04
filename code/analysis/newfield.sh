#!/bin/sh
# usage: newfield.sh name epsg "lonmin,latmin,lonmax,latmax" "srclon, srclat" tile1 tile2 ...
N=$1; E=$2; B=$3; S=$4; shift 4
D=/home/claude/$N; mkdir -p $D/data $D/check
for f in fetch_dem.py run_ny.py candidates.py detect.py spectral.py pointtest.py train.py check_sheets.py tile_morph.py flowfield.py conv_fixed.py law_test.py ssurgo_tiles.py; do
  sed -e "s|/home/claude/ps|$D|g" -e "s|EPSG:32610|EPSG:$E|g" -e "s|transform(-122.7, 49.1)|transform($S)|" /home/claude/ps/$f > $D/$f; done
T=""; for t in "$@"; do T="$T    \"https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/$t/USGS_13_$t.tif\",\n"; done
python3 - "$D/fetch_dem.py" "$T" "$B" <<'PY'
import sys,re
f,t,b=sys.argv[1:]; s=open(f).read()
s=re.sub(r"TILES = \[.*?\]", "TILES = [\n"+t.replace('\\n','\n')+"]", s, flags=re.S)
s=re.sub(r"BBOX = \([^)]*\)", f"BBOX = ({b})", s)
open(f,'w').write(s)
PY
grep -n "BBOX =\|EPSG\|USGS_13" $D/fetch_dem.py | head; grep -n "transform(" $D/flowfield.py
