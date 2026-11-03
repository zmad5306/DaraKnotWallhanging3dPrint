from pathlib import Path
p=Path('.work/render_wall_blocks.py');s=p.read_text()
s=s.replace(" name,view,cam,extra=job\n", " name,view,cam,extra=job\n values=cam.split(','); extra=extra+['-D','$vpr=['+','.join(values[3:6])+']','-D','$vpt=['+','.join(values[:3])+']','-D','$vpd='+values[6]]\n if '--blocks-only' in __import__('sys').argv and name in ['assembly-rear','mount-exploded']:return\n")
p.write_text(s)
