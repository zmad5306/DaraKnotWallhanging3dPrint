"""Diagnostic rendering of captured cover paths; NOT a print prediction.

Run from the repository root with moderngl 5.13.0 and glcontext 3.1.0 in
.work/render-libs, plus the existing geometry dependencies. No visible window.

The advanced mode reconstructs the diamond prisms, corner triangles and
independent normals described in BambuStudio's public AdvancedRenderer.cpp
and resources/shaders/140/gcode.vs. The mitered mode shares join vertices and
normals. Both render exactly the same captured G-code paths, width and height.
Lighting is simplified. This is NOT an image captured from Bambu Studio.

Reference: https://github.com/bambulab/BambuStudio/tree/master/src/slic3r/GUI/GCodeRenderer
"""
import sys,json,gzip,hashlib,zipfile
from pathlib import Path
sys.path[:0]=['.work/render-libs','.work/python-libs','scripts']
import numpy as np,moderngl
from PIL import Image
import prepare_hammered_bands as b
p=Path(__file__).resolve().parents[1]/'working/review/cover-edge'
ctx=moderngl.create_standalone_context()
print('Renderer',ctx.info['GL_RENDERER'])
capture=json.loads(gzip.decompress((p/'renderer-paths.json.gz').read_bytes()))
rows=capture['rows']
with zipfile.ZipFile(b.ROOT/capture['source']) as z:assert hashlib.sha256(z.read('Metadata/plate_1.gcode')).hexdigest()==capture['gcode_sha256']
undo=np.linalg.inv(capture['build_transform']);j=capture['joint'];loc=b.rotation(-j[3]);loc[:2,3]=-loc[:2,:2]@np.array(j[2]);T=loc@undo
# Same extrusion prisms and interpolated normals as Bambu AdvancedRenderer/gcode.vs.
tri=np.array([[0,2,1],[0,3,2],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7],[4,5,6],[4,6,7],[0,3,8],[8,3,2],[0,9,1],[1,9,2]])
vsh='''#version 330
in vec3 pos; in vec3 normal; uniform mat4 view; uniform mat4 proj; out vec3 norm; out vec3 fp;
void main(){vec4 p=view*vec4(pos,1);fp=p.xyz;norm=mat3(view)*normal;gl_Position=proj*p;}'''
fsh='''#version 330
in vec3 norm;in vec3 fp;out vec4 color;
void main(){vec3 n=normalize(norm);vec3 top=vec3(-.4574957,.4574957,.7624929);vec3 front=vec3(.6985074,.1397015,.6985074);float light=.3+max(dot(n,top),0)*.48+max(dot(n,front),0)*.18;float s=.075*pow(max(dot(-normalize(fp),reflect(-top,n)),0),20);color=vec4(vec3(.72,.40,.21)*light+vec3(s),1);}'''
prog=ctx.program(vertex_shader=vsh,fragment_shader=fsh)
view=np.array([[0,1,0,0],[-1,0,0,0],[0,0,1,-50],[0,0,0,1]],dtype=float)@T
view[0,3]-=1
proj=np.eye(4);proj[0,0]=1/23;proj[1,1]=1/8;proj[2,2]=-2/100;proj[2,3]=-1
prog['view'].write(view.T.astype('f4').tobytes());prog['proj'].write(proj.T.astype('f4').tobytes())
ctx.enable(moderngl.DEPTH_TEST|moderngl.CULL_FACE)
for mode in ['advanced','mitered']:
 allv=[];last=None
 for ri,r in enumerate(rows):
  s,e=np.array(r['world']);d=e-s;d/=np.linalg.norm(d);right=np.array([d[1],-d[0],0]);right/=np.linalg.norm(right);up=np.cross(right,d);w=r['w']/2;h=r['h']/2
  points=[];normals=[]
  for pt in [s,e]:
   center=pt-h*up
   for delta,n in [(h*up,up),(w*right,right),(-h*up,-up),(-w*right,-right)]:points.append(center+delta);normals.append(n)
  connected=last is not None and last['group']==r['group'] and np.linalg.norm(np.array(last['world'])[1]-s)<1e-5
  if connected:
   ps,pe=np.array(last['world']);pd=pe-ps;pd/=np.linalg.norm(pd);pr=np.array([pd[1],-pd[0],0]);pr/=np.linalg.norm(pr);pu=np.cross(pr,pd);pc=s-h*pu
   points.extend([pc-w*pr,pc+w*pr]);normals.extend([-pr,pr])
  else:points.extend([points[3],points[1]]);normals.extend([normals[3],normals[1]])
  if mode=='mitered':
   # Shared intersection of adjacent offset lines, smooth shared normals.
   for end_index,adj in [(0,last if connected else None),(1, rows[ri+1] if ri+1<len(rows) else None)]:
    if adj is None or adj['group']!=r['group']:continue
    a0,a1=np.array(adj['world']);ad=a1-a0;ad/=np.linalg.norm(ad);ar=np.array([ad[1],-ad[0],0]);ar/=np.linalg.norm(ar)
    avg=(ar+right);avg/=np.linalg.norm(avg);offset=w*avg/np.dot(avg,right)
    center=[s,e][end_index]-h*up;shift=4*end_index
    points[shift+1]=center+offset;points[shift+3]=center-offset
    normals[shift+1]=avg;normals[shift+3]=-avg
  idx=tri if mode=='advanced' else tri[2:10]
  a=np.concatenate([np.array(points),np.array(normals)],axis=1)
  allv.extend(a[idx.ravel()].tolist());last=r
 data=np.array(allv,dtype='f4');vbo=ctx.buffer(data.tobytes());vao=ctx.vertex_array(prog,[(vbo,'3f 3f','pos','normal')])
 fbo=ctx.simple_framebuffer((1840,640));fbo.use();fbo.clear(.17,.17,.18);vao.render();im=Image.frombytes('RGB',fbo.size,fbo.read(components=3)).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save(p/(mode+'.png'));vao.release();vbo.release();fbo.release()
print('Rendered')
