cd /home/claude
for a in GB=gb,32616,0.5 MEN=men,32616,0.7 LG=lg,32616,0.5 AC=ac,32616,0.7 WSH=wsh,32618,0.5 PZ=pz,32615,0.5 TM=tm,32615,0.5 CHP=chp,32615,0.7 LEE=lee,32616,0.5 BR=br,32616,0.5; do NMAX=1500 python3 field_ssurgo_pts.py $a >> soilpts.log 2>&1; done
echo ALLDONE >> soilpts.log
