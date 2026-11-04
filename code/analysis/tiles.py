import sys, math
lo0,la0,lo1,la1=map(float,sys.argv[1].split(','))
ts=[]
for la in range(math.floor(la0)+1, math.ceil(la1)+1):
    for lo in range(math.floor(lo0), math.ceil(lo1)):
        ts.append(f"n{la:02d}w{-lo:03d}")
print(' '.join(ts))
