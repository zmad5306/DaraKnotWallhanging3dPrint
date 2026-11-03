from pathlib import Path
import ast, json, re

path = Path('working/Dara-Photo-Frame-A1-Jointed.scad')
s = path.read_text()
baseline = Path('.work/photo-retainers-before.scad')
assert not baseline.exists(), 'Do not overwrite the validation baseline'
baseline.write_text(s)

def replace(old, new):
    global s
    assert old in s, old[:100]
    s = s.replace(old, new)

replace('// Rear photo tracks and socket overhangs need support planning at slicing time.\n// Original backers, retainers, artwork, lap seams and overall front height are preserved.',
'''// Photo retainers are separate 20 x 10 x 3 mm rotating tabs, installed after printing.
// All frame sections print rear-down at Z=0, with no integral rear projections.
// Four tabs per photo; #6-19 x 1/2-inch pan-head screws, no washers/countersinks.
// Default photo pilots: diameter 3.175, depth 10.7; tab clearance holes: 4 mm.
// Screw penetration 9.7 mm, tip clearance 1 mm, front cover 2.8 mm.
// Loosen each screw slightly, rotate the tab 90 degrees, then snug after closing.
// Print the fit_sample before committing to the full frame; screw fit is provisional.
// Existing rabbets and lap sockets still need local support assessment at slicing.
// Original backers, artwork, lap seams and overall front height are preserved.''')
replace('thin backers and printed sliding retainers.', 'thin backers and separate screw-mounted rotating tabs.')
replace('retainer:Original keeper, fit_sample:Original keeper fit,', 'retainer:Flat rotating tab, fit_sample:Separate fit-test parts, retainer_detail:Photo screw detail,')
replace('// Clearance per side. A small tapered rib provides sliding friction.\nslide_clearance = 0.20;\nlock_rib = 0.25;',
'''// Independent of the M-mount dimensions. Finished mm, not master-scale values.
photo_retainer_thickness = 3; // [2.5:0.25:4]
photo_pilot_diameter = 3.175; // [2.9:0.025:3.4]
photo_clearance_diameter = 4; // [3.8:0.1:4.5]
show_photo_hardware = true; // Preview-only nominal screw envelopes; never exported.
retainer_cutaway = true; // Applies only to retainer_detail.''')
replace('uniform_scale = overall_width / master_width;', '''uniform_scale = overall_width / master_width;
photo_screw_length = 12.7; // Under-head length of the selected #6-19 x 1/2-inch screw.
photo_pivot_offset = 9.5;
photo_pilot_depth = photo_screw_length-photo_retainer_thickness+1;
photo_preview_ready = false; // Enable only after native geometry and cache verification.''')
replace('$vpt = view_mode=="mount_detail" ? [0,0,12] : [0,0,0];', '$vpt = view_mode=="mount_detail" ? [0,0,12] : view_mode=="retainer_detail" ? [5,0,4] : [0,0,0];')
replace('$vpr = view_mode=="mount_detail" || view_mode=="washer" ? [65,0,25] : [0,0,0];', '$vpr = view_mode=="retainer_detail" ? [110,0,25] : view_mode=="fit_sample" ? [45,0,20] : view_mode=="mount_detail" || view_mode=="washer" ? [65,0,25] : [0,0,0];')
replace('view_mode=="fit_sample" || view_mode=="retainer" ? 100', 'view_mode=="retainer_detail" ? 90 : view_mode=="fit_sample" ? 180 : view_mode=="retainer" ? 70')
replace('assert(rabbet_overlap <= 4.5, "Track roots start 5 mm outside the opening");\nassert(slide_clearance >= 0.1 && slide_clearance <= 0.35);\nassert(lock_rib >= 0 && lock_rib <= 0.4);',
'''assert(rabbet_overlap <= 4.5, "Keep the screw seat outside the photo pocket");
assert(photo_retainer_thickness >= 2.5 && photo_retainer_thickness <= 4);
assert(photo_pilot_diameter >= 2.9 && photo_pilot_diameter <= 3.4);
assert(photo_clearance_diameter >= 3.8 && photo_clearance_diameter <= 4.5);
assert(photo_pilot_depth > 0 && knot_depth*uniform_scale-photo_pilot_depth >= 2);
assert(photo_pivot_offset-photo_pilot_diameter/2-rabbet_overlap >= 3,
       "Photo pilot needs at least 3 mm of material to the rabbet");''')
