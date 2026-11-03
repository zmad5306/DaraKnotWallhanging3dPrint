from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh,manifold3d as md
D=json.loads(Path('.work/jointed-data.json').read_text())
P=json.loads(Path('.work/mount-plan.json').read_text())
A=json.loads(Path('.work/mount-affected.json').read_text())
report={'parts':[],'screw_checks':[],'locator_checks':[]}
def solid(mesh):
    s=md.Manifold(md.Mesh64(mesh.vertices,mesh.faces.astype(np.uint64)))
    assert s.status()==md.Error.NoError
    return s
def cylinder(xy,r,z,h,segments=96):
    return md.Manifold.cylinder(h,r,circular_segments=segments).translate([*xy,z])
def ring(xy,r0,r1,z,h):return cylinder(xy,r1,z,h)-cylinder(xy,r0,z-.01,h+.02)
def union(items):return md.Manifold.batch_boolean(items,md.OpType.Add) if items else md.Manifold()
old={};new={}
for family,d in D.items():
    old[family]=[];new[family]=[]
    for i,pl in enumerate(d['placements']):
        label=f'{family[0].upper()}{i+1}'
        a=trimesh.load_mesh(f'.work/jointed-{label}.stl')
        old_shift=3.2 if family=='frame' and a.extents[2]>15 else 0
        before=solid(a).translate([*pl['centre'],-old_shift]).rotate([0,0,-pl['angle']])
        old[family].append(before)
        b=trimesh.load_mesh(f'.work/mounted-{label}.stl') if i in A[family] else a
        assert b.is_watertight and b.is_winding_consistent and b.volume>0,(label,'mesh invalid')
        assert len(b.split())==1,(label,'disconnected')
        assert max(b.extents[:2])<246 and abs(b.bounds[0,2])<.0001,(label,'print bounds')
        shift=6.5 if family=='M' else old_shift
        after=solid(b).translate([*pl['centre'],-shift]).rotate([0,0,-pl['angle']])
        new[family].append(after)
        # All geometry changes must remain local to the mounts. No lap, face,
        # artwork, photo or rear-track edits are permitted outside these zones.
        idx=0 if family=='M' else 1
        areas=[cylinder(r['xy'],6.02 if family=='frame' else 5.02,-7,32) for r in P['screws'] if r['m' if family=='M' else 'frame']==i]
        areas += [cylinder(r['xy'],4.02,-7,32) for r in P['pins'] if r['m' if family=='M' else 'frame']==i]
        zone=union(areas)
        added_out=((after-before)-zone).volume()
        removed_out=((before-after)-zone).volume()
        entry={'part':label,'size_mm':b.extents.tolist(),'outside_mount_changes_mm3':[added_out,removed_out]}
        report['parts'].append(entry)
        print(label, 'valid, size',np.round(b.extents,3), 'non-mount change',round(added_out+removed_out,6),flush=True)
        assert added_out+removed_out<.03,(label,'unintended changes',added_out,removed_out)

for k,r in enumerate(P['screws']):
    xy=r['xy']; frame=new['frame'][r['frame']]; letter=new['M'][r['m']].translate([0,0,13.5])
    # Seat is a continuous annular 1.6 mm skin; broad rings sample away from
    # tessellation boundaries. Upper well and rear driver recess must be empty.
    tests={
      'seat_missing':(ring(xy,2.02,4.98,5.401,1.598)-frame).volume(),
      'rear_recess_obstructed':(cylinder(xy,5.98,.001,5.398)^frame).volume(),
      'clearance_obstructed':(cylinder(xy,1.99,5.399,1.602)^frame).volume(),
      'boss_well_obstructed':(cylinder(xy,5.13,7.001,6.5)^frame).volume(),
      'pilot_obstructed':(cylinder(xy,1.58,7.001,11.998)^letter).volume(),
      'boss_wall_missing':(ring(xy,1.60,4.97,7.001,6.498)-letter).volume(),
      'front_cap_missing':(cylinder(xy,1.58,19.001,4.998)-letter).volume(),
    }
    print('S'+str(k+1),{key:round(v,7) for key,v in tests.items()},flush=True)
    assert max(tests.values())<.001,('mount feature',k+1,tests)
    report['screw_checks'].append({'mount':k+1,'M':r['m']+1,'frame':r['frame']+1,**tests})

for k,r in enumerate(P['pins']):
    xy=r['xy'];frame=new['frame'][r['frame']];letter=new['M'][r['m']].translate([0,0,13.5])
    theta=math.radians(r['angle']);v=np.array([math.cos(theta),math.sin(theta)])
    c=np.array(xy);ends=[c-v*.399,c+v*.399] if r['slot'] else [c]
    bore=union([cylinder(t,2.09,13.501,3.298,64)for t in ends]).hull()
    tests={
      'pin_missing':(cylinder(xy,1.99,13.501,2.498)^frame).volume(),
      'hole_obstructed':(bore^letter).volume(),
      'closed_front_missing':(cylinder(xy,2.09,16.801,7.198)-letter).volume(),
      'support_pad_missing':(cylinder(xy,3.98,8.701,4.798)-frame).volume(),
    }
    pinvolume=cylinder(xy,1.99,13.501,2.498).volume()
    tests['pin_missing']=pinvolume-tests['pin_missing']
    print('D'+str(k+1),{key:round(v,7) for key,v in tests.items()},flush=True)
    assert max(tests.values())<.001,('locator',k+1,tests)
    report['locator_checks'].append({'dowel':k+1,**tests})

overlaps=[]
for family,parts in new.items():
    for i,s in enumerate(parts):
        for j,t in enumerate(parts[i+1:],i+1):
            volume=(s^t).volume()
            if volume>.0001:overlaps.append([family,i+1,j+1,volume])
            assert volume<.01,('same-family overlap',family,i+1,j+1,volume)
for i,m in enumerate(new['M']):
    assert sum(r['m']==i for r in P['screws'])>=1
    assert sum(r['m']==i for r in P['pins'])==2
    for j,f in enumerate(new['frame']):
        volume=(m.translate([0,0,13.5])^f).volume()
        if volume>.0001:overlaps.append(['M-frame',i+1,j+1,volume])
        assert volume<.01,('M-frame overlap',i+1,j+1,volume)
report['overlaps_mm3']=overlaps
report['thread_engagement_mm']=12.7-1-1.6
report['pilot_tip_clearance_mm']=12-(12.7-1-1.6)
report['dowel_tip_clearance_mm']=3.3-3
Path('.work/mounts-verification.json').write_text(json.dumps(report,indent=2))
print('PASS: all 36 sections valid and mutually clear; 10 reference screw stacks; 12 locating dowels.',flush=True)
