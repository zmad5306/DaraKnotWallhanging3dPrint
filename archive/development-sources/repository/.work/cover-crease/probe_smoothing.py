import sys
from pathlib import Path
sys.path.insert(0, 'scripts')
import prepare_hammered_bands as b
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RectBivariateSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np=b.np
_,outline,joints,_=b.layout()

def smooth_crown(region, sigma=1.5, res=.125):
    pad=5*sigma+res*4
    lo=np.floor((np.array(region.bounds[:2])-pad)/res)*res
    hi=np.ceil((np.array(region.bounds[2:])+pad)/res)*res
    xs,ys=[np.arange(a,z+res/2,res) for a,z in zip(lo,hi)]
    x,y=np.meshgrid(xs,ys,indexing='ij')
    xy=np.column_stack([x.ravel(),y.ravel()])
    d=b.shapely.distance(b.shapely.points(xy),outline.boundary)
    d=np.where(b.shapely.contains(outline,b.shapely.points(xy)),d,-d)
    t=np.minimum(d/17.5,1.)
    z=(2.2*(2*t-t*t)).reshape(x.shape)
    z=gaussian_filter(z,sigma/res,mode='nearest',truncate=5.)
    spl=RectBivariateSpline(xs,ys,z,kx=3,ky=3,s=0)
    return lambda xy:spl.ev(xy[:,0],xy[:,1])

if __name__=='__main__':
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for i,j in enumerate(joints,1):
        reg=b.locate(b.rect(-6,-j[4],6,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
        fn=smooth_crown(reg)
        T=b.rotation(j[3]);T[:2,3]=j[2]
        xs,ys=np.meshgrid(np.arange(-6,6,.15),np.arange(-j[4],j[4],.15))
        p=np.column_stack([xs.ravel(),ys.ravel(),np.zeros(xs.size)])
        xy=b.trimesh.transform_points(p,T)[:,:2]
        xy=xy[b.shapely.contains(reg,b.shapely.points(xy))]
        d=fn(xy)-b.crown(outline,xy)
        print('B',i,'delta',d.min(),d.max(),flush=True)
        if i!=1:continue
        for col,x in enumerate([0,5]):
            y=np.linspace(-5,1,12001)
            xy=b.trimesh.transform_points(np.column_stack([y*0+x,y,y*0]),T)[:,:2]
            for f,label in [(lambda xy:b.crown(outline,xy),'Existing crown'),(fn,'Smoothed crown')]:
                h=f(xy);s=np.gradient(h,y)
                axes[0,col].plot(y,h,label=label)
                axes[1,col].plot(y,np.degrees(np.arctan(s)),label=label)
            axes[0,col].set_title(f'B1, cross-section at x={x} mm')
            axes[0,col].set_ylabel('Crown rise (mm)')
            axes[1,col].set_ylabel('Surface slope (degrees)')
            axes[1,col].set_xlabel('Along cover (mm)')
            for row in range(2):axes[row,col].legend();axes[row,col].grid(alpha=.3)
    fig.suptitle('Actual crown formula: slope transition before and after smoothing')
    fig.tight_layout();fig.savefig('.work/cover-crease/crown-profile.png',dpi=150)
