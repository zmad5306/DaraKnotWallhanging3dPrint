import sys
sys.path[:0]=['.work/python-libs']
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root='.work/veneer-face-r9/'
im=np.asarray(Image.open(r'C:\Users\Zach\AppData\Local\Temp\codex-clipboard-e5ded43a-5bf4-4f27-8e80-780aeb744116.png').convert('RGB')).astype(float)
val=im[:,:,:3].mean(2)
for x in (100,350,700,1100,1370):
 a=val[:,x];f=np.fft.rfftfreq(len(a));p=abs(np.fft.rfft(a-gaussian_filter1d(a,5)));ids=np.argsort(p)[-5:];print('spectrum',x,list(zip(f[ids],p[ids])),flush=True)
# Demodulate the repeated layer shading: unwrapped phase gives the local shape of a layer.
xs=np.arange(335,1380);profiles=[]
fig,axs=plt.subplots(2,1,figsize=(15,8))
for row in (70,140,190,230,300):
 ys=np.arange(row-15,row+16);freq=.36
 # Select dominant period from this horizontal image strip.
 freqs=np.linspace(.25,.45,400)
 spectra=np.exp(-2j*np.pi*freqs[:,None]*ys)@(val[ys][:,xs]-val[ys][:,xs].mean(0))
 power=np.abs(spectra).mean(1);freq=freqs[np.argmax(power)]
 phase=np.unwrap(np.angle(spectra[np.argmax(power)]));phase-=phase[0]
 phase=-phase/(2*np.pi*freq);phase=gaussian_filter1d(phase,3)
 profiles.append((row,phase));axs[0].plot(xs,phase,label=f'row{row} period{1/freq:.2f}')
axs[0].legend();axs[0].grid()
data=np.load(root+'V1-chains.npz');stats=data['stats'];results=[]
sample=np.linspace(0,1,len(xs));target=profiles[2][1];target=target-np.polyval(np.polyfit(sample,target,1),sample)
for z in np.unique(stats[:,0]):
 ids=np.where((abs(stats[:,0]-z)<.001)&(stats[:,2]>20))[0]
 if not len(ids):continue
 segs=np.concatenate([data[f'c{k}'] for k in ids]);a=segs[:,:3];b=segs[:,3:6]
 lo=min(a[:,1].min(),b[:,1].min());hi=max(a[:,1].max(),b[:,1].max())
 yp=lo+(hi-lo)*sample;xp=np.full(len(sample),-np.inf)
 for aa,bb in zip(a,b):
  if abs(bb[1]-aa[1])<1e-8:continue
  t=(yp-aa[1])/(bb[1]-aa[1]);mask=(t>=0)&(t<=1);xp[mask]=np.maximum(xp[mask],aa[0]+t[mask]*(bb[0]-aa[0]))
 if np.isfinite(xp).mean()<.98:continue
 xp=np.interp(sample,sample[np.isfinite(xp)],xp[np.isfinite(xp)])
 for rev in (False,True):
  curve=xp[::-1] if rev else xp;curve=curve-np.polyval(np.polyfit(sample,curve,1),sample)
  corr=np.corrcoef(curve,target)[0,1];results.append((abs(corr),z,rev,corr,lo,hi,curve))
results.sort(key=lambda r:-r[0]);print('best',[(r[:6]) for r in results[:20]],flush=True)
axs[1].plot(sample,target/np.std(target),label='screenshot')
for r in results[:3]:axs[1].plot(sample,r[-1]/np.std(r[-1])*np.sign(r[3]),label=f'Z{r[1]} corr{r[3]:.3f} rev{r[2]}')
axs[1].legend();axs[1].grid();fig.tight_layout();fig.savefig(root+'image-match.png',dpi=130)
np.savez_compressed(root+'image-profiles.npz',xs=xs,rows=np.array([r[0] for r in profiles]),profiles=np.array([r[1] for r in profiles]))