start=s.index('module track_blank_mm() {')
end=s.index('// Evaluate the rear CSG',start)
s=s[:start]+'''module photo_pilot_mm() {
    // Blind cut opens at the original rear plane. No bosses or rear pads.
    translate([photo_pivot_offset,0,-.02])
        cylinder(d=photo_pilot_diameter,h=photo_pilot_depth+.02,$fn=64);
}
'''+s[end:]
replace('            for(i=[0:7],j=[0:3]) at_retainer(i,j) track_blank_mm();\n', '')
replace('track_channel_mm();', 'photo_pilot_mm();')
start=s.index('module slider_mm() {')
end=s.index('module working_model() {',start)
s=s[:start]+'''// One universal tab, with its flat screw-head face on Z=0 for printing.
module retainer_mm() {
    linear_extrude(height=photo_retainer_thickness,convexity=10)
        difference() {
            hull() for(x=[-.5,photo_pivot_offset]) translate([x,0]) circle(d=10,$fn=64);
            translate([photo_pivot_offset,0]) circle(d=photo_clearance_diameter,$fn=64);
        }
}
module installed_retainer_mm() {
    translate([photo_pivot_offset,0,0]) rotate([0,0,retainers_open ? 90 : 0])
        translate([-photo_pivot_offset,0,-photo_retainer_thickness]) retainer_mm();
}
module photo_screw_preview_mm() {
    // Nominal 7 x 2.5 mm head envelope only; this is not a printable screw.
    translate([photo_pivot_offset,0,-photo_retainer_thickness]) {
        cylinder(d=3.5,h=photo_screw_length,$fn=40);
        translate([0,0,-2.5]) cylinder(d=7,h=2.5,$fn=64);
    }
}
module photo_retainer_assembly_mm() {
    color(retainer_colour) installed_retainer_mm();
    if($preview && show_photo_hardware) %color([.55,.57,.6]) photo_screw_preview_mm();
}
module fit_frame_mm() {
    difference() {
        translate([0,-10,0]) cube([18,20,knot_depth*uniform_scale]);
        translate([-.02,-10.02,-.02])
            cube([rabbet_overlap+.02,20.04,backer_thickness+photo_allowance+.02]);
        photo_pilot_mm();
    }
}
module fit_backer_mm() {
    translate([-10,-9,0]) cube([10+rabbet_overlap-backer_clearance,18,backer_thickness]);
}
// Three separate print-ready parts, all at Z=0. No metal is included.
module fit_sample() {
    color(knot_colour) fit_frame_mm();
    if(show_backers) color(backer_colour) translate([-19,0,0]) fit_backer_mm();
    if(show_retainers) color(retainer_colour) translate([0,24,0]) retainer_mm();
}
module retainer_detail() {
    // Keep the negative-Y half when cut away, exposing the screw/pilot axis.
    // render() avoids coincident boolean preview artifacts in OpenSCAD 2021.
    color(knot_colour) render(convexity=20) difference() {
        fit_frame_mm();
        if(retainer_cutaway) translate([-20,0,-8]) cube([50,30,30]);
    }
    if(show_backers) color(backer_colour) render(convexity=10) difference() {
        fit_backer_mm();
        if(retainer_cutaway) translate([-20,0,-8]) cube([50,30,30]);
    }
    if(show_retainers) {
        color(retainer_colour) render(convexity=10) difference() {
            installed_retainer_mm();
            if(retainer_cutaway) translate([-20,0,-8]) cube([50,30,30]);
        }
        if($preview && show_photo_hardware) %color([.55,.57,.6]) photo_screw_preview_mm();
    }
}
'''+s[end:]
replace('else if(view_mode=="retainer") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) slider_mm();',
        'else if(view_mode=="retainer") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale])\n        translate([-4.5,0,0]) retainer_mm();')
replace('else if(view_mode=="fit_sample") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) fit_sample();',
'''else if(view_mode=="fit_sample") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) fit_sample();
    else if(view_mode=="retainer_detail") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) retainer_detail();''')
replace('if(show_retainers && view_mode!="frame") color(retainer_colour)', 'if(show_retainers && view_mode!="frame")')
replace('translate([retainers_open ? 12 : 0,0,view_mode=="exploded" ? -exploded_distance-8 : 0])\n                    slider_mm();',
        'translate([0,0,view_mode=="exploded" ? -exploded_distance-8 : 0])\n                    photo_retainer_assembly_mm();')
replace('                for(t=frame_tracks[i]) scale([uniform_scale,uniform_scale,uniform_scale])\n                    at_retainer(floor(t/4),t%4) track_blank_mm();\n', '')
replace('frame_tracks', 'frame_retainers')
replace('if(show_retainers) color(retainer_colour)\n                for(i=[0:7],j=[0:3]) at_retainer(i,j)\n                    translate([retainers_open ? 12 : 0,0,view_mode=="exploded" ? -exploded_distance-8 : 0]) slider_mm();',
'''if(show_retainers)
                for(i=[0:7],j=[0:3]) at_retainer(i,j)
                    translate([0,0,view_mode=="exploded" ? -exploded_distance-8 : 0]) photo_retainer_assembly_mm();''')
replace('    // Frame parts carrying original rear tracks keep the 3.2 mm Z allowance.',
        '    // Frame and M both rest on their original rear plane, with zero Z lift.')
replace('    rabbet_overlap==4 && (kind=="frame" ||', '''    rabbet_overlap==4 &&
    (kind=="M" || (photo_preview_ready && photo_pilot_diameter==3.175 &&
                   photo_pilot_depth==10.7 && photo_pivot_offset==9.5)) &&
    (kind=="frame" ||''')
placements=ast.literal_eval(re.search(r'^frame_placements = (.*?);',s,re.M).group(1))
for p in placements: p[3]=0
s,n=re.subn(r'^frame_placements = .*?;', 'frame_placements = '+json.dumps(placements,separators=(',',':'))+';',s,flags=re.M)
assert n==1
assert not re.search(r'slider_mm|track_blank_mm|track_channel_mm|slide_clearance|lock_rib|frame_tracks',s)
path.write_text(s)
print('Updated photo CAD; preview cache deliberately disabled until validation.')
