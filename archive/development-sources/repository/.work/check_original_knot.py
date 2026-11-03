exec(open('.work/check_core_footprint.py').read().split("core=unary_union")[0])
from shapely.ops import unary_union
base=unary_union([k,f])
print('Frame footprint valid:',base.is_valid,'connected:',base.geom_type)
print('Fabric backing intrusion into photos:',sum(f.intersection(polys('photo_loop_'+str(i))).area for i in range(1,9)))
r=Path('reference/Dara-Clean-Reference.scad').read_text()
for name in ['knot_outline','fabric_outline','letter_outline']:
    a=s.split('module '+name+'() {',1)[1].split('\nmodule ',1)[0].strip()
    b=r.split('module '+name+'() {',1)[1].split('\nmodule ',1)[0].strip()
    assert a==b,name
    print(name,'unchanged')
assert 'letter_outline' not in s.split('module print_core() {',1)[1].split('\nmodule ',1)[0]
print('No M-shaped frame platform')
