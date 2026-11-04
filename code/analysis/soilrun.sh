cd /home/claude
for a in NY=drumlins,32618,0.25 GB=gb,32616,0.5 AC=ac,32616,0.7 BR=br,32616,0.5 LG=lg,32616,0.5 PZ=pz,32615,0.5 TM=tm,32615,0.7 MEN=men,32616,0.7 LEE=lee,32616,0.7 PS=ps,32610,0.5 BRD=brd,32615,0.85 CHP=chp,32615,0.7 WSH=wsh,32618,0.7; do python3 field_ssurgo.py $a >> ssurgo_fields.log 2>&1; sleep 5; done
echo SOILDONE >> ssurgo_fields.log
