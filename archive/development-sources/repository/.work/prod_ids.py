exec(open('.work/check_production_cover.py').read().split("for label,files")[0])
cfg=ET.fromstring(prod['Metadata/model_settings.config'])
co=next(o for o in cfg.findall('object') if b.props(o)['name'].split(' - ')[0]=='Band1')
print('Band1 overrides',b.props(co))
plate=cfg.findall('plate')[30]
print('plate31',[(b.props(i)) for i in plate.findall('model_instance')])
info=ET.fromstring(prod['Metadata/slice_info.config'])
sp=next(p for p in info.findall('plate') if b.props(p)['index']=='31')
print('sliceobjects',[o.attrib for o in sp.findall('object')])
