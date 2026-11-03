// DARA PHOTO FRAME - A1 STAGGERED KEYED LAP SECTIONS
// New manufacturing copy of Dara-Photo-Frame.scad; source/reference untouched.
// CAD ONLY. No slicing, supports, toolpaths, print project, or production meshes.
// 20 frame sections F1-F20; 6 letter sections M1-M6. Finished size 914.4 mm.
// Repartitioned from continuous outlines: 31 frame laps + 5 M laps (previously 42 + 5).
// Irregular angled seams, with no grid or four-way seam intersections.
// All sections fit a 253 mm square including tongues at the saved flat rotations.
// A1 printable area: 256 x 256 mm; at least 1.5 mm per edge, before any brim.
// Separate bed outlines are review aids; layout does not represent one loaded plate.
// Exact shoulder profiles and key/pocket contours extracted from the frozen
// Tested-Lap-Joints.scad straight sample, in final mm (NO further 75% scaling).
// Same geometry follows curved rails by clipping to the original body outline.
// Lap 18 mm; tongue 4.8 mm; shoulder radius .75 mm; hidden gap .15 mm;
// visible gap .075 mm. Keys 13.5 x 3 x 1.2 mm, radius .6 mm;
// pockets have .15 mm XY clearance and .3 mm clearance above the keys.
// Two keys per seam, spaced across each local rail. Lap geometry is unchanged.
// M mounting: 10 rear screws and reference washers; 12 locating dowels on the knot.
// M1/M3/M4/M6 have two screws each; M2/M5 have one. Every M has two locators.
// All screws and dowels are on full-height knot rails, clear of the lowered weave.
// M's rear stays at local Z=0: blind holes only, no projecting bosses or pads.
// The reference boss is a surrogate for material INSIDE M, not an external boss.
// Reference hardware: #6-19 x 1/2-inch pan-head plastic thread-forming screws,
// 12 mm rear counterbores, 4 mm clearance holes, 3.175 mm pilots and 1 mm washers.
// Adapt the reference's axial stack to the 10.5 mm M: 4 mm knot seat, 8.7 mm
// blind pilot. Engagement = 12.7-1-4 = 7.7 mm; tip clearance 1 mm; front cover 1.8 mm.
// The sample's 1.6 mm seat/12 mm pilot would not fit inside this flat-backed M.
// M bears directly on the original knot top at Z=13.5; front remains at Z=24.
// Knot counterbores end at Z=9.5; washers bear at Z=8.5..9.5.
// Each M section has a round locator hole and a secondary 0.8 mm axial relief slot.
// Integral knot pins are 4 mm diameter with 3 mm insertion and chamfered tips.
// M holes are 4.2 mm wide and 3.3 mm deep; neither the pins nor their roots
// touch the recessed weave. No support pedestals are added to the frame.
// Assemble and bond the lap sections first, lower M onto the pins, then install
// washers and screws from the rear. Screwdriver access clears photo hardware.
// The reference confirms lap rigidity, not the revised screw stack or dowel fit.
// This remains CAD only; no slicer settings or print projects are changed.
// M retains its 10.5 mm body, with the same unscaled joint geometry.
// Full 36-inch model is fixed here: changing scale invalidates bed and fit checks.
// Section mode centres one part at Z=0; M sections print with their flat rear down.
// Layout is a review of separate 256 mm bed outlines, not a multi-part plate.
// See the assembly_order arrays below: lower each socket over earlier tongues.
// This keyed lap needs a suitable bonded assembly; it is not a locking fastener.
// Photo retainers are separate 20 x 10 x 3 mm rotating tabs, installed after printing.
// All frame sections print rear-down at Z=0, with no integral rear projections.
// Four tabs per photo; #6-19 x 1/2-inch pan-head screws, no washers/countersinks.
// Default photo pilots: diameter 3.175, depth 10.7; tab clearance holes: 4 mm.
// Screw penetration 9.7 mm, tip clearance 1 mm, front cover 2.8 mm.
// Loosen each screw slightly, rotate the tab 90 degrees, then snug after closing.
// Print the fit_sample before committing to the full frame; screw fit is provisional.
// Existing rabbets and lap sockets still need local support assessment at slicing.
// Original backers, artwork, tested lap profile and overall front height are preserved.
// Source SHA256: dcd467893411bca2ddaefc2110132db8b98dfd855f9dfdf1902084aa4d63706b

/* [M attachment] */
show_mount_hardware = true; // Preview only: metal screws and separate reference washers.
mount_index = 1; // [1:10]
mount_cutaway = true;
mount_explode = 0; // [0:1:25]
// Diameter clearance, not clearance per side. Default is 0.10 mm per side.
dowel_clearance = 0.20; // [0.10:0.05:0.40]
// Extra total length of the secondary hole, along the line between both pins.
dowel_slot_relief = 0.80; // [0.40:0.10:1.20]

/* [Sections] */
part_family = "frame"; // [frame:Frame F1-F20, M:Letter M1-M6]
section_index = 1; // [1:20]
colour_sections = true;
fast_preview = true; // Exact embedded default-shape preview; F6 always evaluates the CAD.
show_plate_outline = false; // Preview the A1 bed around a single section.
show_section_ids = false; // Preview annotations only; never part of an export.
joint_index = 1; // [1:31]
joint_separation = 12;

// DARA WALL HANGING - WORKING PHOTO FRAME
// Units: millimetres. Artwork faces +Z; +Y is up in the front view.
// Separate working copy: rear rabbets, thin backers and separate screw-mounted rotating tabs.
// Closed frame core beneath the weave only; rear face remains at Z=0.
// M is a separate sectioned assembly: view_mode="M" puts its bottom at Z=0.
// Model the core as a solid volume; the slicer supplies infill and solid skins.
// Clean reference is read-only. Front artwork is copied without outline changes.
// This file is self-contained: no STL imports, includes, or installed fonts.
// The 48-inch master is uniformly scaled to 36 inches (75%) in X, Y and Z.

/* [Display] */
view_mode = "assembly"; // [assembly:Sectioned assembly, frame:Sectioned frame, M:Sectioned M, exploded:Separate sections, section:One section at print origin, layout:Separate bed reviews, joint_detail:Selected lap pair, backer:Original photo backer, retainer:Flat rotating tab, fit_sample:Separate fit-test parts, retainer_detail:Photo screw detail, drawing:Original front drawing, mount_detail:Screw mount detail, mount_map:Mount locations, washer:Reference washer]
show_backers = true;
show_retainers = true;
retainers_open = false;
backer_index = 1; // [1:8]

/* [Photo retention - finished mm] */
backer_thickness = 1.6;
photo_allowance = 0.4;
rabbet_overlap = 4;
backer_clearance = 0.3;
// Independent of the M-mount dimensions. Finished mm, not master-scale values.
photo_retainer_thickness = 3; // [2.5:0.25:4]
photo_pilot_diameter = 3.175; // [2.9:0.025:3.4]
photo_clearance_diameter = 4; // [3.8:0.1:4.5]
show_photo_hardware = true; // Preview-only nominal screw envelopes; never exported.
retainer_cutaway = true; // Applies only to retainer_detail.
exploded_distance = 30;
backer_colour = [0.48, 0.59, 0.65];
retainer_colour = [0.9, 0.56, 0.22];
show_knot = true;
show_letter = true;
show_fabric = true;
fabric_style = "woven"; // [woven:Raised weave on solid backing, plain:Simple fabric surface]

/* [Overall size - mm] */
overall_width = 914.4;

/* [Master proportions - before uniform scaling] */
// These master dimensions are all multiplied by overall_width / 1219.2.
// At 36 inches: knot depth 13.5 mm; M front Z=24 mm; fabric depth 0.6 mm.
knot_depth = 18;
letter_back_z = 18;
letter_depth = 14;
fabric_back_z = 12;
fabric_depth = 0.8;
fabric_pitch = 8;
fabric_thread_width = 2;

/* [Reference colours] */
knot_colour = [0.76, 0.79, 0.75];
fabric_colour = [0.57, 0.49, 0.36];
letter_colour = [0.96, 0.91, 0.79];

/* [Hidden] */
master_width = 1219.2;
uniform_scale = overall_width / master_width;
photo_screw_length = 12.7; // Under-head length of the selected #6-19 x 1/2-inch screw.
photo_pivot_offset = 9.5;
photo_pilot_depth = photo_screw_length-photo_retainer_thickness+1;
photo_preview_ready = false; // Regenerated from verified native flat-back sections.
// Front orthographic view on opening. Rotate normally to inspect the depth.
$vpt = view_mode=="mount_detail" ? [0,0,12] : view_mode=="retainer_detail" ? [5,0,4] : view_mode=="layout" ? [560,-floor((part_count(part_family)-1)/5)*140,0] : [0,0,0];
$vpr = view_mode=="retainer_detail" ? [110,0,205] : view_mode=="fit_sample" ? [45,0,20] : view_mode=="mount_detail" || view_mode=="washer" ? [65,0,25] : [0,0,0];
$vpd = view_mode=="section" ? 600 : view_mode=="joint_detail" || view_mode=="mount_detail" ? 220 : view_mode=="washer" ? 40 : view_mode=="retainer_detail" ? 90 : view_mode=="fit_sample" ? 180 : view_mode=="retainer" ? 70 : overall_width*2.75;
$fn = 32;

assert(overall_width > 0 && knot_depth > 0 && letter_depth > 0);
assert(fabric_pitch > fabric_thread_width && fabric_thread_width > 0);
assert(fabric_back_z >= 0 && fabric_depth > 0);
assert(fabric_back_z + fabric_depth <= knot_depth);
assert(letter_back_z >= knot_depth);

// Outline modules below hold the artwork; these modules describe its depth.
// The knot rails have a plain, continuous section. The M is a single outline.
module knot_reference() {
    linear_extrude(height = knot_depth, convexity = 30)
        knot_outline();
}

module letter_reference() {
    translate([0, 0, letter_back_z])
        linear_extrude(height = letter_depth, convexity = 10)
            letter_outline();
}

// Raised decorative threads above the continuous print core.
// The tiny edge overlap joins the thread tips to the surrounding rails.
module fabric_pattern() {
    intersection() {
        offset(delta = 0.15) fabric_outline();
        if (fabric_style == "plain") {
            square([master_width + 4, master_width + 4], center = true);
        } else {
            union() {
                for (i = [-ceil(master_width / (2 * fabric_pitch)):
                           ceil(master_width / (2 * fabric_pitch))]) {
                    translate([i * fabric_pitch, 0])
                        square([fabric_thread_width, master_width + 4], center = true);
                    translate([0, i * fabric_pitch])
                        square([master_width + 4, fabric_thread_width], center = true);
                }
            }
        }
    }
}

module fabric_reference() {
    translate([0, 0, fabric_back_z])
        linear_extrude(height = fabric_depth, convexity = 30)
            fabric_pattern();
}

// Fill to the existing fabric height, rather than enclosing an empty cavity
// between two sheets. This lets slicer infill support the top skin and weave.
// Follow only the fabric footprint: no M-shaped platform beneath the letter.
// The knot retains its original shape, including where it passes under the M.
module print_core() {
    if (show_fabric && fabric_back_z > 0)
        linear_extrude(height = fabric_back_z, convexity = 30)
            offset(delta = 0.15) fabric_outline();
}

module reference_model() {
    // Fuse the frame backing and weave, with no interior partitions.
    // Keep the M outside this union; its own bottom is at letter_back_z.
    union() {
        if (show_knot) color(knot_colour) photo_frame();
        else color(knot_colour) print_core();
        if (show_fabric) color(fabric_colour) fabric_reference();
    }
    if (show_letter && view_mode != "frame") color(letter_colour)
        translate([0, 0, view_mode == "exploded" ? u(exploded_distance) : 0])
            letter_reference();
}

// Occlude the fabric and knot below the M in the flat drawing as in the model.
// Export this view to SVG or DXF when a 1:1 design drawing is needed.
module reference_drawing() {
    if (show_knot) color(knot_colour) difference() {
        knot_outline();
        if (show_letter) letter_outline();
    }
    if (show_fabric) color(fabric_colour) difference() {
        offset(delta = 0.15) fabric_outline();
        if (show_knot) knot_outline();
        if (show_letter) letter_outline();
    }
    if (show_letter) color(letter_colour) letter_outline();
}



// Rear photo hardware. All dimensions here are finished millimetres.
function u(mm) = mm / uniform_scale;
assert(backer_index >= 1 && backer_index <= 8 && floor(backer_index)==backer_index);
assert(backer_thickness > 0 && photo_allowance > 0);
assert(backer_clearance > 0 && backer_clearance < rabbet_overlap);
assert(rabbet_overlap <= 4.5, "Keep the screw seat outside the photo pocket");
assert(photo_retainer_thickness >= 2.5 && photo_retainer_thickness <= 4);
assert(photo_pilot_diameter >= 2.9 && photo_pilot_diameter <= 3.4);
assert(photo_clearance_diameter >= 3.8 && photo_clearance_diameter <= 4.5);
assert(photo_pilot_depth > 0 && knot_depth*uniform_scale-photo_pilot_depth >= 2);
assert(photo_pivot_offset-photo_pilot_diameter/2-rabbet_overlap >= 3,
       "Photo pilot needs at least 3 mm of material to the rabbet");
assert(backer_thickness + photo_allowance < knot_depth*uniform_scale - 2);

module photo_opening(i) {
    if (i==0) photo_loop_1();
    if (i==1) photo_loop_2();
    if (i==2) photo_loop_3();
    if (i==3) photo_loop_4();
    if (i==4) photo_loop_5();
    if (i==5) photo_loop_6();
    if (i==6) photo_loop_7();
    if (i==7) photo_loop_8();
}
// Local hardware X points outward from the photo; Y follows the boundary.
// Hardware itself is authored in real mm and converted back to master units.
module at_retainer(i,j) {
    translate(concat(photo_anchors[i][j],[0]))
        rotate([0,0,atan2(photo_normals[i][j][1],photo_normals[i][j][0])])
            scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) children();
}
module photo_pilot_mm() {
    // Blind cut opens at the original rear plane. No bosses or rear pads.
    translate([photo_pivot_offset,0,-.02])
        cylinder(d=photo_pilot_diameter,h=photo_pilot_depth+.02,$fn=64);
}
// Evaluate the rear CSG once so OpenSCAD F5 shows all rails reliably.
module photo_frame() {
    render(convexity=40) difference() {
        union() {
            knot_reference();
            print_core();
        }
        for(i=[0:7]) {
            // Pocket opens from rear Z=0. Remaining rail forms the photo lip.
            translate([0,0,-u(0.02)])
                linear_extrude(height=u(backer_thickness+photo_allowance+0.02))
                    offset(delta=u(rabbet_overlap)) photo_opening(i);
            for(j=[0:3]) at_retainer(i,j) photo_pilot_mm();
        }
    }
}
module photo_backer(i) {
    linear_extrude(height=u(backer_thickness))
        offset(delta=u(rabbet_overlap-backer_clearance)) photo_opening(i);
}
// One universal tab, with its flat screw-head face on Z=0 for printing.
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
module working_model() {
    if(view_mode=="drawing") reference_drawing();
    else if(view_mode=="M")
        // One closed, flat-bottomed solid; the slicer supplies its infill.
        translate([0,0,-letter_back_z]) letter_reference();
    else if(view_mode=="backer")
        translate(-concat(photo_centres[backer_index-1],[0])) photo_backer(backer_index-1);
    else if(view_mode=="retainer") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale])
        translate([-4.5,0,0]) retainer_mm();
    else if(view_mode=="fit_sample") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) fit_sample();
    else if(view_mode=="retainer_detail") scale([1/uniform_scale,1/uniform_scale,1/uniform_scale]) retainer_detail();
    else {
        reference_model();
        if(show_backers && view_mode!="frame") color(backer_colour)
            translate([0,0,view_mode=="exploded" ? -u(exploded_distance) : 0])
                for(i=[0:7]) photo_backer(i);
        if(show_retainers && view_mode!="frame")
            for(i=[0:7],j=[0:3]) at_retainer(i,j)
                translate([0,0,view_mode=="exploded" ? -exploded_distance-8 : 0])
                    photo_retainer_assembly_mm();
    }
}

photo_anchors = [[[-508.6727731678386, 174.58821188649384], [-408.55798411626273, 265.5530074163491], [-361.4951130197122, 177.4069544306994], [-439.7518829335932, 114.06354245688844]], [[-114.11018033278197, 466.0549877646803], [-151.21858043396162, 361.3888729303523], [-270.61089843983495, 382.42837561173457], [-198.35523888920898, 496.96069697358826]], [[213.90197787944842, 361.33755332913637], [114.14536345093697, 402.86782173114005], [140.69583020143614, 517.5877482063768], [252.13419881675154, 441.3716825100894]], [[427.2950544372671, 258.92664868320145], [514.5758751150873, 155.99965838134406], [420.58292057201805, 113.98435467627775], [361.503397790245, 197.70142445442994]], [[361.4060634645851, -195.26934232679343], [421.7669410226277, -114.12529001127064], [513.8925079018736, -157.97461027453028], [425.1570662440525, -259.87134691555264]], [[181.9328146220998, -361.31645829769707], [264.47949368494227, -412.42426243243307], [170.69817449045175, -510.11225094510013], [114.13682646409413, -435.4091787777073]], [[-213.64256084925617, -361.33778416776863], [-114.15397457737086, -403.6283979095759], [-139.9332326692331, -517.6674495948424], [-251.9994279265822, -441.53908788033056]], [[-466.337218656933, -114.02891203739962], [-361.38056622526875, -151.92842303314632], [-383.19479573486996, -270.3262730118398], [-497.09162928458284, -198.051631399313]]];
photo_normals = [[[-0.9342003589138299, 0.3567487763192348], [-0.2730270130304725, 0.9620063670037003], [0.9999998142856961, -0.0006094494017187715], [-3.809901158706309e-05, -0.9999999992742327]], [[0.9999997539248198, -0.0007015342470969591], [0.0008184153769005592, -0.9999996650980794], [-0.9942667697264718, 0.10692796929563053], [-0.5079755640177946, 0.8613714798858872]], [[-0.000818420692356471, -0.9999996650937291], [-0.9999997941105817, -0.000641699925292327], [0.16074279168333055, 0.98699632974082], [0.8790873550701607, 0.47666069919361853]], [[0.4080325432096921, 0.9129673836900367], [0.9709071426070618, 0.2394563017224445], [0.0007424343868480728, -0.9999997243955526], [-0.9999994710355091, 0.0010285566109334457]], [[-0.9999989849080914, -0.001424844829082511], [-0.001470820204884646, 0.9999989183433775], [0.9707998131563383, -0.2398910643930252], [0.3926476297406988, -0.9196889902891147]], [[0.0003704521858292773, 0.9999999313825867], [0.9530527688174993, -0.3028042599589676], [0.3319017614333979, -0.9433139566217643], [-0.9999996462762263, 0.0008410989373131886]], [[0.000818415377973525, 0.9999996650980785], [0.9999997539211466, 0.0007015394830091864], [-0.15613270644747268, -0.9877360872102362], [-0.8720085375704862, -0.4894906642666251]], [[-0.0005343544679549074, 0.9999998572326412], [0.9999998524651402, -0.0005432031827138062], [-0.10301235666085963, -0.994680076394001], [-0.8569294266948138, -0.515433756815071]]];
photo_centres = [[-429.0922121190071, 181.52032594519565], [-181.65203444371883, 428.99150266327075], [181.6861449386055, 428.996048867354], [429.0782183813088, 181.53694151217613], [428.96878069115945, -181.59377208269007], [181.63405913664218, -428.96710728084116], [-181.6509789089073, -428.9866733915242], [-429.06225529502893, -181.4975655908118]];

// COPIED ARTWORK: edit this working file only.
module knot_outline() {
    polygon(points = [
        [-366.5960, 23.5600], [-365.3120, 23.3290], [-364.0580, 23.0350], [-361.3150, 22.2000], [-361.3150, -22.2000],
        [-363.3160, -22.7370], [-364.4720, -22.9960], [-365.6390, -23.2040], [-367.1190, -23.3920], [-368.9360, -23.5430],
        [-371.4630, -23.6830], [-376.8670, -23.8270], [-540.0130, -24.0150], [-544.8870, -24.0640], [-546.5990, -24.1260],
        [-548.2790, -24.2380], [-550.5680, -24.4910], [-553.1090, -24.8970], [-557.1610, -25.6610], [-559.5990, -26.2170],
        [-561.6780, -26.8170], [-564.0220, -27.6170], [-566.9370, -28.7120], [-569.5040, -29.7740], [-571.7250, -30.8100],
        [-573.9150, -31.9570], [-576.3710, -33.3800], [-579.1030, -35.0970], [-581.2750, -36.5650], [-583.1360, -37.9260],
        [-585.2010, -39.5700], [-587.2170, -41.3060], [-589.4350, -43.3760], [-591.5400, -45.5560], [-593.6760, -48.0470],
        [-595.8130, -50.7880], [-597.6210, -53.3380], [-599.3280, -56.0180], [-601.0720, -59.0430], [-602.6300, -62.0680],
        [-604.0430, -65.1110], [-605.0850, -67.6480], [-606.2090, -70.8030], [-607.1040, -73.7150], [-607.6930, -76.1190],
        [-608.3420, -79.5380], [-609.0080, -83.6600], [-609.3410, -86.6000], [-609.5090, -89.6460], [-609.5650, -93.4650],
        [-609.5780, -122.5420], [-609.5300, -127.7660], [-609.4350, -130.1570], [-609.2930, -132.1690], [-608.3070, -141.3840],
        [-607.7210, -149.4360], [-607.4170, -152.0450], [-607.0350, -154.6040], [-605.9760, -160.5830], [-605.1280, -165.6450],
        [-604.5890, -168.4520], [-601.9170, -180.0130], [-600.1620, -186.5530], [-599.2250, -189.7740], [-596.8550, -196.9600],
        [-594.5720, -203.5110], [-593.3990, -206.6440], [-591.6350, -211.0330], [-589.8670, -215.2180], [-587.0470, -221.5670],
        [-585.4970, -224.8700], [-580.8380, -234.1430], [-579.0310, -237.9970], [-577.2980, -240.6030], [-574.2040, -245.7400],
        [-572.3220, -248.7100], [-569.3710, -253.1960], [-565.7250, -258.5440], [-564.0230, -260.9490], [-562.0770, -263.5650],
        [-557.4720, -269.4900], [-555.4270, -272.0570], [-553.3010, -274.6000], [-547.5900, -281.2580], [-545.0420, -284.1550],
        [-543.0730, -286.2780], [-535.0500, -294.3060], [-533.5750, -295.7240], [-532.0710, -297.1010], [-525.7620, -302.7020],
        [-523.5270, -304.6270], [-517.8340, -309.3610], [-516.1190, -310.7080], [-514.3260, -312.0450], [-508.7090, -315.9970],
        [-502.3580, -320.5850], [-499.9120, -322.2370], [-496.6220, -324.3550], [-492.5010, -326.9300], [-489.4720, -328.7200],
        [-484.5520, -331.4380], [-479.4040, -334.1940], [-474.2560, -336.8290], [-469.0630, -339.3800], [-465.7140, -340.9050],
        [-460.1070, -343.3120], [-456.2500, -344.8970], [-451.2520, -346.8240], [-448.7150, -347.7260], [-442.1620, -349.9420],
        [-438.9810, -350.9420], [-433.4220, -352.5920], [-425.4070, -354.7640], [-422.3940, -355.4980], [-413.8020, -357.3500],
        [-411.3240, -357.8370], [-408.4840, -358.3040], [-402.0800, -359.2220], [-397.3190, -359.9870], [-395.3820, -360.2440],
        [-393.0750, -360.4750], [-386.3990, -361.0480], [-383.3470, -361.2330], [-378.8390, -361.3350], [-363.7820, -361.4180],
        [-362.9530, -363.4420], [-362.4490, -364.9310], [-362.0630, -366.4780], [-361.8030, -368.0910], [-361.6520, -369.7600],
        [-361.5670, -371.8140], [-361.5030, -380.5310], [-361.4110, -383.9800], [-361.2420, -386.6840], [-360.7020, -393.0190],
        [-360.4720, -395.3280], [-360.2150, -397.2680], [-359.2070, -403.3080], [-358.3140, -409.4190], [-357.9480, -411.6330],
        [-357.5800, -413.4910], [-356.5530, -418.0620], [-355.3250, -423.9020], [-354.7970, -426.0010], [-353.1890, -431.9440],
        [-352.2690, -435.1870], [-350.5870, -440.7230], [-347.7900, -449.0070], [-346.6320, -452.1570], [-344.7710, -456.8170],
        [-341.7200, -464.1650], [-339.9030, -468.2580], [-337.9290, -472.3400], [-335.0440, -478.0360], [-332.6110, -482.6290],
        [-329.6310, -488.0730], [-328.0600, -490.8190], [-326.3890, -493.5720], [-323.6130, -497.9580], [-321.4560, -501.2360],
        [-319.7700, -503.6520], [-315.9340, -508.9280], [-312.3590, -514.0100], [-311.0240, -515.8110], [-309.4860, -517.7740],
        [-303.4840, -524.9390], [-295.8330, -533.5030], [-293.7690, -535.6440], [-287.1440, -542.2670], [-285.4670, -543.8850],
        [-283.5560, -545.6220], [-278.7240, -549.7820], [-272.4060, -555.1350], [-269.5810, -557.3870], [-263.1320, -562.3820],
        [-259.7030, -564.8850], [-254.5660, -568.4110], [-249.9260, -571.4850], [-245.7800, -574.1230], [-243.3010, -575.5880],
        [-240.2920, -577.2620], [-230.3450, -582.7030], [-226.3010, -584.7950], [-222.9800, -586.3630], [-214.8200, -589.9950],
        [-211.0560, -591.5900], [-206.4140, -593.4520], [-203.2810, -594.6340], [-197.2150, -596.8010], [-191.6710, -598.6050],
        [-188.1770, -599.6790], [-182.2500, -601.3150], [-179.5590, -602.0140], [-169.8440, -604.2710], [-167.3910, -604.7960],
        [-161.1200, -605.9080], [-155.8180, -606.8960], [-153.9140, -607.1980], [-151.6510, -607.4990], [-148.3460, -607.8300],
        [-143.2840, -608.1620], [-140.9420, -608.3530], [-132.0650, -609.3120], [-128.3490, -609.5270], [-123.1390, -609.5940],
        [-97.9290, -609.6000], [-92.3350, -609.5870], [-89.2230, -609.5260], [-86.5240, -609.3670], [-83.9100, -609.0750],
        [-79.1460, -608.3130], [-75.6940, -607.6650], [-73.2440, -607.0630], [-70.8580, -606.3250], [-68.2320, -605.3870],
        [-63.0530, -603.3910], [-60.1020, -602.4100], [-57.5220, -600.4650], [-52.0700, -596.6280], [-49.1100, -594.3010],
        [-45.6670, -591.3630], [-43.2170, -589.0980], [-41.3390, -587.1640], [-39.3690, -584.8780], [-37.3480, -582.2340],
        [-35.2970, -579.2420], [-33.2410, -575.9590], [-32.1360, -574.0480], [-31.1160, -572.1320], [-30.3120, -570.4750],
        [-29.4450, -568.5070], [-28.5290, -566.2000], [-27.6770, -563.8510], [-26.9940, -561.7810], [-26.3950, -559.6880],
        [-25.8830, -557.5570], [-25.3660, -555.0850], [-24.8310, -552.2730], [-24.4740, -550.0470], [-24.2290, -548.0990],
        [-23.9340, -545.1310], [-23.5770, -541.1510], [-23.4210, -538.7960], [-23.3090, -535.0110], [-23.2810, -528.7170],
        [-23.1010, -378.7600], [-23.1130, -373.8730], [-23.1850, -368.1700], [-23.1250, -366.2920], [-22.9710, -364.7820],
        [-22.7090, -363.3110], [-22.2120, -361.2920], [22.1900, -361.2920], [22.6540, -363.0040], [22.9840, -364.4470],
        [23.1920, -365.6140], [23.3790, -367.0930], [23.5290, -368.9090], [23.6680, -371.4350], [23.8070, -376.4900],
        [23.9210, -526.2650], [23.8620, -531.4730], [23.6250, -536.8210], [23.5840, -538.7680], [23.6120, -540.3870],
        [23.7280, -542.6770], [23.9980, -546.6730], [24.2110, -548.9870], [24.6200, -551.8760], [25.3890, -555.9310],
        [26.0630, -558.9900], [26.7930, -561.6550], [27.8510, -564.7950], [29.1410, -568.1330], [30.3480, -570.8710],
        [31.7330, -573.5950], [33.4680, -576.5750], [35.5310, -579.7590], [37.6950, -582.7860], [39.8090, -585.4760],
        [41.7130, -587.6740], [43.7950, -589.8280], [46.0030, -591.8580], [48.7420, -594.1570], [50.7260, -595.7220],
        [52.4940, -597.0170], [54.3280, -598.2480], [56.4980, -599.5910], [58.6980, -600.8530], [60.8970, -602.0140],
        [63.3730, -603.2150], [65.8780, -604.3280], [67.8610, -605.1140], [70.1530, -605.9330], [72.4670, -606.6790],
        [74.2340, -607.1770], [76.0450, -607.6040], [77.8980, -607.9710], [81.3550, -608.5700], [83.9060, -608.9580],
        [85.8620, -609.1850], [87.5280, -609.3160], [89.5700, -609.4090], [91.6450, -609.4500], [121.0500, -609.4700],
        [126.9800, -609.4340], [129.3820, -609.3570], [131.7370, -609.2050], [141.2810, -608.1900], [149.3510, -607.6100],
        [152.6280, -607.2390], [155.5030, -606.8090], [161.1230, -605.7690], [166.4750, -604.8320], [169.5640, -604.1910],
        [178.9650, -601.9910], [187.5530, -599.6730], [190.7630, -598.7270], [196.2060, -596.9330], [203.8850, -594.2470],
        [208.7520, -592.3660], [214.2810, -590.0700], [223.0110, -586.1910], [226.0550, -584.7550], [229.3010, -583.0940],
        [242.7780, -575.7150], [245.5170, -574.1120], [248.7590, -572.0640], [253.2480, -569.1160], [258.6050, -565.4710],
        [261.0060, -563.7690], [263.3590, -562.0230], [270.5660, -556.4250], [272.6130, -554.7730], [274.8980, -552.8500],
        [280.5990, -547.9730], [284.4140, -544.6280], [287.3740, -541.8290], [293.8980, -535.2980], [296.7140, -532.3380],
        [303.4260, -524.7870], [308.6520, -518.5690], [311.1570, -515.3960], [312.6790, -513.3140], [316.2590, -508.2260],
        [319.9050, -503.2170], [321.7640, -500.5220], [323.7290, -497.5130], [326.3270, -493.4010], [327.8330, -490.9230],
        [329.4150, -488.1770], [332.6060, -482.4670], [333.9210, -480.0380], [335.2990, -477.3400], [338.5210, -470.8280],
        [339.8200, -468.1110], [341.0480, -465.3980], [343.0480, -460.7840], [344.4410, -457.4480], [345.9070, -453.7100],
        [347.2030, -450.2660], [350.2250, -441.4180], [352.5240, -433.8430], [354.8710, -425.2360], [355.6700, -421.9110],
        [357.3980, -413.9360], [357.8920, -411.4630], [358.3660, -408.6260], [359.1930, -402.8590], [360.0110, -397.7840],
        [360.3230, -395.5320], [360.5600, -393.2300], [361.0740, -387.2320], [361.2950, -383.8580], [361.3850, -380.4090],
        [361.4360, -372.0350], [361.5390, -368.9390], [361.7600, -366.2540], [362.1990, -362.9780], [364.0630, -361.2920],
        [380.5070, -361.2680], [383.6140, -361.1900], [386.3230, -361.0290], [392.3050, -360.4910], [395.2440, -360.1620],
        [401.9410, -359.1100], [408.7400, -358.1780], [411.2850, -357.7760], [413.4570, -357.3520], [418.0300, -356.3270],
        [422.9600, -355.3090], [426.5650, -354.4130], [433.3970, -352.5570], [438.9560, -350.9040], [442.1370, -349.9020],
        [448.4130, -347.7700], [451.8520, -346.5210], [456.2560, -344.7650], [462.2010, -342.2860], [467.6130, -339.9180],
        [471.2160, -338.2480], [477.0090, -335.3910], [480.0980, -333.8210], [482.8870, -332.3150], [488.6470, -329.0990],
        [491.3970, -327.5020], [495.2490, -325.1250], [499.9070, -322.1360], [503.1520, -319.9180], [508.6970, -315.8950],
        [513.7840, -312.3210], [515.8440, -310.7970], [517.5640, -309.4490], [519.6790, -307.6940], [525.4610, -302.7490],
        [531.7510, -297.2220], [533.5270, -295.6160], [535.4530, -293.7630], [542.3000, -286.9210], [543.9150, -285.2450],
        [545.4370, -283.5730], [549.3880, -278.9970], [554.9550, -272.4390], [557.2140, -269.6180], [562.2150, -263.1730],
        [564.7240, -259.7500], [568.0730, -254.8880], [571.1550, -250.2570], [573.9800, -245.8380], [575.7690, -242.8100],
        [580.3220, -234.6730], [582.8850, -229.8900], [584.8100, -226.1160], [586.5060, -222.5100], [589.7110, -215.3060],
        [591.4870, -211.1240], [593.2620, -206.7290], [594.5470, -203.3140], [597.0330, -196.2000], [598.7510, -191.0330],
        [599.7380, -187.8360], [601.4980, -181.6440], [602.0460, -179.5560], [604.7750, -167.3500], [605.8910, -161.0750],
        [606.8810, -155.7740], [607.1840, -153.8700], [607.4860, -151.6070], [607.8180, -148.3040], [608.1510, -143.2440],
        [608.3430, -140.9030], [609.3040, -132.0280], [609.5200, -128.3140], [609.5880, -123.1060], [609.6000, -97.9030],
        [609.5890, -92.3110], [609.5280, -89.2000], [609.3700, -86.5010], [609.0790, -83.8880], [608.3180, -79.1250],
        [607.6710, -75.6750], [607.0700, -73.2250], [606.3320, -70.8400], [605.3940, -68.2150], [603.3990, -63.0380],
        [602.4190, -60.0880], [600.4740, -57.5090], [597.3950, -53.0730], [595.7600, -50.8200], [593.6420, -48.1260],
        [591.5130, -45.6600], [589.1900, -43.2150], [586.9910, -41.1500], [584.7510, -39.2920], [581.7480, -37.0490],
        [578.6440, -34.9190], [575.6900, -33.0660], [574.0600, -32.1240], [572.4200, -31.2430], [571.0440, -30.5600],
        [569.3710, -29.7950], [567.3780, -28.9620], [565.3450, -28.1770], [563.0020, -27.3280], [561.2350, -26.7480],
        [559.7420, -26.3200], [557.9160, -25.8800], [553.2400, -24.9750], [551.3410, -24.6570], [549.7300, -24.4360],
        [546.7370, -24.1810], [543.9900, -24.0900], [539.1030, -24.0570], [376.9060, -23.8330], [374.1550, -23.7840],
        [371.4930, -23.6880], [368.9600, -23.5470], [367.1350, -23.3940], [365.6480, -23.2050], [364.4730, -22.9970],
        [363.0190, -22.6650], [361.2930, -22.2000], [361.2930, 22.2000], [362.7940, 22.6840], [364.9450, 23.2550],
        [365.8930, 23.4440], [367.1860, 23.6400], [368.5100, 23.7750], [369.8610, 23.8600], [373.3140, 23.9420],
        [540.2640, 24.0950], [545.4760, 24.1580], [547.5150, 24.2560], [549.1750, 24.3970], [552.0720, 24.7920],
        [556.1430, 25.5280], [558.9070, 26.1140], [561.0010, 26.6760], [563.9340, 27.6530], [567.7130, 29.0870],
        [570.5350, 30.3040], [573.0110, 31.5300], [576.0020, 33.2230], [578.9460, 35.0830], [582.0220, 37.2190],
        [584.7250, 39.2810], [586.9240, 41.1170], [589.1050, 43.1330], [590.9650, 45.0560], [593.1330, 47.5420],
        [594.5620, 49.2810], [595.9220, 51.0180], [597.0320, 52.5330], [597.9200, 53.8320], [598.9500, 55.4380],
        [600.1000, 57.3520], [601.1830, 59.2790], [602.1880, 61.2030], [603.2580, 63.4040], [604.2670, 65.6280],
        [605.0900, 67.6120], [605.8530, 69.6340], [606.4590, 71.3970], [607.0070, 73.1900], [607.4760, 75.0200],
        [607.8700, 76.8850], [608.6410, 81.3020], [609.1200, 84.4980], [609.3850, 87.1300], [609.5190, 89.8460],
        [609.5750, 95.0640], [609.5740, 124.1280], [609.5150, 128.2920], [609.3570, 131.3430], [609.1160, 133.9940],
        [608.3210, 141.2240], [607.8780, 147.6230], [607.6790, 149.9580], [607.3370, 152.9010], [606.9560, 155.4580],
        [605.8610, 161.3920], [604.9850, 166.4250], [604.4230, 169.2080], [603.3630, 173.7800], [602.0080, 179.9170],
        [601.4550, 182.0040], [600.0380, 187.0120], [599.1740, 189.9270], [598.0570, 193.3740], [594.8220, 202.7720],
        [593.4570, 206.4710], [591.4780, 211.4060], [589.5060, 216.0160], [585.7330, 224.4320], [584.1300, 227.7210],
        [580.6900, 234.4130], [579.0080, 237.9970], [577.2760, 240.6030], [573.8470, 246.2820], [570.4000, 251.6140],
        [565.7080, 258.5380], [564.1970, 260.6770], [562.6510, 262.7780], [557.0580, 269.9880], [554.1560, 273.5630],
        [549.2300, 279.3320], [545.8100, 283.2680], [543.8610, 285.4220], [541.8380, 287.5240], [535.0460, 294.2880],
        [532.5730, 296.6290], [524.5160, 303.7680], [519.2500, 308.1830], [517.1110, 309.9200], [513.8060, 312.4050],
        [508.7170, 315.9760], [503.9690, 319.4270], [501.5590, 321.1170], [498.8310, 322.9260], [494.9930, 325.3700],
        [491.9670, 327.2410], [489.4890, 328.6980], [482.6740, 332.5060], [479.9740, 333.9650], [477.2740, 335.3380],
        [470.4840, 338.6860], [467.7610, 339.9730], [465.0320, 341.1850], [456.2790, 344.8150], [452.4890, 346.3250],
        [449.9060, 347.2930], [441.3370, 350.2020], [433.7540, 352.4900], [425.7320, 354.6640], [422.7110, 355.3890],
        [418.0790, 356.3390], [413.1860, 357.4310], [411.3180, 357.7920], [409.0950, 358.1520], [402.6580, 359.0730],
        [397.2460, 359.9260], [394.3350, 360.3040], [386.7040, 361.0200], [382.9740, 361.2480], [378.4620, 361.3390],
        [363.7590, 361.4180], [362.9300, 363.4440], [362.4260, 364.9340], [362.0400, 366.4820], [361.7800, 368.0960],
        [361.6290, 369.7660], [361.5440, 371.8220], [361.4800, 380.5440], [361.3870, 383.9940], [361.2180, 386.7000],
        [360.6780, 393.0390], [360.4480, 395.3480], [360.1920, 397.2870], [359.3230, 402.6840], [358.3940, 409.0960],
        [357.9660, 411.6180], [357.4710, 414.0930], [355.4680, 423.2850], [354.8630, 425.6880], [353.0890, 432.2280],
        [352.1620, 435.4700], [350.4750, 441.0060], [347.6820, 449.2750], [346.4480, 452.6390], [344.4880, 457.6210],
        [342.5390, 462.2560], [340.5200, 466.8650], [338.7280, 470.6720], [335.1710, 477.8350], [333.7260, 480.6460],
        [332.2080, 483.4290], [329.1400, 488.9120], [327.5340, 491.6640], [324.9740, 495.7880], [322.1470, 500.1730],
        [320.3000, 502.8890], [314.4470, 511.2280], [311.9470, 514.6030], [309.6310, 517.5700], [303.6450, 524.7280],
        [295.7760, 533.5400], [293.7090, 535.6820], [287.0740, 542.3130], [285.3960, 543.9300], [283.7230, 545.4540],
        [279.1440, 549.4060], [272.5790, 554.9730], [269.7550, 557.2330], [263.3030, 562.2350], [259.8770, 564.7450],
        [255.0110, 568.0940], [250.3750, 571.1770], [245.9520, 574.0030], [242.9200, 575.7930], [234.7750, 580.3460],
        [229.9860, 582.9090], [226.2090, 584.8340], [222.6000, 586.5300], [215.3880, 589.7340], [211.2020, 591.5100],
        [206.8030, 593.2850], [203.3840, 594.5710], [196.2700, 597.0550], [191.1170, 598.7660], [187.9300, 599.7490],
        [181.7440, 601.5020], [179.6550, 602.0510], [167.4400, 604.7830], [155.8530, 606.8870], [153.9480, 607.1900],
        [151.6840, 607.4920], [148.3780, 607.8250], [140.9710, 608.3490], [132.0880, 609.3080], [128.3710, 609.5260],
        [123.1580, 609.5930], [98.2830, 609.6000], [92.3350, 609.5880], [89.2210, 609.5260], [86.5190, 609.3680],
        [83.9030, 609.0770], [79.1360, 608.3150], [75.6820, 607.6680], [73.2290, 607.0660], [70.8420, 606.3270],
        [68.2150, 605.3880], [63.0320, 603.3920], [60.0790, 602.4100], [57.4990, 600.4650], [53.0630, 597.3870],
        [51.0560, 595.9360], [48.3610, 593.8350], [45.6490, 591.5040], [43.1940, 589.1750], [41.0900, 586.9530],
        [39.1420, 584.6390], [37.1390, 581.9800], [35.2820, 579.2570], [33.2240, 575.9740], [32.2710, 574.3360],
        [31.3800, 572.6960], [30.6880, 571.3210], [29.9130, 569.6530], [29.1900, 567.9530], [28.3990, 565.9250],
        [27.6560, 563.8680], [26.9720, 561.7980], [26.4530, 560.0070], [25.9990, 558.1880], [24.9810, 553.2320],
        [24.6540, 551.3390], [24.4290, 549.7300], [24.2910, 548.4160], [24.1720, 546.7390], [24.0810, 543.9930],
        [24.0470, 539.1060], [23.8220, 376.9060], [23.7740, 374.1550], [23.6780, 371.4930], [23.5360, 368.9600],
        [23.3840, 367.1350], [23.1940, 365.6480], [22.9860, 364.4720], [22.6550, 363.0180], [22.1900, 361.2920],
        [-22.2120, 361.2920], [-22.2890, 361.5760], [-22.7090, 363.2950], [-22.9720, 364.7560], [-23.1270, 366.2570],
        [-23.1860, 368.1260], [-23.1090, 373.8170], [-23.0960, 378.7010], [-23.2480, 530.3450], [-23.2940, 536.2760],
        [-23.4560, 540.0380], [-24.1100, 547.3620], [-24.3340, 549.3250], [-24.6130, 551.2500], [-25.1820, 554.3880],
        [-25.8870, 557.7900], [-26.4860, 560.2170], [-27.1050, 562.3020], [-28.0130, 564.9560], [-29.0080, 567.5780],
        [-29.9660, 569.8480], [-31.0180, 572.0640], [-32.1840, 574.2530], [-33.6250, 576.7090], [-35.3590, 579.4430],
        [-36.8430, 581.6100], [-38.6250, 583.9800], [-40.5250, 586.2740], [-42.5440, 588.5170], [-44.6840, 590.6800],
        [-46.6590, 592.4710], [-48.9060, 594.3230], [-51.6470, 596.4180], [-54.2090, 598.2180], [-56.6090, 599.7570],
        [-59.0750, 601.1760], [-61.5850, 602.4480], [-64.3970, 603.7340], [-67.5240, 605.0370], [-70.4300, 606.1080],
        [-73.1090, 606.9550], [-75.5580, 607.5680], [-79.0110, 608.2230], [-83.7780, 608.9910], [-86.3890, 609.2910],
        [-89.0860, 609.4590], [-94.6430, 609.5400], [-124.0780, 609.5450], [-128.2460, 609.4870], [-131.6350, 609.3060],
        [-133.9530, 609.0920], [-140.8560, 608.3290], [-143.1980, 608.1350], [-148.9320, 607.7480], [-150.9180, 607.5520],
        [-153.1980, 607.2710], [-156.0660, 606.8280], [-161.3830, 605.8460], [-166.7750, 604.9460], [-168.6470, 604.5890],
        [-170.4830, 604.1810], [-174.7210, 603.1370], [-179.8980, 601.9250], [-186.1570, 600.2470], [-189.9790, 599.1410],
        [-196.3940, 597.0870], [-199.3110, 596.0770], [-206.1700, 593.6060], [-209.5500, 592.3000], [-212.6850, 590.9840],
        [-221.9170, 586.8790], [-224.9950, 585.4660], [-228.0030, 583.9870], [-234.4300, 580.6830], [-238.0160, 579.0000],
        [-240.6270, 577.2680], [-245.7720, 574.1750], [-248.7460, 572.2930], [-253.5030, 569.1650], [-258.8650, 565.5100],
        [-261.5320, 563.6100], [-264.1430, 561.6540], [-270.3320, 556.8380], [-272.8960, 554.7700], [-278.7040, 549.8380],
        [-282.7070, 546.3760], [-285.1010, 544.2380], [-287.2110, 542.2330], [-293.9360, 535.5040], [-295.8350, 533.5450],
        [-297.4390, 531.7870], [-303.9090, 524.4860], [-309.8750, 517.3290], [-311.7940, 514.8520], [-313.6730, 512.2880],
        [-320.1620, 503.1480], [-321.8330, 500.7180], [-325.5400, 494.9630], [-328.2350, 490.5590], [-332.3870, 483.1830],
        [-334.0050, 480.2090], [-335.5220, 477.2380], [-339.4150, 469.3380], [-341.1980, 465.4300], [-343.9510, 459.0030],
        [-345.4030, 455.4190], [-347.1110, 450.9700], [-347.9120, 448.7120], [-350.4150, 441.2970], [-352.0190, 436.0570],
        [-352.9570, 432.8260], [-354.8920, 425.6950], [-355.4250, 423.5950], [-357.3660, 414.7000], [-357.8630, 412.2250],
        [-358.2840, 409.6990], [-359.2180, 403.2730], [-360.2220, 397.2490], [-360.4780, 395.3100], [-360.6790, 393.3330],
        [-361.2490, 386.6590], [-361.4180, 383.9520], [-361.5110, 380.5000], [-361.5790, 371.7760], [-361.6640, 369.7220],
        [-361.8130, 368.0560], [-362.0710, 366.4490], [-362.4550, 364.9090], [-362.9560, 363.4290], [-363.7820, 361.4180],
        [-380.2460, 361.3180], [-383.3600, 361.2330], [-386.4140, 361.0460], [-393.7580, 360.4130], [-396.3760, 360.1200],
        [-402.7450, 359.1220], [-408.8430, 358.2480], [-411.9960, 357.7100], [-421.5260, 355.6880], [-424.2640, 355.0560],
        [-432.9000, 352.7360], [-438.1820, 351.1840], [-442.2390, 349.9150], [-450.4930, 347.1010], [-456.3350, 344.8600],
        [-461.2640, 342.8240], [-466.1520, 340.7100], [-469.6890, 339.0800], [-478.2380, 334.8570], [-481.8930, 332.9480],
        [-488.7690, 329.1190], [-492.0750, 327.1880], [-498.3960, 323.2200], [-502.7570, 320.3060], [-512.1930, 313.6160],
        [-515.2800, 311.3550], [-518.4550, 308.8560], [-524.1730, 304.0780], [-532.3920, 296.7950], [-534.1490, 295.1810],
        [-542.0390, 287.3460], [-544.7810, 284.4770], [-548.7460, 279.9330], [-555.1600, 272.3850], [-560.4330, 265.6980],
        [-563.3960, 261.8060], [-566.2410, 257.7980], [-570.6420, 251.2830], [-573.8440, 246.3160], [-577.2970, 240.6060],
        [-579.0310, 237.9970], [-580.5800, 234.6840], [-584.4300, 227.1740], [-586.4070, 223.0320], [-589.2100, 216.7430],
        [-590.8780, 212.8770], [-592.7050, 208.4240], [-594.1540, 204.6940], [-597.4380, 195.3010], [-598.8550, 191.0020],
        [-599.7440, 188.1010], [-601.9180, 180.0910], [-604.3220, 169.7660], [-604.7180, 167.9260], [-605.1300, 165.7440],
        [-605.9780, 160.6870], [-606.9880, 155.0260], [-607.4670, 151.8280], [-607.8510, 148.2180], [-608.3510, 141.1600],
        [-609.1840, 133.5850], [-609.4330, 130.5770], [-609.5650, 127.1510], [-609.6000, 121.9150], [-609.5950, 93.8870],
        [-609.5570, 90.4070], [-609.4650, 88.0130], [-609.3130, 86.0080], [-609.0410, 83.7300], [-608.5920, 80.8670],
        [-607.9790, 77.4200], [-607.5930, 75.5790], [-607.1400, 73.7830], [-606.6210, 72.0280], [-605.9530, 70.0070],
        [-605.1240, 67.7160], [-604.3240, 65.7380], [-603.3280, 63.5130], [-602.1240, 61.0360], [-601.1120, 59.1140],
        [-600.0170, 57.1920], [-598.8370, 55.2840], [-597.5820, 53.4090], [-596.4510, 51.8340], [-595.2760, 50.2850],
        [-592.6100, 46.9960], [-590.2050, 44.2660], [-589.0510, 43.0580], [-587.8600, 41.8950], [-585.6530, 39.9580],
        [-582.9200, 37.8420], [-579.6130, 35.5120], [-576.4200, 33.4620], [-573.4320, 31.7410], [-572.0640, 31.0280],
        [-570.4060, 30.2320], [-568.7210, 29.4910], [-567.0010, 28.7930], [-562.9160, 27.2860], [-560.5590, 26.5410],
        [-558.1470, 25.9360], [-553.4870, 25.0330], [-550.3100, 24.5290], [-548.3440, 24.3180], [-546.3230, 24.1910],
        [-543.9140, 24.1230], [-540.7770, 24.0980], [-372.6970, 23.9500], [-369.2550, 23.8360], [-367.9120, 23.7260],
        [361.7110, -265.2760], [361.6060, -263.9360], [361.4990, -260.4950], [361.2930, -115.9180], [362.7960, -115.4160],
        [364.0200, -115.0600], [365.2730, -114.7660], [366.2350, -114.5920], [367.5470, -114.4200], [368.8900, -114.3090],
        [372.3320, -114.1980], [517.1490, -113.9850], [517.7560, -115.6600], [518.1740, -117.1180], [518.4240, -118.3440],
        [518.6270, -119.9510], [518.7310, -121.6240], [518.7690, -123.6840], [518.7460, -126.8150], [518.6620, -129.9350],
        [518.4920, -132.6500], [518.1860, -135.2770], [517.3160, -140.6840], [516.3790, -147.0940], [516.0460, -148.9840],
        [515.6570, -150.8340], [513.6500, -158.9560], [512.8290, -161.9120], [510.6910, -168.6110], [509.8700, -170.9390],
        [508.7860, -173.8280], [506.1510, -180.3610], [505.3120, -182.3180], [504.4250, -184.2520], [503.0780, -186.9770],
        [501.1180, -190.7520], [499.6770, -193.4430], [498.4590, -195.5970], [496.1390, -199.4120], [493.4380, -203.5450],
        [490.3140, -208.1040], [487.7590, -211.6070], [485.2760, -214.7520], [481.9580, -218.7250], [477.8030, -223.3900],
        [475.4550, -225.8780], [474.1410, -227.1530], [470.8880, -230.1530], [467.4900, -233.4060], [465.9970, -234.7800],
        [463.7080, -236.7160], [459.8430, -239.7440], [456.2410, -242.4820], [453.1320, -244.6550], [446.7780, -248.8590],
        [444.8680, -250.0340], [442.6770, -251.2990], [437.4940, -254.1210], [433.6590, -256.0550], [427.5470, -258.8510],
        [422.4830, -261.0130], [419.0690, -262.3130], [414.2020, -263.9610], [407.7940, -265.9070], [404.2340, -266.8980],
        [401.4870, -267.5360], [393.4820, -269.2280], [390.9540, -269.6600], [388.3600, -269.9920], [378.4800, -270.9850],
        [373.8110, -271.3690], [371.7690, -271.4600], [369.6990, -271.5020], [363.0680, -271.4970], [362.3020, -268.7860],
        [362.0330, -267.5410], [361.8710, -266.5840], [362.1330, 267.5720], [362.4260, 268.8260], [362.7810, 270.0500],
        [363.2820, 271.5540], [370.2660, 271.5160], [372.6720, 271.4380], [374.7030, 271.3150], [381.0240, 270.7320],
        [388.3020, 269.9890], [390.9180, 269.6760], [393.1570, 269.3250], [395.6520, 268.8310], [402.0990, 267.3910],
        [404.2290, 266.8760], [406.3200, 266.3090], [411.8890, 264.6570], [415.0740, 263.6480], [419.3700, 262.1760],
        [422.5040, 260.9780], [426.1800, 259.4250], [430.3820, 257.5470], [433.9900, 255.8720], [437.0100, 254.3820],
        [440.0290, 252.7980], [443.0860, 251.0910], [445.5980, 249.5880], [448.0780, 247.9970], [453.5130, 244.3670],
        [455.9340, 242.6810], [458.5590, 240.7190], [463.4650, 236.8880], [465.2520, 235.4130], [467.0010, 233.8670],
        [473.2440, 228.0720], [475.1590, 226.2220], [477.4660, 223.7850], [481.3840, 219.4080], [483.9400, 216.4060],
        [486.5250, 213.2380], [488.2020, 211.0670], [490.2020, 208.3270], [493.2820, 203.9380], [495.3190, 200.9060],
        [497.0730, 198.0870], [499.1090, 194.5760], [501.0530, 190.9920], [503.5970, 186.1010], [504.6670, 183.9130],
        [505.6730, 181.6950], [507.0890, 178.3200], [508.5790, 174.6170], [509.8950, 171.1530], [510.8270, 168.5330],
        [512.4320, 163.5780], [513.4220, 160.3720], [514.2310, 157.3980], [515.4940, 152.2770], [516.0390, 149.8300],
        [516.4480, 147.6390], [517.5440, 140.2660], [518.3690, 135.1720], [518.6150, 133.2110], [518.7620, 131.5360],
        [518.9170, 128.1000], [518.9940, 122.5110], [518.9540, 118.6670], [518.7980, 114.8340], [515.8540, 114.4320],
        [513.5170, 114.2160], [511.1270, 114.1020], [507.6550, 114.0490], [372.9630, 113.9490], [370.8840, 113.9810],
        [369.1820, 114.0570], [367.8620, 114.1800], [366.6040, 114.3890], [365.4380, 114.7170], [364.6440, 115.0600],
        [363.9340, 115.4960], [363.3190, 116.0310], [362.8040, 116.6650], [362.5160, 117.1390], [362.2730, 117.6520],
        [361.9830, 118.4850], [361.7190, 119.6950], [361.5620, 120.9870], [361.4780, 122.3310], [361.4280, 124.3970],
        [361.5680, 260.5100], [361.6780, 263.9540], [361.7880, 265.2970], [361.9590, 266.6100], [-268.7670, -22.9140],
        [-269.8970, -22.6560], [-271.5750, -22.2000], [-271.5750, 22.2000], [-269.8900, 22.7140], [-268.7540, 23.0080],
        [-267.6030, 23.2470], [-266.1340, 23.4650], [-264.6220, 23.6120], [-262.7330, 23.7250], [-258.0330, 23.8420],
        [-95.4940, 23.9560], [-90.2670, 24.0030], [-87.2060, 24.1480], [-84.9060, 24.3870], [-82.6750, 24.7330],
        [-78.9340, 25.4530], [-75.8720, 26.1350], [-73.7860, 26.6960], [-71.4560, 27.4280], [-68.8690, 28.3380],
        [-66.5920, 29.2290], [-64.3530, 30.2140], [-61.8860, 31.4190], [-59.4680, 32.7050], [-57.3550, 33.9390],
        [-55.5260, 35.1160], [-53.4520, 36.5730], [-51.1360, 38.3290], [-49.1090, 39.9820], [-46.4230, 42.3570],
        [-44.1240, 44.5740], [-41.9190, 46.9020], [-39.5590, 49.6140], [-37.5300, 52.1690], [-35.4640, 55.0170],
        [-33.7750, 57.6300], [-32.2620, 60.2830], [-30.5990, 63.5420], [-29.3400, 66.3320], [-28.1240, 69.4650],
        [-26.9570, 72.9290], [-26.2080, 75.5940], [-25.4520, 78.9570], [-24.6770, 83.0130], [-24.2150, 86.2230],
        [-23.9880, 88.5340], [-23.4000, 95.5490], [-23.2570, 98.2710], [-23.1960, 101.0400], [-23.0680, 254.1050],
        [-23.1400, 265.0590], [-23.0760, 266.9280], [-22.9150, 268.4180], [-22.6440, 269.8610], [-22.2120, 271.5540],
        [22.1900, 271.5540], [22.6620, 269.8500], [22.9330, 268.7030], [23.1510, 267.5420], [23.3510, 266.0650],
        [23.5110, 264.2400], [23.6400, 262.0190], [23.7790, 256.9520], [23.9230, 95.1150], [23.9700, 90.2380],
        [24.0320, 88.5250], [24.1430, 86.8440], [24.3990, 84.5540], [24.7580, 82.3310], [25.5520, 78.2870],
        [26.1810, 75.5430], [26.7550, 73.4640], [27.4980, 71.1400], [28.4180, 68.5550], [29.3200, 66.2820],
        [30.3180, 64.0480], [31.5330, 61.5870], [32.8310, 59.1750], [34.0790, 57.0660], [35.4470, 54.9820],
        [36.9210, 52.9190], [38.6550, 50.6380], [40.4310, 48.4510], [42.4550, 46.1790], [44.5830, 44.0260],
        [47.3640, 41.4570], [50.0980, 39.1250], [52.9360, 36.9180], [55.5870, 35.0280], [58.0310, 33.4550],
        [60.5010, 32.0470], [63.2530, 30.6670], [66.3200, 29.3100], [69.4500, 28.1050], [72.9140, 26.9390],
        [75.5770, 26.1920], [78.3220, 25.5660], [82.6820, 24.7200], [85.5650, 24.2960], [87.2170, 24.1400],
        [89.2480, 24.0280], [94.4580, 23.9530], [258.0700, 23.8300], [262.7660, 23.7120], [265.8600, 23.4890],
        [267.0370, 23.3350], [268.1890, 23.1270], [269.3220, 22.8620], [271.5520, 22.2000], [271.5520, -22.2000],
        [269.8590, -22.6550], [268.7200, -22.9140], [267.2730, -23.1680], [265.7890, -23.3530], [263.6310, -23.5390],
        [261.3670, -23.6750], [256.5950, -23.8080], [95.1360, -23.9330], [90.2600, -23.9780], [86.8640, -24.1480],
        [84.5730, -24.3980], [82.3440, -24.7460], [78.2840, -25.4980], [75.5400, -26.1080], [73.4760, -26.6900],
        [71.4570, -27.3580], [68.5790, -28.4060], [65.9520, -29.4570], [63.5830, -30.5070], [61.5050, -31.5130],
        [59.4560, -32.6040], [57.4630, -33.7820], [55.2630, -35.2250], [53.1350, -36.7450], [50.8020, -38.5350],
        [48.7800, -40.2010], [46.1200, -42.5570], [43.6650, -44.9070], [41.7950, -46.8730], [39.7900, -49.1990],
        [37.4470, -52.1910], [35.2250, -55.2850], [33.5590, -57.9000], [32.0620, -60.5580], [30.5450, -63.5500],
        [29.2880, -66.3400], [28.0740, -69.4740], [26.9080, -72.9380], [26.1600, -75.6030], [25.4060, -78.9660],
        [24.6320, -83.0230], [24.1720, -86.2340], [23.9460, -88.5450], [23.3360, -95.8970], [23.1960, -98.9710],
        [23.1460, -102.4460], [23.0440, -254.4570], [23.1140, -265.3770], [23.0530, -266.9280], [22.8920, -268.4180],
        [22.6210, -269.8610], [22.1900, -271.5540], [-22.2120, -271.5540], [-22.6430, -269.8470], [-22.9130, -268.3940],
        [-23.0740, -266.8940], [-23.1380, -265.0170], [-23.0680, -254.4050], [-23.1630, -104.4700], [-23.2320, -98.5520],
        [-23.3230, -96.5020], [-23.4910, -94.1450], [-24.0050, -88.1400], [-24.2430, -85.8360], [-24.5620, -83.5860],
        [-25.0740, -80.7610], [-25.7730, -77.3580], [-26.4380, -74.6380], [-27.3250, -71.7100], [-28.4350, -68.5490],
        [-29.4450, -65.9930], [-30.6900, -63.2050], [-31.9270, -60.7260], [-33.3180, -58.2560], [-34.6960, -56.0790],
        [-36.3640, -53.6830], [-38.4910, -50.8540], [-40.4660, -48.4150], [-42.4910, -46.1430], [-44.6190, -43.9900],
        [-47.4010, -41.4220], [-50.1360, -39.0910], [-52.9730, -36.8850], [-55.6250, -34.9960], [-58.0690, -33.4250],
        [-60.5400, -32.0190], [-63.2970, -30.6370], [-66.3720, -29.2760], [-69.7860, -27.9590], [-73.5180, -26.6830],
        [-75.8830, -26.0270], [-78.3270, -25.4930], [-82.7040, -24.6880], [-85.5920, -24.2740], [-87.2450, -24.1190],
        [-89.2760, -24.0080], [-94.4850, -23.9330], [-256.6680, -23.8060], [-261.4390, -23.6720], [-263.7020, -23.5360],
        [-265.8540, -23.3520], [-267.3300, -23.1680], [114.2080, -266.1390], [114.0940, -263.7460], [114.0410, -260.2680],
        [113.9200, -115.9180], [115.9100, -113.9280], [260.2660, -114.0490], [263.7430, -114.1010], [266.1360, -114.2150],
        [268.4770, -114.4320], [271.4260, -114.8340], [271.4230, -260.2660], [271.3730, -263.7440], [271.2610, -266.1370],
        [271.0460, -268.4790], [270.6460, -271.4280], [265.4110, -271.6640], [259.4620, -271.7210], [114.8260, -271.4280],
        [114.4240, -268.4790], [271.2920, 374.7430], [271.4010, 372.7130], [271.4580, 370.3080], [271.4260, 362.9790],
        [269.5620, 361.2920], [115.6070, 361.4180], [114.8790, 364.2220], [114.4840, 366.4790], [114.2690, 368.8200],
        [114.1650, 372.2670], [114.0790, 506.2860], [114.0990, 509.0730], [114.1610, 511.1310], [114.2570, 512.4630],
        [114.4310, 513.7360], [114.7140, 514.9190], [115.0190, 515.7240], [115.4170, 516.4440], [115.9150, 517.0670],
        [116.3030, 517.4250], [116.7350, 517.7370], [117.2090, 518.0040], [117.9920, 518.3240], [118.5570, 518.4880],
        [119.4570, 518.6730], [121.0630, 518.8530], [122.4080, 518.9230], [124.4750, 518.9620], [129.3380, 518.9310],
        [132.4020, 518.7870], [135.0330, 518.5100], [141.6890, 517.4260], [148.0680, 516.4690], [149.9420, 516.1200],
        [151.7750, 515.7120], [158.9850, 513.9140], [161.6450, 513.1730], [168.0530, 511.1360], [172.6980, 509.4630],
        [176.1400, 508.1200], [180.6610, 506.2600], [183.1670, 505.1590], [185.3620, 504.1110], [189.7000, 501.8780],
        [194.0890, 499.5220], [197.3540, 497.6510], [200.4580, 495.7480], [203.4790, 493.7410], [207.8610, 490.6740],
        [210.8730, 488.4850], [213.2960, 486.6150], [216.7190, 483.8150], [219.4730, 481.4630], [223.8520, 477.5350],
        [226.2910, 475.2280], [227.9340, 473.5330], [233.4580, 467.5770], [234.7970, 466.0930], [236.0920, 464.5760],
        [238.1440, 462.0070], [242.5310, 456.3350], [244.2510, 453.9920], [245.8820, 451.6200], [248.1000, 448.1730],
        [250.1970, 444.7580], [251.8640, 441.8700], [253.4500, 438.9450], [255.5150, 434.8930], [257.4710, 430.8380],
        [259.3060, 426.8000], [260.7980, 423.2560], [262.0570, 419.9050], [263.6910, 415.0550], [264.6950, 411.8710],
        [266.3420, 406.3040], [266.9060, 404.2130], [267.4180, 402.0830], [268.8530, 395.6470], [269.3430, 393.1650],
        [269.6890, 390.9380], [269.9980, 388.3310], [270.7980, 380.3970], [124.2870, 271.5200], [259.4620, 271.7270],
        [265.4100, 271.6660], [270.6460, 271.4290], [271.0460, 268.4790], [271.2610, 266.1380], [271.3730, 263.7440],
        [271.4230, 260.2660], [271.4260, 114.8340], [268.4780, 114.4340], [266.1380, 114.2190], [263.7450, 114.1070],
        [260.2690, 114.0570], [115.6070, 114.0540], [113.9200, 115.9180], [113.9190, 257.3730], [113.9740, 262.9400],
        [114.0680, 264.6270], [114.2170, 265.9210], [114.4660, 267.1340], [114.7400, 267.9690], [114.9710, 268.4820],
        [115.2440, 268.9550], [115.7380, 269.5840], [116.3330, 270.1100], [117.0250, 270.5330], [117.8060, 270.8580],
        [118.6620, 271.0970], [119.5800, 271.2630], [120.8730, 271.4010], [122.2180, 271.4750], [114.7620, -365.2730],
        [115.0550, -364.0200], [115.4090, -362.7960], [115.9100, -361.2920], [269.7760, -361.3490], [271.5520, -363.2820],
        [271.5200, -369.9130], [271.4650, -371.9810], [271.3600, -374.0210], [271.1760, -376.3650], [270.7630, -380.6760],
        [269.8430, -389.5860], [269.4890, -392.1730], [269.0300, -394.6900], [267.4050, -402.0280], [266.6650, -405.0360],
        [264.7830, -411.4690], [263.4060, -415.8030], [261.8090, -420.3780], [260.3290, -424.0720], [258.9700, -427.2010],
        [256.8910, -431.8250], [254.7230, -436.3640], [253.3180, -439.0880], [252.0050, -441.5010], [250.6170, -443.9160],
        [249.3050, -446.0810], [245.6880, -451.6860], [243.1750, -455.3300], [241.4410, -457.6520], [238.2600, -461.7500],
        [235.4230, -465.2870], [233.2040, -467.7550], [226.3980, -474.8590], [224.3970, -476.7920], [219.6050, -481.2240],
        [217.8550, -482.7550], [215.6130, -484.6330], [213.4190, -486.4140], [211.4850, -487.9220], [207.2220, -491.0260],
        [202.3070, -494.3990], [198.4180, -496.8410], [193.7770, -499.5770], [188.2930, -502.5200], [183.9280, -504.7140],
        [180.5830, -506.2050], [175.4850, -508.2930], [171.1650, -509.9480], [167.6720, -511.1770], [162.7200, -512.7580],
        [160.0820, -513.5380], [152.2830, -515.5050], [149.8460, -516.0620], [147.3400, -516.5150], [141.2740, -517.4160],
        [135.8960, -518.3070], [134.2840, -518.5270], [132.6360, -518.6930], [130.6110, -518.8130], [127.8520, -518.8760],
        [114.9150, -518.8610], [114.4800, -515.9200], [114.2480, -513.5860], [114.1270, -511.1980], [114.0760, -507.7270],
        [114.1890, -373.3790], [114.2870, -369.2310], [114.3850, -367.8810], [114.5390, -366.5600], [-271.3350, -374.7020],
        [-271.4580, -372.6710], [-271.5360, -370.2640], [-271.5750, -363.2820], [-269.5850, -361.2920], [-115.6290, -361.4180],
        [-114.9010, -364.2210], [-114.6530, -365.5000], [-114.4650, -366.8070], [-114.3360, -368.1410], [-114.2550, -369.5000],
        [-114.1750, -373.6580], [-114.0810, -507.6490], [-114.1280, -511.1210], [-114.2390, -513.5110], [-114.4520, -515.8480],
        [-114.8490, -518.7920], [-127.4480, -518.8540], [-130.2150, -518.8110], [-132.2510, -518.7120], [-133.9100, -518.5660],
        [-135.5330, -518.3630], [-140.3030, -517.6090], [-147.6710, -516.5100], [-149.5470, -516.1520], [-151.6860, -515.6660],
        [-158.9000, -513.8600], [-161.2700, -513.2050], [-165.6410, -511.8430], [-168.8550, -510.7860], [-172.6330, -509.4340],
        [-176.0910, -508.1330], [-179.2210, -506.8520], [-182.3140, -505.4910], [-184.8050, -504.3090], [-187.8020, -502.7840],
        [-191.3240, -500.8970], [-194.5850, -499.0550], [-199.6650, -496.0700], [-202.4970, -494.2900], [-205.5980, -492.1840],
        [-209.2040, -489.6330], [-211.6740, -487.8010], [-213.8490, -486.0920], [-217.0470, -483.4590], [-219.8010, -481.0870],
        [-223.1970, -478.0040], [-225.8430, -475.4720], [-228.2710, -472.9870], [-233.1850, -467.7910], [-234.9710, -465.8140],
        [-236.4630, -464.0360], [-238.6730, -461.1990], [-243.1340, -455.2730], [-244.7670, -452.9470], [-247.7320, -448.5380],
        [-249.4160, -445.9430], [-250.9930, -443.3320], [-252.6220, -440.4300], [-254.1780, -437.4790], [-255.6680, -434.4780],
        [-257.2220, -431.1540], [-259.3560, -426.3960], [-260.9150, -422.7230], [-262.1210, -419.5910], [-263.5970, -415.2950],
        [-264.6990, -411.8210], [-266.3510, -406.2520], [-266.9130, -404.1580], [-267.3470, -402.3290], [-268.9330, -394.9540],
        [-269.3640, -392.7870], [-269.7200, -390.5660], [-270.0370, -387.9620], [-270.7520, -381.0220], [-271.3980, 263.7560],
        [-271.2850, 266.1460], [-271.0690, 268.4840], [-270.6690, 271.4290], [-265.4330, 271.6640], [-259.4850, 271.7220],
        [-114.8490, 271.4290], [-114.4490, 268.4810], [-114.2340, 266.1410], [-114.1220, 263.7480], [-114.0720, 260.2720],
        [-114.0690, 115.6140], [-115.9330, 113.9280], [-258.3330, 113.9040], [-263.1910, 113.9670], [-264.8680, 114.0720],
        [-266.1480, 114.2360], [-267.3410, 114.5070], [-268.1570, 114.8010], [-268.6550, 115.0470], [-269.1120, 115.3370],
        [-269.7150, 115.8550], [-270.2140, 116.4730], [-270.6110, 117.1880], [-270.9120, 117.9880], [-271.1300, 118.8600],
        [-271.2790, 119.7900], [-271.4010, 121.0940], [-271.4720, 122.7880], [-271.5010, 124.8650], [-271.4490, 260.2830],
        [-132.2520, 518.7120], [-130.2160, 518.8110], [-127.4490, 518.8540], [-114.8490, 518.7930], [-114.4520, 515.8480],
        [-114.2390, 513.5110], [-114.1280, 511.1220], [-114.0810, 507.6500], [-114.1750, 373.6580], [-114.2550, 369.5000],
        [-114.3360, 368.1420], [-114.4650, 366.8070], [-114.6530, 365.5000], [-114.9010, 364.2220], [-115.6290, 361.4180],
        [-269.5850, 361.2920], [-271.5750, 363.2820], [-271.5430, 369.9180], [-271.4870, 371.9870], [-271.3820, 374.0260],
        [-271.1680, 376.7030], [-270.6560, 382.0090], [-269.8050, 389.9220], [-269.4700, 392.1690], [-269.0550, 394.3600],
        [-267.4100, 402.0440], [-266.7560, 404.7660], [-265.9270, 407.7120], [-264.1670, 413.5370], [-262.8350, 417.5590],
        [-261.7090, 420.7040], [-260.5750, 423.5450], [-258.9960, 427.2120], [-256.7230, 432.2400], [-255.1430, 435.5520],
        [-253.4650, 438.8410], [-251.8110, 441.8810], [-250.1880, 444.6730], [-248.6270, 447.1680], [-245.1750, 452.3370],
        [-243.3000, 455.0340], [-240.9540, 458.1930], [-236.7900, 463.6300], [-235.3150, 465.4160], [-233.7640, 467.1650],
        [-226.7680, 474.6280], [-224.3300, 476.9980], [-220.2350, 480.7070], [-217.4800, 483.0950], [-214.0260, 485.9480],
        [-211.6070, 487.8500], [-209.1350, 489.6810], [-205.0130, 492.5960], [-201.7050, 494.8540], [-198.9160, 496.6300],
        [-195.4500, 498.6740], [-192.4170, 500.3530], [-188.0510, 502.6580], [-185.0620, 504.1800], [-182.5830, 505.3640],
        [-179.5030, 506.7290], [-176.3800, 508.0180], [-172.9260, 509.3270], [-168.8580, 510.7850], [-165.6440, 511.8420],
        [-161.2720, 513.2050], [-158.9020, 513.8590], [-151.6880, 515.6660], [-149.5490, 516.1520], [-147.6730, 516.5100],
        [-140.3050, 517.6090], [-135.5340, 518.3630], [-133.9110, 518.5660], [-271.4390, -264.5370], [-271.5090, -263.1860],
        [-271.5520, -261.1150], [-271.4490, -114.8340], [-268.5000, -114.4320], [-266.1590, -114.2150], [-263.7660, -114.1010],
        [-260.2890, -114.0490], [-115.9330, -113.9280], [-114.0690, -115.6140], [-114.0720, -260.2720], [-114.1220, -263.7480],
        [-114.2340, -266.1400], [-114.4490, -268.4800], [-114.8490, -271.4280], [-261.1350, -271.7750], [-263.2040, -271.7300],
        [-264.5520, -271.6540], [-265.8480, -271.5100], [-266.7690, -271.3370], [-267.6300, -271.0930], [-268.4160, -270.7620],
        [-269.1140, -270.3360], [-269.7140, -269.8090], [-270.2140, -269.1800], [-270.6140, -268.4570], [-270.9210, -267.6510],
        [-271.1470, -266.7740], [-271.3060, -265.8420], [-509.8410, 114.0950], [-512.9360, 114.2050], [-515.6180, 114.4440],
        [-518.8890, 114.9230], [-518.9120, 127.5010], [-518.8590, 130.2630], [-518.7520, 132.2940], [-518.6010, 133.9480],
        [-518.3930, 135.5670], [-517.6360, 140.3290], [-516.5940, 147.3690], [-516.2450, 149.2470], [-515.7680, 151.3880],
        [-513.9680, 158.5910], [-513.3220, 160.9630], [-512.1530, 164.7460], [-510.9160, 168.5360], [-509.8750, 171.4400],
        [-508.5560, 174.8940], [-507.0660, 178.5830], [-505.7660, 181.6710], [-504.7560, 183.8900], [-503.5450, 186.3500],
        [-500.8690, 191.4780], [-499.2480, 194.4360], [-497.4920, 197.4120], [-495.4110, 200.7060], [-492.8530, 204.5510],
        [-490.4640, 208.0080], [-488.4610, 210.7690], [-486.5960, 213.1850], [-483.8040, 216.5980], [-481.2360, 219.5960],
        [-477.3310, 223.9410], [-475.0280, 226.3480], [-473.3240, 227.9830], [-467.0860, 233.7670], [-465.5900, 235.0920],
        [-463.8090, 236.5730], [-458.9210, 240.3920], [-456.0880, 242.5170], [-453.7560, 244.1460], [-448.7640, 247.4750],
        [-446.3340, 249.0390], [-443.8710, 250.5090], [-439.7720, 252.7800], [-435.9640, 254.8000], [-432.7090, 256.4200],
        [-429.2090, 258.0630], [-425.7040, 259.6170], [-422.6930, 260.8560], [-419.6120, 261.9950], [-413.6340, 264.0390],
        [-410.7320, 264.9360], [-406.6060, 266.1070], [-404.2080, 266.7340], [-402.0710, 267.2290], [-394.7030, 268.8010],
        [-391.9000, 269.3250], [-389.0050, 269.7200], [-383.0760, 270.3430], [-376.4480, 270.9800], [-373.0900, 271.2160],
        [-370.3540, 271.2850], [-367.6050, 271.2240], [-364.8900, 271.0080], [-362.2210, 270.6480], [-361.7870, 267.3710],
        [-361.5690, 264.6860], [-361.4700, 261.5890], [-361.4470, 256.3520], [-361.5270, 125.0860], [-361.5720, 121.9510],
        [-361.6810, 119.5400], [-361.9000, 117.1680], [-362.2210, 114.8340], [-364.8370, 114.4740], [-367.1670, 114.2450],
        [-369.5510, 114.1190], [-373.0190, 114.0610], [-504.2560, 114.0660], [-518.7470, -132.2110], [-518.8450, -130.1780],
        [-518.8860, -127.4140], [-518.8210, -114.8340], [-515.8750, -114.4320], [-513.5370, -114.2170], [-511.1470, -114.1030],
        [-507.6730, -114.0510], [-372.9310, -113.9790], [-370.8510, -114.0110], [-369.1480, -114.0870], [-367.8270, -114.2090],
        [-366.5670, -114.4170], [-365.4000, -114.7450], [-364.6050, -115.0870], [-363.8930, -115.5220], [-363.2760, -116.0560],
        [-362.7590, -116.6880], [-362.3420, -117.4130], [-362.0210, -118.2200], [-361.7850, -119.0980], [-361.6200, -120.0320],
        [-361.4830, -121.3390], [-361.4000, -123.0340], [-361.3660, -125.1130], [-361.4390, -259.5010], [-361.4900, -262.9740],
        [-361.6040, -265.3640], [-361.8200, -267.7030], [-362.2210, -270.6480], [-364.8900, -271.0080], [-367.2640, -271.2050],
        [-370.0110, -271.2840], [-372.7520, -271.2310], [-376.1170, -271.0090], [-382.0870, -270.4410], [-388.6820, -269.7580],
        [-391.5890, -269.3760], [-394.4050, -268.8620], [-401.4660, -267.3570], [-403.6070, -266.8740], [-405.7110, -266.3320],
        [-410.7020, -264.8730], [-414.1880, -263.8000], [-418.4870, -262.3600], [-421.6250, -261.2070], [-424.4570, -260.0490],
        [-428.1130, -258.4580], [-432.5730, -256.4340], [-435.6060, -254.9700], [-438.8820, -253.2610], [-443.2500, -250.8620],
        [-445.7170, -249.4160], [-447.9000, -248.0370], [-453.5930, -244.2500], [-456.0120, -242.5690], [-458.6350, -240.6120],
        [-463.2800, -236.9960], [-465.3230, -235.3210], [-467.0710, -233.7800], [-472.6440, -228.5920], [-474.3370, -226.9590],
        [-476.1900, -225.0370], [-481.2170, -219.5920], [-483.1750, -217.3460], [-485.8240, -214.1460], [-487.7270, -211.7380],
        [-489.7380, -209.0250], [-492.1190, -205.6290], [-494.6950, -201.7990], [-496.8460, -198.4600], [-498.7040, -195.3710],
        [-500.4200, -192.2980], [-503.0120, -187.3850], [-504.3840, -184.6610], [-505.5430, -182.1730], [-506.7400, -179.3680],
        [-508.3550, -175.4000], [-509.6840, -171.9510], [-510.8390, -168.7600], [-511.8970, -165.5520], [-513.2570, -161.1880],
        [-513.9090, -158.8200], [-515.7100, -151.6170], [-516.1950, -149.4820], [-516.5510, -147.6080], [-517.6470, -140.2510],
        [-518.3990, -135.4880], [-518.6020, -133.8670], [-270.9530, -334.1000], [-271.2020, -333.7970], [-271.3870, -333.4510],
        [-271.5010, -333.0760], [-271.5390, -332.6860], [-271.5390, -300.9460], [-271.5010, -300.5550], [-271.3870, -300.1800],
        [-271.2020, -299.8340], [-270.9530, -299.5310], [-270.4820, -299.1820], [-270.1200, -299.0320], [-269.7350, -298.9550],
        [-263.5390, -298.9460], [-262.5500, -298.8960], [-257.6700, -298.8660], [22.0110, -298.8660], [22.4010, -298.9040],
        [22.7760, -299.0180], [23.1220, -299.2030], [23.4250, -299.4510], [23.6740, -299.7540], [23.8590, -300.1000],
        [24.0010, -300.6700], [24.0010, -332.9570], [23.8590, -333.5260], [23.6740, -333.8720], [23.4250, -334.1750],
        [22.9540, -334.5250], [22.5920, -334.6750], [22.2070, -334.7510], [-255.9210, -334.7610], [-262.5500, -334.7300],
        [-263.5390, -334.6860], [-269.5390, -334.6860], [-269.9290, -334.6470], [-270.3040, -334.5330], [-270.6500, -334.3490],
        [-461.4360, -271.6550], [-457.4890, -274.0640], [-453.5300, -276.2930], [-447.3530, -279.5380], [-443.8270, -281.3210],
        [-440.5130, -282.8640], [-435.7490, -284.8900], [-430.1570, -287.0850], [-426.7790, -288.3130], [-421.9080, -289.9320],
        [-415.2160, -291.9470], [-412.2790, -292.7780], [-410.1800, -293.2960], [-401.6700, -295.2420], [-399.8080, -295.6000],
        [-397.5940, -295.9550], [-391.4720, -296.7670], [-386.0540, -297.5960], [-383.7720, -297.8580], [-381.7640, -298.0040],
        [-377.0100, -298.2520], [-369.9470, -298.7730], [-366.8470, -298.8760], [-363.0940, -298.8980], [-362.7090, -298.9740],
        [-362.1790, -299.2250], [-361.7440, -299.6190], [-361.5260, -299.9450], [-361.3280, -300.4980], [-361.2900, -300.8880],
        [-361.2900, -332.7570], [-361.3760, -333.3370], [-361.6270, -333.8680], [-362.0210, -334.3030], [-362.3470, -334.5210],
        [-362.7090, -334.6710], [-363.2900, -334.7570], [-376.2410, -334.7390], [-379.0010, -334.6720], [-381.3710, -334.5360],
        [-384.9970, -334.1620], [-393.3780, -333.0180], [-400.2150, -332.2160], [-402.7760, -331.8480], [-404.6520, -331.5050],
        [-409.5720, -330.4720], [-414.5580, -329.5110], [-416.4010, -329.1040], [-418.5090, -328.5710], [-425.9280, -326.5430],
        [-432.3490, -324.6140], [-435.5200, -323.5920], [-440.3570, -321.8810], [-444.0750, -320.4700], [-449.7950, -318.1940],
        [-454.3010, -316.2700], [-457.8930, -314.6320], [-461.1500, -313.0340], [-468.4630, -309.2770], [-471.7230, -307.5050],
        [-476.5640, -304.7670], [-479.7540, -302.8530], [-483.5290, -300.4310], [-487.5980, -297.7170], [-492.1870, -294.5550],
        [-494.5620, -292.8310], [-497.4090, -290.6670], [-502.8110, -286.4500], [-505.3650, -284.3650], [-510.9640, -279.4680],
        [-512.7800, -277.8270], [-521.2950, -269.5370], [-523.4700, -267.3230], [-525.7470, -264.8790], [-528.2670, -262.0410],
        [-530.7010, -259.1800], [-534.1670, -254.9000], [-539.5780, -247.9540], [-541.7500, -245.1150], [-543.4560, -242.7650],
        [-545.7830, -239.2940], [-550.6150, -231.6770], [-552.4420, -228.7270], [-554.1840, -225.7570], [-555.9870, -222.5060],
        [-558.1340, -218.4490], [-560.4820, -213.8200], [-562.4800, -209.7310], [-563.9820, -206.4750], [-565.5310, -202.9360],
        [-566.7870, -199.8590], [-567.9900, -196.7170], [-571.2470, -187.6290], [-572.5870, -183.6150], [-573.4850, -180.6970],
        [-575.9790, -171.4940], [-578.1480, -162.4290], [-578.7110, -159.6460], [-579.6910, -152.9300], [-580.7380, -146.5910],
        [-581.0850, -144.0000], [-581.3120, -141.6850], [-581.9440, -134.0070], [-582.0690, -131.6310], [-582.1340, -128.8700],
        [-582.1520, -94.9400], [-582.1250, -91.4560], [-582.0510, -89.0500], [-581.9430, -87.3640], [-581.8100, -86.0430],
        [-581.6310, -84.7480], [-581.4040, -83.4820], [-581.1290, -82.2410], [-580.7250, -80.7190], [-580.2610, -79.2190],
        [-579.7450, -77.7330], [-578.6820, -75.0880], [-577.5660, -72.7920], [-576.9430, -71.6690], [-576.1070, -70.2880],
        [-575.3960, -69.2040], [-574.4580, -67.8760], [-572.6340, -65.5630], [-571.5440, -64.3200], [-570.6320, -63.3530],
        [-568.7060, -61.5100], [-567.6960, -60.6440], [-566.3980, -59.6160], [-563.9810, -57.9020], [-562.6080, -57.0230],
        [-561.2220, -56.2030], [-560.1070, -55.5960], [-558.7100, -54.9030], [-557.3090, -54.2790], [-555.9000, -53.7150],
        [-554.4750, -53.2090], [-553.3120, -52.8460], [-552.1240, -52.5270], [-550.9040, -52.2530], [-549.6520, -52.0280],
        [-548.3680, -51.8520], [-547.0530, -51.7220], [-545.3720, -51.6160], [-542.2750, -51.5350], [-94.6970, -51.5080],
        [-91.9150, -51.5380], [-89.8550, -51.6050], [-87.8370, -51.7430], [-86.2000, -51.9300], [-84.6110, -52.1920],
        [-82.7720, -52.6070], [-81.2900, -53.0300], [-79.5600, -53.6160], [-77.0080, -54.6280], [-74.7470, -55.6780],
        [-72.5080, -56.9070], [-70.3250, -58.3030], [-67.6960, -60.2080], [-65.4370, -62.0470], [-64.4800, -62.9120],
        [-63.5580, -63.8140], [-61.8270, -65.7160], [-60.8140, -66.9590], [-59.8420, -68.2330], [-58.0170, -70.8500],
        [-56.5330, -73.2780], [-55.2350, -75.7600], [-54.5990, -77.1540], [-54.0170, -78.5560], [-53.4860, -79.9700],
        [-53.0080, -81.4070], [-52.6700, -82.5840], [-52.3760, -83.7890], [-52.1300, -85.0270], [-51.9330, -86.2980],
        [-51.7540, -87.9300], [-51.6240, -89.9460], [-51.5560, -92.3510], [-51.5320, -95.8350], [-51.5290, -269.5520],
        [-51.5680, -269.9420], [-51.6820, -270.3170], [-51.8670, -270.6630], [-52.1150, -270.9660], [-52.4180, -271.2150],
        [-52.7640, -271.4000], [-53.1390, -271.5130], [-53.5290, -271.5520], [-85.3970, -271.5520], [-85.7870, -271.5130],
        [-86.1620, -271.4000], [-86.6660, -271.0980], [-86.9430, -270.8210], [-87.1610, -270.4950], [-87.3580, -269.9420],
        [-87.3970, -269.5520], [-87.4110, -88.9850], [-88.9750, -87.4000], [-544.6950, -87.4000], [-546.2590, -88.9850],
        [-546.2580, -112.7890], [-546.2240, -117.6710], [-546.0800, -121.4390], [-545.6010, -128.1660], [-545.4220, -135.0610],
        [-545.2910, -137.7780], [-545.0500, -140.4240], [-544.6140, -143.6470], [-542.4100, -156.2290], [-542.0200, -158.0720],
        [-541.5810, -159.8850], [-539.0570, -169.4680], [-537.5760, -174.4350], [-536.4250, -177.9050], [-534.4910, -183.1370],
        [-532.5490, -187.9720], [-530.8580, -191.8810], [-528.9360, -196.0030], [-525.9700, -201.9920], [-523.8430, -206.0560],
        [-521.5350, -210.1670], [-519.5330, -213.5060], [-517.7550, -216.2550], [-513.5610, -222.4990], [-511.4420, -225.4090],
        [-507.2490, -230.8180], [-504.8560, -233.8070], [-502.5070, -236.5950], [-499.9660, -239.4540], [-497.4120, -242.1350],
        [-488.6550, -250.7480], [-486.9480, -252.3830], [-484.4820, -254.5930], [-479.9620, -258.4620], [-477.1490, -260.7540],
        [-474.3050, -262.9450], [-470.6710, -265.5620], [-466.4920, -268.4070], [-300.3870, 271.4530], [-299.8570, 271.2020],
        [-299.4220, 270.8080], [-299.1200, 270.3040], [-298.9780, 269.7350], [-298.9680, 263.5390], [-298.9180, 262.5300],
        [-298.8870, 257.6510], [-298.8970, -22.2070], [-298.9730, -22.5920], [-299.1230, -22.9540], [-299.4730, -23.4250],
        [-299.9440, -23.7750], [-300.3060, -23.9250], [-300.6910, -24.0010], [-332.9790, -24.0010], [-333.3640, -23.9250],
        [-333.7260, -23.7750], [-334.0520, -23.5570], [-334.3290, -23.2800], [-334.5470, -22.9540], [-334.6970, -22.5920],
        [-334.7830, -22.0110], [-334.7830, 255.9010], [-334.7530, 262.5300], [-334.7070, 263.5390], [-334.6980, 269.7350],
        [-334.6210, 270.1200], [-334.4710, 270.4820], [-334.1220, 270.9530], [-333.8190, 271.2020], [-333.4730, 271.3870],
        [-333.0980, 271.5010], [-332.7070, 271.5390], [-300.9680, 271.5390], [-479.1390, 259.1680], [-485.2770, 253.9160],
        [-488.2100, 251.2260], [-496.8210, 242.7790], [-499.3960, 240.0730], [-502.1810, 236.9720], [-505.0240, 233.6460],
        [-507.8760, 230.1410], [-510.4810, 226.8000], [-512.7970, 223.6510], [-514.8260, 220.6910], [-519.3920, 213.7900],
        [-521.2940, 210.6540], [-523.3760, 206.9740], [-525.5040, 202.9620], [-528.4900, 196.9850], [-530.4340, 192.8800],
        [-532.1470, 188.9920], [-534.2170, 183.9010], [-536.1740, 178.6730], [-537.3630, 175.2080], [-538.9970, 169.9880],
        [-539.7370, 167.3310], [-541.6160, 159.8400], [-542.3750, 156.5050], [-544.5310, 144.2540], [-544.9080, 141.6940],
        [-545.2000, 139.0800], [-545.4120, 135.7160], [-545.6120, 128.1370], [-546.0890, 121.4110], [-546.2250, 117.9900],
        [-546.2630, 113.1120], [-546.2560, 88.9610], [-544.6700, 87.3970], [-363.3500, 87.3820], [-362.9600, 87.3440],
        [-362.4070, 87.1460], [-362.0810, 86.9290], [-361.8040, 86.6510], [-361.5020, 86.1480], [-361.3880, 85.7730],
        [-361.3500, 85.3820], [-361.3500, 53.5590], [-361.3880, 53.1680], [-361.5020, 52.7930], [-361.8040, 52.2900],
        [-362.0810, 52.0130], [-362.4070, 51.7950], [-362.9600, 51.5970], [-363.3500, 51.5590], [-538.8150, 51.5070],
        [-544.0350, 51.5580], [-545.7450, 51.6270], [-547.4230, 51.7480], [-549.6990, 52.0330], [-551.5730, 52.3950],
        [-553.6660, 52.9510], [-555.6810, 53.6330], [-557.9340, 54.5520], [-559.8910, 55.4900], [-561.8370, 56.5700],
        [-564.0290, 57.9560], [-566.1560, 59.4740], [-567.9540, 60.9050], [-569.6900, 62.4390], [-571.3470, 64.0800],
        [-572.8950, 65.8210], [-574.3200, 67.6420], [-575.6260, 69.5240], [-576.9730, 71.7180], [-578.0120, 73.6560],
        [-578.9160, 75.6090], [-579.8080, 77.8660], [-580.5780, 80.1730], [-581.1440, 82.2620], [-581.5290, 84.1220],
        [-581.8120, 86.0490], [-582.0150, 88.3780], [-582.1190, 91.1170], [-582.1520, 94.5980], [-582.1290, 129.2350],
        [-582.0680, 131.6490], [-581.9420, 134.0250], [-581.2810, 142.0380], [-581.0450, 144.3480], [-580.7840, 146.2910],
        [-579.7370, 152.6350], [-578.9090, 158.4010], [-578.5940, 160.2970], [-578.0710, 162.7560], [-575.6670, 172.7150],
        [-573.4020, 180.9930], [-572.6840, 183.3170], [-571.4490, 187.0370], [-570.3630, 190.1550], [-567.7880, 197.2580],
        [-566.4620, 200.6770], [-565.0750, 204.0040], [-563.5040, 207.5310], [-561.9690, 210.7920], [-559.6730, 215.4260],
        [-557.5830, 219.5030], [-555.5580, 223.2940], [-553.7270, 226.5700], [-551.7850, 229.8920], [-550.0610, 232.6770],
        [-544.7320, 240.9010], [-543.4610, 242.7580], [-541.9480, 244.8500], [-539.7820, 247.6920], [-533.3570, 255.9200],
        [-530.2990, 259.6740], [-527.6640, 262.7590], [-525.5820, 265.0530], [-523.2400, 267.4910], [-513.7750, 276.9140],
        [-510.7730, 279.6700], [-506.2060, 283.6510], [-504.1680, 285.3630], [-501.8540, 287.2050], [-496.1840, 291.6080],
        [-493.8360, 293.3650], [-491.4430, 295.0780], [-486.3040, 298.5940], [-482.2070, 301.3020], [-478.6160, 303.5980],
        [-475.5830, 305.4030], [-470.6630, 308.1150], [-466.3090, 310.3980], [-459.5460, 313.8350], [-454.8780, 316.0160],
        [-449.2530, 318.4190], [-442.6690, 321.0150], [-436.9720, 323.0880], [-432.9770, 324.4150], [-425.7000, 326.6050],
        [-417.3770, 328.8660], [-414.6250, 329.4990], [-409.3170, 330.5270], [-404.6940, 331.4980], [-402.8170, 331.8420],
        [-400.9020, 332.1280], [-394.0640, 332.9290], [-385.0330, 334.1570], [-381.7420, 334.5060], [-380.0600, 334.6220],
        [-378.0080, 334.7050], [-372.0890, 334.7600], [-116.0390, 334.7610], [-115.6490, 334.7230], [-115.2740, 334.6090],
        [-114.7700, 334.3070], [-114.4930, 334.0300], [-114.2750, 333.7040], [-114.0780, 333.1510], [-114.0390, 332.7610],
        [-114.0390, 300.8880], [-114.1250, 300.3080], [-114.2750, 299.9450], [-114.4930, 299.6190], [-114.7700, 299.3420],
        [-115.0960, 299.1240], [-115.6490, 298.9270], [-116.0390, 298.8880], [-121.8400, 298.8880], [-123.4770, 298.8360],
        [-126.6130, 298.8150], [-366.6890, 298.8040], [-369.1070, 298.7500], [-371.1510, 298.6530], [-376.8550, 298.2250],
        [-381.9410, 297.9610], [-384.2700, 297.7840], [-386.2120, 297.5530], [-391.2920, 296.7710], [-396.7720, 296.0480],
        [-399.0050, 295.7130], [-400.8870, 295.3770], [-403.0430, 294.9240], [-410.6350, 293.1730], [-413.0230, 292.5660],
        [-421.4780, 290.0610], [-425.4970, 288.7440], [-428.6200, 287.6560], [-432.2510, 286.2760], [-436.1760, 284.7150],
        [-439.5440, 283.2910], [-442.3250, 282.0420], [-444.7910, 280.8520], [-447.7700, 279.3280], [-452.8850, 276.6440],
        [-456.0960, 274.8740], [-458.8010, 273.2870], [-462.0850, 271.2610], [-465.6110, 269.0030], [-468.5270, 267.0590],
        [-471.6490, 264.8910], [-474.2470, 263.0070], [-476.5760, 261.2270], [287.0750, -430.1530], [288.3040, -426.7740],
        [289.9250, -421.9020], [291.9400, -415.2080], [292.7720, -412.2700], [293.2900, -410.1710], [295.2380, -401.6580],
        [295.5950, -399.7950], [295.9510, -397.5810], [296.8090, -391.1370], [297.5930, -386.0380], [297.8580, -383.7560],
        [298.2740, -377.3550], [298.6500, -372.6630], [298.7740, -370.6280], [298.8730, -367.5260], [298.9000, -363.0940],
        [298.9760, -362.7090], [299.2270, -362.1790], [299.4760, -361.8760], [299.9480, -361.5260], [300.5000, -361.3280],
        [300.8900, -361.2900], [332.7440, -361.2900], [333.3240, -361.3760], [333.8550, -361.6270], [334.2900, -362.0210],
        [334.5070, -362.3470], [334.6570, -362.7090], [334.7440, -363.2900], [334.7340, -376.1100], [334.6710, -378.8730],
        [334.5410, -381.2460], [334.3610, -383.2390], [334.1310, -385.2010], [333.0270, -393.2590], [332.1850, -400.4230],
        [331.8080, -402.9790], [331.3960, -405.1600], [330.4260, -409.7700], [329.4690, -414.7380], [329.0580, -416.5690],
        [328.6010, -418.3690], [326.5720, -425.7850], [324.5600, -432.4860], [323.4400, -435.9340], [321.7170, -440.7720],
        [320.1850, -444.7770], [318.4710, -449.0490], [315.7070, -455.3790], [314.2390, -458.6300], [312.7890, -461.6020],
        [309.3160, -468.3800], [307.2730, -472.1920], [305.2950, -475.7510], [303.4800, -478.7860], [300.9980, -482.6530],
        [298.2800, -486.7500], [294.9450, -491.6200], [292.6580, -494.7930], [289.5390, -498.9410], [287.1280, -502.0350],
        [285.0340, -504.5940], [278.6790, -511.8590], [275.8590, -514.8740], [265.5490, -525.1460], [263.3990, -527.1320],
        [260.7720, -529.3900], [257.3190, -532.2330], [254.0000, -534.8750], [246.5350, -540.6770], [243.1560, -543.1840],
        [239.9660, -545.3570], [232.5440, -550.1540], [229.7590, -551.8750], [226.4380, -553.8130], [222.8920, -555.7880],
        [218.8320, -557.9450], [213.9330, -560.4370], [209.8420, -562.4400], [207.1170, -563.6930], [203.8300, -565.1100],
        [198.7880, -567.1760], [195.6570, -568.3870], [187.4470, -571.3350], [183.1560, -572.7620], [180.2420, -573.6460],
        [173.4410, -575.5030], [171.0490, -576.1180], [162.2270, -578.1650], [159.4370, -578.7210], [152.7470, -579.7550],
        [146.7360, -580.7590], [144.1600, -581.1090], [141.8540, -581.3390], [134.1760, -581.9780], [131.8010, -582.1100],
        [129.0410, -582.1800], [95.1060, -582.1990], [91.2740, -582.1710], [88.8730, -582.0970], [87.1940, -581.9880],
        [85.8810, -581.8550], [84.5970, -581.6770], [83.3440, -581.4520], [82.1200, -581.1820], [80.6290, -580.7870],
        [79.1730, -580.3360], [77.7430, -579.8390], [75.2100, -578.8230], [73.8190, -578.1760], [72.7120, -577.6090],
        [71.6110, -576.9970], [70.2460, -576.1720], [67.8430, -574.5320], [65.5300, -572.7120], [64.2870, -571.6230],
        [63.3200, -570.7130], [61.4840, -568.7970], [60.6270, -567.8000], [59.6190, -566.5290], [58.6780, -565.2390],
        [57.8000, -563.9380], [56.9790, -562.6260], [56.2130, -561.3040], [55.5010, -559.9690], [54.8390, -558.6200],
        [54.1080, -556.9810], [53.5520, -555.5910], [53.0490, -554.1680], [52.6930, -552.9990], [52.3820, -551.7970],
        [52.1200, -550.5610], [51.9080, -549.2910], [51.7450, -547.9900], [51.5480, -545.3080], [51.4690, -542.2060],
        [51.4180, -95.0640], [51.4520, -91.9350], [51.5240, -89.8780], [51.6700, -87.8650], [51.8650, -86.2340],
        [52.1350, -84.6520], [52.5590, -82.8220], [52.9880, -81.3500], [53.5820, -79.6300], [54.1340, -78.2200],
        [54.7360, -76.8210], [55.9650, -74.3270], [57.3880, -71.8790], [58.9750, -69.4980], [60.6970, -67.2000],
        [61.7130, -65.9710], [62.5630, -65.0200], [64.3730, -63.2100], [66.3180, -61.5090], [68.8780, -59.4970],
        [71.2810, -57.8210], [73.4910, -56.4970], [75.7420, -55.3600], [78.5650, -54.1670], [79.9850, -53.6450],
        [81.4270, -53.1740], [82.9050, -52.7650], [84.1220, -52.4880], [85.3720, -52.2590], [86.6540, -52.0780],
        [88.2990, -51.9170], [90.3270, -51.8030], [95.8780, -51.7230], [259.6500, -51.5200], [263.5520, -51.5720],
        [269.5520, -51.5720], [269.9420, -51.6100], [270.3170, -51.7240], [270.6630, -51.9090], [270.9660, -52.1580],
        [271.2150, -52.4610], [271.4000, -52.8070], [271.5130, -53.1820], [271.5520, -53.5720], [271.5520, -85.3820],
        [271.5130, -85.7730], [271.4000, -86.1480], [271.0980, -86.6510], [270.8210, -86.9290], [270.4950, -87.1460],
        [269.9420, -87.3440], [269.5520, -87.3820], [88.9770, -87.3970], [87.3920, -88.9610], [87.3920, -544.6660],
        [88.9770, -546.2300], [112.7910, -546.2280], [117.6740, -546.1950], [121.4430, -546.0490], [128.1730, -545.5710],
        [135.0710, -545.3920], [137.7880, -545.2600], [140.4350, -545.0180], [143.6590, -544.5820], [155.2880, -542.5160],
        [157.1380, -542.1320], [159.2640, -541.6350], [166.5080, -539.8220], [169.4880, -539.0210], [174.4720, -537.5330],
        [178.2440, -536.2740], [183.7700, -534.2160], [188.8700, -532.1430], [192.7660, -530.4260], [197.1460, -528.3440],
        [201.4780, -526.1420], [207.7330, -522.8410], [211.0690, -520.9680], [213.8560, -519.2800], [216.8730, -517.3130],
        [222.8420, -513.2910], [225.7420, -511.1570], [231.1460, -506.9600], [233.8760, -504.7650], [236.4320, -502.6120],
        [239.0410, -500.2960], [241.3460, -498.1040], [250.1320, -489.2940], [252.0290, -487.3360], [254.2960, -484.8190],
        [258.4260, -479.9790], [260.7220, -477.1590], [262.9150, -474.3130], [265.5350, -470.6780], [268.3820, -466.4980],
        [271.6320, -461.4410], [274.0430, -457.4920], [276.2740, -453.5330], [279.5210, -447.3540], [281.3060, -443.8270],
        [282.8500, -440.5120], [284.8770, -435.7470], [361.9360, -86.7960], [361.6870, -86.4930], [361.5020, -86.1480],
        [361.3880, -85.7720], [361.3500, -85.3820], [361.3500, -54.0490], [361.3880, -53.6590], [361.5020, -53.2840],
        [361.6870, -52.9380], [361.9360, -52.6350], [362.4070, -52.2860], [362.7690, -52.1360], [363.1540, -52.0590],
        [365.6800, -52.0490], [366.3730, -51.9240], [367.7000, -51.7530], [369.0550, -51.6450], [372.8630, -51.5400],
        [541.1930, -51.7190], [543.9690, -51.7630], [546.3560, -51.8710], [548.3490, -52.0520], [550.2750, -52.3360],
        [552.1280, -52.7270], [553.9100, -53.2220], [555.9210, -53.9140], [557.8930, -54.7170], [560.1300, -55.7880],
        [562.3480, -57.0430], [564.5260, -58.4570], [566.8930, -60.2010], [568.9160, -61.8860], [570.6140, -63.4750],
        [572.2180, -65.1680], [573.9060, -67.2120], [575.4330, -69.3430], [576.8060, -71.5270], [578.0100, -73.7370],
        [579.0390, -75.9650], [580.0230, -78.5080], [580.8550, -81.1230], [581.4430, -83.5500], [581.6720, -84.8080],
        [581.8540, -86.0970], [581.9910, -87.4140], [582.1040, -89.0960], [582.2040, -93.2360], [582.1950, -128.5610],
        [582.1410, -131.3290], [582.0300, -133.7150], [581.3190, -142.4030], [581.0770, -144.7090], [580.8110, -146.6480],
        [579.7130, -153.3060], [578.8850, -159.0690], [578.4910, -161.2630], [576.0420, -171.8950], [573.2190, -181.9300],
        [572.2010, -185.1010], [570.7470, -189.3700], [568.1910, -196.4560], [566.7740, -200.1690], [565.3980, -203.5160],
        [563.8390, -207.0470], [562.3230, -210.3040], [560.4490, -214.1170], [558.0990, -218.7410], [555.8020, -223.0730],
        [553.8280, -226.6170], [551.7210, -230.2170], [549.8090, -233.2800], [544.8320, -240.9540], [543.0040, -243.5990],
        [541.0790, -246.1980], [535.0830, -253.9200], [532.8320, -256.7460], [530.5060, -259.5320], [526.1620, -264.5500],
        [524.5600, -266.2990], [522.5200, -268.3980], [514.6920, -276.1810], [512.9750, -277.8360], [510.4570, -280.1040],
        [504.8720, -284.9350], [502.3040, -287.0000], [496.6360, -291.4070], [493.7690, -293.5570], [490.8370, -295.6400],
        [486.0090, -298.9200], [482.5810, -301.1450], [479.3970, -303.0860], [472.4030, -307.2030], [470.2330, -308.4410],
        [466.4260, -310.4610], [459.3980, -314.0070], [456.9610, -315.1340], [452.3210, -317.1830], [447.8410, -319.0910],
        [441.2600, -321.6570], [434.9940, -323.8730], [432.4010, -324.6990], [426.2860, -326.5390], [418.5590, -328.6280],
        [415.5160, -329.3430], [409.9140, -330.4630], [404.9970, -331.5250], [402.8110, -331.9320], [400.8960, -332.2180],
        [394.3820, -332.9760], [385.6760, -334.1590], [382.0670, -334.5610], [380.0520, -334.7030], [378.0000, -334.7850],
        [372.0800, -334.8380], [116.0390, -334.7630], [115.6490, -334.7240], [115.2740, -334.6100], [114.9280, -334.4260],
        [114.6250, -334.1770], [114.3760, -333.8740], [114.1920, -333.5280], [114.0780, -333.1530], [114.0390, -332.7630],
        [114.0390, -300.8710], [114.1250, -300.2910], [114.2750, -299.9290], [114.4930, -299.6030], [114.7700, -299.3250],
        [115.0960, -299.1080], [115.6490, -298.9100], [116.0390, -298.8710], [121.8400, -298.8710], [123.8740, -298.8190],
        [127.0110, -298.8020], [364.8380, -298.7760], [367.9630, -298.7360], [370.3610, -298.6480], [376.7380, -298.1810],
        [383.4900, -297.7990], [386.0890, -297.5080], [391.1650, -296.7250], [397.6020, -295.8640], [400.1310, -295.4480],
        [402.6030, -294.9460], [410.4960, -293.1250], [413.1760, -292.4370], [421.0430, -290.1040], [427.0570, -288.1120],
        [431.2620, -286.5510], [436.0420, -284.6220], [442.4030, -281.8230], [446.0530, -280.0740], [452.5850, -276.6630],
        [456.7340, -274.3430], [458.3980, -273.3250], [460.0400, -272.2360], [461.3800, -271.2700], [462.9530, -270.0510],
        [464.6800, -269.1900], [466.3550, -268.2560], [468.2420, -267.0820], [470.3400, -265.6690], [472.9410, -263.8300],
        [475.2770, -262.0930], [477.8550, -260.0740], [480.4000, -257.9760], [485.9460, -253.1970], [488.7670, -250.5880],
        [498.7590, -240.5970], [500.3600, -238.9220], [501.8630, -237.2540], [503.8980, -234.8650], [505.9030, -232.4090],
        [511.8900, -224.7080], [514.1670, -221.5130], [518.9560, -214.3240], [520.2620, -212.2360], [521.5000, -210.1440],
        [524.2890, -205.1300], [525.6880, -202.4400], [527.5960, -198.6380], [530.3470, -192.9030], [531.5850, -190.1340],
        [532.8830, -187.0550], [534.1380, -183.9310], [535.3530, -180.7390], [537.1000, -175.8190], [539.3800, -168.5700],
        [540.3300, -164.9870], [541.6620, -159.5450], [542.2080, -157.1060], [542.6800, -154.6170], [544.6410, -143.2810],
        [545.0270, -140.3770], [545.2900, -137.3960], [545.3880, -135.3590], [545.5800, -128.8250], [546.0390, -122.4400],
        [546.1680, -119.7150], [546.2320, -114.5030], [546.2330, -88.9610], [544.6480, -87.3970], [363.3500, -87.3820],
        [362.9600, -87.3440], [362.5850, -87.2300], [362.2390, -87.0450], [300.0990, 23.8590], [300.4740, 23.9730],
        [300.8640, 24.0110], [332.7600, 24.0110], [333.1510, 23.9730], [333.5260, 23.8590], [333.8720, 23.6740],
        [334.1750, 23.4250], [334.5240, 22.9540], [334.6740, 22.5920], [334.7510, 22.2070], [334.7600, -255.9010],
        [334.7300, -262.5300], [334.6850, -263.5390], [334.6850, -269.5390], [334.6460, -269.9290], [334.4480, -270.4820],
        [334.0990, -270.9530], [333.7960, -271.2020], [333.4500, -271.3870], [332.8810, -271.5290], [300.7490, -271.5290],
        [300.3650, -271.4530], [300.0020, -271.3030], [299.5310, -270.9530], [299.1810, -270.4820], [299.0310, -270.1200],
        [298.9550, -269.7350], [298.9450, -263.5390], [298.8950, -262.5300], [298.8650, -257.6500], [298.8640, 22.0110],
        [298.9500, 22.5920], [299.2010, 23.1220], [299.5950, 23.5570], [466.6620, 268.2810], [461.8700, 271.3670],
        [457.6580, 273.9530], [453.7020, 276.1900], [447.7840, 279.3030], [443.9830, 281.2330], [440.6730, 282.7810],
        [435.9090, 284.8180], [430.3110, 287.0200], [426.6500, 288.3490], [421.7780, 289.9650], [414.7930, 292.0640],
        [412.1460, 292.8050], [410.0450, 293.3200], [401.5350, 295.2670], [399.6700, 295.6220], [397.4520, 295.9750],
        [391.3230, 296.7850], [385.9060, 297.6150], [383.6210, 297.8730], [377.5560, 298.2590], [370.8340, 298.7460],
        [367.7370, 298.8390], [363.0940, 298.8590], [362.7090, 298.9350], [362.1790, 299.1860], [361.8760, 299.4350],
        [361.5260, 299.9070], [361.3280, 300.4590], [361.2900, 300.8490], [361.2900, 332.7410], [361.3760, 333.3210],
        [361.6270, 333.8520], [362.0210, 334.2870], [362.3470, 334.5050], [362.7090, 334.6550], [363.2900, 334.7410],
        [376.1300, 334.7180], [378.8960, 334.6510], [381.2720, 334.5160], [384.9060, 334.1400], [393.6250, 332.9400],
        [400.1500, 332.1690], [402.7160, 331.7960], [404.9040, 331.3850], [409.8150, 330.3140], [415.4150, 329.1860],
        [417.2530, 328.7670], [419.3610, 328.2300], [425.9040, 326.4430], [432.3220, 324.5020], [435.4900, 323.4750],
        [440.0480, 321.8570], [444.0580, 320.3340], [449.7780, 318.0460], [454.2840, 316.1120], [458.1530, 314.3330],
        [461.4120, 312.7170], [466.8220, 309.9120], [469.4980, 308.3860], [472.1060, 306.6720], [475.1430, 305.2350],
        [477.8220, 303.7830], [480.4390, 302.1890], [484.3490, 299.6560], [488.8610, 296.6170], [492.3550, 294.1940],
        [494.7260, 292.4630], [497.3180, 290.4900], [502.7250, 286.2710], [505.0240, 284.3970], [512.2260, 278.1000],
        [514.1920, 276.2770], [516.6050, 273.9350], [519.6060, 270.9150], [525.5170, 264.7940], [527.6850, 262.4300],
        [529.9370, 259.8110], [532.5890, 256.5810], [535.2230, 253.2530], [540.6190, 246.3050], [543.1200, 242.9260],
        [545.1110, 240.0020], [549.9090, 232.5850], [551.6350, 229.7990], [553.5790, 226.4760], [555.5590, 222.9340],
        [557.7140, 218.8840], [560.2000, 213.9980], [562.3360, 209.6410], [563.9620, 206.1140], [565.5090, 202.5710],
        [567.0080, 198.9120], [568.3630, 195.4200], [570.1570, 190.3920], [572.1100, 184.5980], [573.2260, 181.1350],
        [574.1750, 177.9120], [575.3420, 173.7830], [575.9590, 171.3890], [577.1060, 166.2000], [578.1120, 161.9640],
        [578.5470, 159.7970], [579.5830, 152.7610], [580.6320, 146.4320], [580.9740, 143.8520], [581.1980, 141.5430],
        [581.8320, 133.8630], [581.9570, 131.4850], [582.0220, 128.7230], [582.0430, 94.7970], [582.0160, 91.3140],
        [581.9420, 88.9090], [581.8320, 87.2240], [581.6990, 85.9040], [581.5180, 84.6100], [581.2900, 83.3450],
        [581.0150, 82.1040], [580.6090, 80.5830], [580.1440, 79.0840], [579.6270, 77.5990], [578.5630, 74.9550],
        [577.4450, 72.6600], [576.8210, 71.5370], [575.9840, 70.1580], [574.3330, 67.7470], [572.5080, 65.4350],
        [571.4180, 64.1930], [570.5050, 63.2260], [568.5770, 61.3850], [567.5670, 60.5200], [566.2680, 59.4930],
        [563.8510, 57.7820], [562.4780, 56.9040], [561.0920, 56.0860], [559.9770, 55.4810], [558.5800, 54.7890],
        [557.1780, 54.1660], [555.7680, 53.6040], [554.3390, 53.0990], [553.1730, 52.7370], [551.9780, 52.4180],
        [550.7520, 52.1440], [549.4930, 51.9190], [548.2010, 51.7410], [546.8800, 51.6110], [545.1940, 51.5040],
        [542.0920, 51.4220], [94.9140, 51.4720], [90.0650, 51.5580], [88.0410, 51.6850], [86.3980, 51.8620],
        [84.8010, 52.1130], [82.9530, 52.5160], [81.4650, 52.9300], [79.7320, 53.5100], [77.1910, 54.5210],
        [74.6850, 55.7070], [72.4930, 56.9270], [70.0850, 58.4750], [68.7800, 59.4070], [67.5010, 60.3830],
        [65.2890, 62.2360], [63.4480, 63.9940], [62.5740, 64.9180], [61.5190, 66.1170], [60.5010, 67.3580],
        [59.5200, 68.6340], [57.8660, 71.0000], [56.3850, 73.4350], [55.1000, 75.9220], [54.4710, 77.3170],
        [53.8960, 78.7200], [52.9920, 81.2890], [52.5730, 82.7610], [52.2880, 83.9730], [52.0510, 85.2170],
        [51.8620, 86.4930], [51.6920, 88.1320], [51.5720, 90.1540], [51.5100, 92.5640], [51.4890, 95.7000],
        [51.4920, 269.5520], [51.5300, 269.9420], [51.6440, 270.3170], [51.8290, 270.6630], [52.0780, 270.9660],
        [52.3810, 271.2150], [52.7260, 271.4000], [53.1020, 271.5130], [53.4920, 271.5520], [85.3740, 271.5520],
        [85.9550, 271.4660], [86.3170, 271.3160], [86.6430, 271.0980], [86.9200, 270.8210], [87.1380, 270.4950],
        [87.3360, 269.9420], [87.3740, 269.5520], [87.3880, 88.9860], [88.9520, 87.4000], [544.6720, 87.4000],
        [546.2360, 88.9860], [546.2350, 113.8370], [546.1960, 118.7160], [546.0610, 122.1390], [545.5800, 128.8640],
        [545.3890, 135.4000], [545.2910, 137.4370], [545.0280, 140.4170], [544.5960, 143.6320], [542.4610, 155.8740],
        [541.6710, 159.5490], [540.1900, 165.5960], [539.5590, 167.9880], [538.0440, 172.9400], [536.5230, 177.5620],
        [534.7110, 182.5010], [532.8980, 187.0740], [530.9950, 191.5470], [528.6450, 196.7170], [526.9270, 200.1770],
        [524.1200, 205.5240], [521.9050, 209.5060], [519.6690, 213.2680], [516.9230, 217.5650], [514.1280, 221.7510],
        [511.8950, 224.8540], [508.9510, 228.7130], [505.9090, 232.5130], [502.7270, 236.3110], [500.4070, 238.9300],
        [498.0160, 241.4450], [489.1920, 250.2410], [487.2330, 252.1340], [484.7140, 254.3950], [480.1300, 258.3060],
        [477.3130, 260.6070], [474.4710, 262.8060], [470.8370, 265.4320], [269.7350, 298.9520], [263.5390, 298.9420],
        [262.5280, 298.8970], [255.8980, 298.8660], [-22.2070, 298.8760], [-22.5920, 298.9520], [-22.9540, 299.1020],
        [-23.4250, 299.4520], [-23.7750, 299.9230], [-23.9250, 300.2850], [-24.0010, 300.6700], [-24.0010, 332.9570],
        [-23.9250, 333.3420], [-23.7750, 333.7040], [-23.5570, 334.0300], [-23.2800, 334.3070], [-22.9540, 334.5250],
        [-22.5920, 334.6750], [-22.0110, 334.7610], [257.6480, 334.7600], [262.5280, 334.7300], [263.5390, 334.6800],
        [269.7350, 334.6700], [270.1200, 334.5940], [270.4820, 334.4440], [270.9530, 334.0940], [271.3030, 333.6230],
        [271.4530, 333.2600], [271.5290, 332.8760], [271.5390, 300.9420], [271.4530, 300.3610], [271.3030, 299.9990],
        [271.0850, 299.6730], [270.8080, 299.3960], [270.4820, 299.1780], [270.1200, 299.0280], [333.8200, 114.4930],
        [333.4940, 114.2750], [333.1310, 114.1250], [332.5510, 114.0390], [300.8870, 114.0390], [300.3070, 114.1250],
        [299.7760, 114.3760], [299.3410, 114.7700], [299.1240, 115.0960], [298.9730, 115.4590], [298.8870, 116.0390],
        [298.8870, 121.8400], [298.8370, 123.4010], [298.8150, 126.5370], [298.7500, 367.3110], [298.6960, 369.7300],
        [298.5990, 371.7750], [298.1910, 377.1400], [297.9080, 381.8710], [297.7510, 383.8720], [297.4800, 386.1480],
        [296.6950, 391.2430], [296.0190, 396.4060], [295.6890, 398.6420], [295.3590, 400.5290], [294.9110, 402.6880],
        [293.1570, 410.2810], [292.5560, 412.6730], [290.0560, 421.1330], [288.7420, 425.1550], [287.6590, 428.2810],
        [286.5000, 431.3570], [284.8390, 435.5570], [283.4230, 438.9250], [282.0550, 441.9880], [281.0040, 444.1840],
        [279.6290, 446.8980], [276.8100, 452.2870], [275.2010, 455.2280], [273.9460, 457.3720], [272.7530, 459.2530],
        [271.4490, 461.1180], [270.0490, 462.9490], [269.1870, 464.6780], [268.4120, 466.0780], [267.4190, 467.7090],
        [266.3750, 469.2970], [264.5670, 471.9040], [262.8650, 474.2440], [261.0910, 476.5680], [258.8800, 479.3480],
        [257.0780, 481.5260], [255.1030, 483.8180], [253.1350, 486.0280], [251.4980, 487.7760], [242.8610, 496.5910],
        [240.3970, 498.9530], [237.7510, 501.3560], [234.9270, 503.8080], [232.2440, 506.0210], [225.8500, 511.0230],
        [222.9980, 513.1720], [220.0750, 515.2100], [215.2290, 518.3810], [212.3260, 520.1980], [209.6970, 521.7340],
        [205.9730, 523.7580], [198.6830, 527.5440], [194.8700, 529.4150], [191.0100, 531.1890], [185.9950, 533.2990],
        [180.7090, 535.3620], [176.7470, 536.7820], [172.6870, 538.0660], [167.3770, 539.5880], [159.5730, 541.6180],
        [157.1430, 542.1840], [154.9700, 542.6070], [144.5850, 544.4270], [142.0320, 544.8140], [139.4290, 545.1190],
        [137.7670, 545.2570], [135.7360, 545.3650], [128.1530, 545.5690], [121.4230, 546.0480], [117.9990, 546.1860],
        [113.1190, 546.2260], [88.9520, 546.2270], [87.3880, 544.6410], [87.3740, 363.3500], [87.3350, 362.9600],
        [87.1380, 362.4070], [86.9200, 362.0810], [86.6430, 361.8040], [86.1390, 361.5020], [85.7640, 361.3880],
        [85.3740, 361.3500], [53.9560, 361.3500], [53.5660, 361.3880], [53.0130, 361.5860], [52.5420, 361.9360],
        [52.1920, 362.4070], [52.0420, 362.7690], [51.9650, 363.1540], [51.9560, 365.6800], [51.7390, 366.8190],
        [51.5850, 368.4550], [51.5130, 370.5040], [51.4880, 373.6380], [51.4650, 537.7300], [51.4890, 542.6140],
        [51.5720, 545.3640], [51.6840, 547.0470], [51.8610, 548.6890], [52.1140, 550.2830], [52.3710, 551.5200],
        [52.7620, 553.0170], [53.2220, 554.4650], [53.7440, 555.8730], [54.4410, 557.5310], [55.2130, 559.1750],
        [56.0690, 560.8160], [57.0130, 562.4530], [57.8690, 563.8070], [58.9710, 565.4040], [59.9510, 566.7040],
        [61.1990, 568.2270], [62.3000, 569.4620], [63.4570, 570.6590], [64.6670, 571.8040], [65.6690, 572.6780],
        [66.9590, 573.7140], [68.2860, 574.6880], [69.6410, 575.6050], [71.2980, 576.6290], [72.7040, 577.4140],
        [74.1330, 578.1330], [75.5840, 578.7840], [77.3490, 579.4860], [79.1310, 580.1130], [80.6300, 580.5780],
        [82.1510, 580.9840], [83.7050, 581.3220], [85.3000, 581.5850], [86.6080, 581.7420], [88.2780, 581.8760],
        [89.9820, 581.9540], [92.4030, 582.0010], [128.0830, 581.9900], [131.1990, 581.9300], [133.5840, 581.8140],
        [142.9270, 581.0350], [144.8870, 580.8140], [146.8110, 580.5390], [152.8240, 579.5380], [158.9140, 578.6580],
        [161.7230, 578.1320], [166.2650, 577.0550], [170.5330, 576.1010], [172.3350, 575.6490], [180.8980, 573.2400],
        [185.2320, 571.8620], [189.7790, 570.2990], [196.8600, 567.7050], [203.3370, 565.0860], [207.7210, 563.1910],
        [210.1730, 562.0490], [213.1700, 560.5820], [216.9840, 558.6620], [219.9630, 557.1060], [221.8420, 556.0730],
        [223.4340, 555.1360], [224.7440, 554.3070], [226.2950, 553.2560], [229.2040, 551.8410], [230.6320, 551.0570],
        [232.0430, 550.2220], [239.7640, 545.2690], [243.7570, 542.5550], [247.8270, 539.5550], [254.7150, 534.1110],
        [258.9850, 530.6590], [262.9280, 527.3160], [265.5630, 524.9410], [268.0380, 522.5590], [276.4260, 514.0260],
        [278.2840, 512.0730], [283.1210, 506.6110], [285.2950, 504.0840], [287.9860, 500.7530], [290.9530, 496.8830],
        [294.0400, 492.7000], [296.8480, 488.6650], [300.4990, 483.2260], [303.8600, 477.9820], [305.7950, 474.6790],
        [309.0750, 468.6910], [311.6370, 463.8310], [313.5180, 460.0310], [315.2560, 456.2240], [318.5050, 448.7800],
        [320.8870, 442.7840], [322.4710, 438.5020], [324.0400, 433.9470], [326.0810, 427.2720], [326.9230, 424.3320],
        [328.9250, 416.9090], [329.4780, 414.4700], [330.4380, 409.4920], [331.4720, 404.5640], [332.0130, 401.4160],
        [332.9040, 393.9370], [333.9640, 386.2070], [334.2870, 383.6040], [334.5540, 380.6130], [334.6920, 377.1960],
        [334.7250, 369.5200], [334.5510, 116.0390], [334.4650, 115.4590], [334.3150, 115.0960], [334.0970, 114.7700],
        [-254.0840, -485.0930], [-252.4830, -486.8990], [-251.0770, -488.4050], [-249.0260, -490.4950], [-240.9150, -498.5770],
        [-239.2400, -500.1890], [-237.5700, -501.7040], [-234.9430, -503.9460], [-231.9840, -506.3500], [-226.0860, -510.9450],
        [-223.4640, -512.8980], [-221.0460, -514.5720], [-214.3960, -518.9920], [-211.7830, -520.6090], [-208.8910, -522.2670],
        [-204.8890, -524.4070], [-197.8760, -528.0250], [-193.7770, -529.9980], [-189.8960, -531.7390], [-184.5380, -533.9460],
        [-179.3170, -535.9190], [-175.5610, -537.2230], [-170.3440, -538.8640], [-166.7920, -539.8470], [-159.2580, -541.7340],
        [-156.5130, -542.3470], [-144.2590, -544.5040], [-141.6990, -544.8800], [-139.0860, -545.1720], [-135.7220, -545.3830],
        [-128.1440, -545.5830], [-121.4200, -546.0600], [-117.9990, -546.1960], [-113.1220, -546.2340], [-88.9750, -546.2260],
        [-87.4110, -544.6410], [-87.3970, -363.3500], [-87.3580, -362.9600], [-87.1600, -362.4070], [-86.9430, -362.0810],
        [-86.6650, -361.8040], [-86.1620, -361.5020], [-85.7870, -361.3880], [-85.3970, -361.3500], [-53.9980, -361.3500],
        [-53.6080, -361.3880], [-53.2330, -361.5020], [-52.7300, -361.8040], [-52.4520, -362.0810], [-52.2340, -362.4070],
        [-52.0370, -362.9600], [-51.9980, -363.3500], [-51.9980, -365.6800], [-51.8720, -366.2150], [-51.7310, -367.1560],
        [-51.5860, -369.1500], [-51.5280, -372.6100], [-51.5520, -538.8850], [-51.6080, -544.1040], [-51.6790, -545.8130],
        [-51.8050, -547.4890], [-52.0960, -549.7620], [-52.4660, -551.6300], [-53.0340, -553.7120], [-53.7330, -555.7060],
        [-54.6640, -557.9180], [-55.7320, -560.1090], [-56.9530, -562.2960], [-58.3330, -564.4590], [-59.8590, -566.5640],
        [-61.3090, -568.3460], [-62.8680, -570.0650], [-64.5330, -571.6990], [-66.2950, -573.2200], [-68.1340, -574.6180],
        [-70.0320, -575.9010], [-71.9760, -577.0710], [-73.9640, -578.1150], [-75.9970, -579.0280], [-78.0620, -579.8240],
        [-80.4460, -580.6100], [-82.5690, -581.1750], [-84.4400, -581.5510], [-86.3720, -581.8190], [-88.3660, -581.9850],
        [-91.1000, -582.0880], [-94.5800, -582.1220], [-129.2240, -582.1120], [-131.6410, -582.0540], [-134.0210, -581.9310],
        [-142.0430, -581.2720], [-144.3550, -581.0370], [-146.2990, -580.7780], [-152.9590, -579.6760], [-159.6450, -578.6450],
        [-162.4330, -578.0880], [-170.0640, -576.3930], [-171.8780, -575.9580], [-181.0690, -573.3880], [-185.9940, -571.8140],
        [-189.6930, -570.5430], [-196.7820, -567.9830], [-199.9210, -566.7840], [-202.9940, -565.5330], [-206.5290, -563.9870],
        [-210.0600, -562.3560], [-213.8830, -560.4830], [-218.2440, -558.2750], [-222.0340, -556.2790], [-225.2950, -554.4900],
        [-228.8760, -552.4320], [-231.9420, -550.5710], [-240.4740, -545.0700], [-242.6040, -543.6270], [-244.4390, -542.3140],
        [-247.2870, -540.1620], [-255.0080, -534.1510], [-258.3070, -531.5010], [-261.4650, -528.8640], [-264.0260, -526.6140],
        [-266.7310, -524.0740], [-269.1050, -521.7350], [-276.5570, -514.2450], [-279.1140, -511.5130], [-284.6560, -505.1740],
        [-286.3590, -503.1310], [-288.2050, -500.8160], [-292.7250, -494.8640], [-295.3870, -491.1570], [-300.9370, -483.0610],
        [-301.8660, -481.6110], [-302.7140, -480.1370], [-305.0220, -475.6030], [-308.2820, -469.8510], [-309.7700, -467.0750],
        [-313.0510, -460.6500], [-314.0960, -458.4900], [-315.3270, -455.7780], [-318.2220, -449.1730], [-320.2810, -444.0470],
        [-321.2720, -441.4720], [-323.4130, -435.4930], [-324.1660, -433.1980], [-326.4470, -425.6240], [-328.4030, -418.1410],
        [-329.1900, -414.7990], [-331.4150, -404.3380], [-331.7540, -402.4570], [-332.0330, -400.5370], [-332.7530, -394.3450],
        [-333.9340, -385.2870], [-334.3560, -381.3370], [-334.4990, -379.3210], [-334.5850, -377.2700], [-334.6450, -371.3530],
        [-334.7800, -116.0390], [-334.6940, -115.4590], [-334.5430, -115.0960], [-334.3260, -114.7700], [-333.8910, -114.3760],
        [-333.5450, -114.1920], [-333.1700, -114.0780], [-332.7800, -114.0390], [-300.9110, -114.0390], [-300.3300, -114.1250],
        [-299.9680, -114.2750], [-299.6420, -114.4930], [-299.3650, -114.7700], [-299.1470, -115.0960], [-298.9490, -115.6490],
        [-298.9110, -116.0390], [-298.9110, -121.8400], [-298.8590, -123.2080], [-298.8330, -126.3400], [-298.8310, -366.6990],
        [-298.7750, -369.1170], [-298.6780, -371.1600], [-298.2510, -376.8630], [-297.9850, -381.9520], [-297.8030, -384.2850],
        [-297.5210, -386.5530], [-296.6650, -391.9580], [-295.6280, -399.3760], [-295.2990, -401.2670], [-294.8490, -403.4260],
        [-293.1730, -410.7150], [-292.4810, -413.3940], [-290.1300, -421.2510], [-288.0910, -427.2380], [-286.9890, -430.3470],
        [-285.7150, -433.7120], [-284.5900, -436.5180], [-283.1590, -439.8790], [-281.9010, -442.6540], [-280.5650, -445.3880],
        [-278.8890, -448.6390], [-276.5870, -452.9990], [-274.9040, -456.0450], [-273.2690, -458.8410], [-271.5610, -461.6200],
        [-269.3030, -465.1610], [-267.1900, -468.3420], [-265.2160, -471.1970], [-263.3500, -473.7920], [-261.5850, -476.1230],
        [-259.5380, -478.6910], [-257.6350, -480.9690], [-71.7500, 577.0840], [-69.5710, 575.7300], [-67.7140, 574.4220],
        [-65.6610, 572.7970], [-63.6870, 571.0300], [-62.0450, 569.3730], [-60.5080, 567.6280], [-58.8920, 565.5600],
        [-57.4320, 563.4340], [-56.1390, 561.2570], [-55.0220, 559.0410], [-53.9520, 556.5190], [-53.1430, 554.2350],
        [-52.4870, 551.8580], [-52.0630, 549.6740], [-51.7870, 547.3920], [-51.6390, 545.0300], [-51.5700, 541.9210],
        [-51.4630, 94.1220], [-51.5180, 91.0050], [-51.6720, 88.2980], [-51.8080, 86.9800], [-51.9900, 85.6930],
        [-52.4270, 83.5180], [-53.0980, 81.1510], [-54.0310, 78.5920], [-55.1320, 76.0770], [-56.4230, 73.5940],
        [-57.8990, 71.1630], [-59.5270, 68.7930], [-61.2910, 66.4980], [-62.9940, 64.5630], [-64.6020, 62.9860],
        [-66.5550, 61.3190], [-69.1110, 59.3930], [-71.4910, 57.7990], [-73.9350, 56.3670], [-76.1490, 55.2550],
        [-78.3870, 54.2920], [-80.6610, 53.4610], [-83.0190, 52.7780], [-85.1830, 52.3260], [-87.1180, 52.0550],
        [-89.4560, 51.8660], [-92.2010, 51.7710], [-99.5300, 51.7320], [-260.4540, 51.5410], [-263.5520, 51.5980],
        [-269.5520, 51.5980], [-269.9420, 51.6360], [-270.3170, 51.7500], [-270.8210, 52.0520], [-271.2150, 52.4870],
        [-271.4660, 53.0170], [-271.5520, 53.5980], [-271.5520, 85.3830], [-271.5130, 85.7730], [-271.4000, 86.1480],
        [-271.0980, 86.6520], [-270.8210, 86.9290], [-270.4950, 87.1470], [-269.9420, 87.3440], [-269.5520, 87.3830],
        [-89.0000, 87.3970], [-87.4140, 88.9610], [-87.4140, 544.6660], [-89.0000, 546.2300], [-114.2050, 546.2260],
        [-117.3420, 546.2010], [-119.7560, 546.1360], [-122.1320, 546.0060], [-127.8440, 545.5890], [-129.8970, 545.5050],
        [-136.1070, 545.3550], [-138.1320, 545.2370], [-140.4440, 545.0200], [-143.0290, 544.6810], [-145.5670, 544.2700],
        [-155.6290, 542.4990], [-159.0040, 541.7770], [-168.6330, 539.3390], [-171.5600, 538.4700], [-176.1920, 536.9920],
        [-179.9540, 535.6640], [-184.3090, 534.0130], [-188.8340, 532.1670], [-192.4540, 530.5780], [-197.1090, 528.3950],
        [-202.7440, 525.6520], [-205.6370, 524.1110], [-209.5830, 521.8680], [-213.6160, 519.4590], [-218.1700, 516.5350],
        [-221.8270, 514.0830], [-225.1890, 511.6550], [-229.3020, 508.4980], [-233.5730, 505.0480], [-237.5010, 501.7080],
        [-240.5790, 498.9060], [-243.5470, 495.9930], [-252.1700, 487.1940], [-254.7560, 484.3640], [-257.9750, 480.6030],
        [-261.3870, 476.3460], [-264.1050, 472.7220], [-267.3760, 468.0380], [-270.5090, 463.2530], [-273.3120, 458.7590],
        [-275.4500, 455.0770], [-277.6010, 451.0800], [-281.0830, 444.3290], [-282.8930, 440.4690], [-285.0340, 435.4240],
        [-287.4290, 429.2730], [-288.9220, 425.0200], [-290.5010, 420.1260], [-292.6460, 412.8240], [-293.2510, 410.4340],
        [-294.9930, 402.8380], [-295.3680, 400.9850], [-295.7390, 398.7750], [-296.6780, 391.9990], [-297.5830, 386.2710],
        [-297.8570, 383.9960], [-298.0110, 381.9930], [-298.2820, 376.9020], [-298.8240, 369.8380], [-298.9410, 366.7360],
        [-298.9670, 363.0940], [-299.0430, 362.7090], [-299.1100, 362.5250], [-299.1930, 362.3470], [-299.4110, 362.0210],
        [-299.8460, 361.6270], [-300.3770, 361.3760], [-300.9570, 361.2900], [-332.7750, 361.2900], [-333.3560, 361.3760],
        [-333.7180, 361.5260], [-334.0440, 361.7440], [-334.4380, 362.1790], [-334.6890, 362.7090], [-334.7750, 363.2900],
        [-334.7420, 375.5260], [-334.6680, 378.2870], [-334.5280, 380.6590], [-334.3140, 382.9860], [-334.0110, 385.6080],
        [-332.9010, 394.0220], [-332.2130, 399.8920], [-331.9010, 402.1440], [-331.5110, 404.3450], [-330.4080, 409.5760],
        [-329.5060, 414.2380], [-328.8090, 417.2860], [-326.4480, 425.8980], [-323.8640, 434.3290], [-322.7830, 437.4640],
        [-321.3320, 441.4570], [-319.7730, 445.4640], [-318.3900, 448.8800], [-315.4880, 455.4990], [-314.0070, 458.7500],
        [-312.8180, 461.1760], [-309.6700, 467.2880], [-308.1750, 470.0600], [-305.0770, 475.5030], [-304.2870, 477.0180],
        [-302.9340, 479.7460], [-301.9400, 481.5270], [-300.4420, 483.8480], [-295.5510, 490.9790], [-292.8890, 494.7000],
        [-288.5760, 500.4070], [-286.7420, 502.7270], [-285.0530, 504.7730], [-277.8960, 512.9270], [-275.6360, 515.3230],
        [-272.5250, 518.4730], [-266.1660, 524.6510], [-263.5390, 527.1200], [-260.4550, 529.8130], [-256.7350, 532.8770],
        [-249.5290, 538.6140], [-247.3350, 540.3160], [-244.0120, 542.7560], [-240.8290, 544.9490], [-233.4160, 549.7590],
        [-230.3490, 551.6810], [-225.6440, 554.4250], [-218.3370, 558.4730], [-216.4800, 559.6040], [-214.3940, 560.9990],
        [-212.3330, 561.7100], [-210.3240, 562.4880], [-203.1840, 565.5800], [-198.9730, 567.2830], [-195.2520, 568.6710],
        [-189.5980, 570.7050], [-183.5990, 572.7340], [-181.2680, 573.4600], [-172.6800, 575.8830], [-170.2690, 576.4800],
        [-162.6220, 578.1810], [-160.4630, 578.6300], [-158.5770, 578.9600], [-152.8400, 579.8330], [-146.8210, 580.8360],
        [-143.5760, 581.2600], [-134.2360, 582.0540], [-131.8600, 582.1830], [-129.1000, 582.2520], [-93.7670, 582.2640],
        [-89.9540, 582.2070], [-87.2460, 582.0620], [-84.9500, 581.8100], [-82.7300, 581.4180], [-80.5860, 580.8780],
        [-78.5140, 580.2040], [-76.2150, 579.3060], [-73.9660, 578.2740]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881, 882, 883, 884, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898, 899, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989],
        [990, 991, 992, 993, 994, 995, 996, 997, 998, 999, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066],
        [1067, 1068, 1069, 1070, 1071, 1072, 1073, 1074, 1075, 1076, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154, 1155, 1156, 1157, 1158],
        [1159, 1160, 1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240, 1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1360, 1361, 1362, 1363, 1364, 1365, 1366, 1367, 1368, 1369, 1370, 1371],
        [1372, 1373, 1374, 1375, 1376, 1377, 1378, 1379, 1380, 1381, 1382, 1383, 1384, 1385, 1386, 1387, 1388, 1389, 1390],
        [1391, 1392, 1393, 1394, 1395, 1396, 1397, 1398, 1399, 1400, 1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416, 1417, 1418, 1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1470, 1471, 1472],
        [1473, 1474, 1475, 1476, 1477, 1478, 1479, 1480, 1481, 1482, 1483, 1484, 1485, 1486, 1487, 1488, 1489, 1490, 1491, 1492, 1493, 1494, 1495, 1496, 1497, 1498, 1499, 1500, 1501, 1502, 1503],
        [1504, 1505, 1506, 1507, 1508, 1509, 1510, 1511, 1512, 1513, 1514, 1515, 1516, 1517, 1518, 1519, 1520, 1521, 1522, 1523, 1524, 1525, 1526, 1527, 1528, 1529, 1530, 1531, 1532, 1533, 1534, 1535, 1536, 1537, 1538, 1539, 1540, 1541, 1542, 1543, 1544, 1545, 1546, 1547, 1548, 1549, 1550, 1551, 1552, 1553, 1554, 1555, 1556, 1557, 1558, 1559, 1560, 1561, 1562, 1563, 1564, 1565, 1566, 1567, 1568, 1569, 1570, 1571, 1572, 1573],
        [1574, 1575, 1576, 1577, 1578, 1579, 1580, 1581, 1582, 1583, 1584, 1585, 1586, 1587, 1588, 1589, 1590, 1591, 1592, 1593, 1594, 1595, 1596, 1597, 1598, 1599, 1600, 1601, 1602, 1603, 1604, 1605, 1606, 1607, 1608, 1609, 1610, 1611, 1612, 1613, 1614, 1615, 1616, 1617, 1618, 1619, 1620, 1621, 1622, 1623, 1624, 1625, 1626, 1627, 1628, 1629, 1630, 1631, 1632, 1633, 1634, 1635, 1636, 1637, 1638, 1639, 1640, 1641, 1642, 1643, 1644, 1645, 1646, 1647, 1648],
        [1649, 1650, 1651, 1652, 1653, 1654, 1655, 1656, 1657, 1658, 1659, 1660, 1661, 1662, 1663, 1664, 1665, 1666, 1667, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675, 1676, 1677, 1678, 1679],
        [1680, 1681, 1682, 1683, 1684, 1685, 1686, 1687, 1688, 1689, 1690, 1691, 1692, 1693, 1694, 1695, 1696, 1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711, 1712, 1713, 1714, 1715, 1716, 1717, 1718, 1719, 1720, 1721, 1722, 1723, 1724, 1725, 1726, 1727, 1728, 1729, 1730, 1731, 1732, 1733, 1734, 1735, 1736, 1737, 1738, 1739, 1740, 1741, 1742, 1743, 1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1752],
        [1753, 1754, 1755, 1756, 1757, 1758, 1759, 1760, 1761, 1762, 1763, 1764, 1765, 1766, 1767, 1768, 1769, 1770, 1771, 1772, 1773, 1774, 1775, 1776, 1777, 1778, 1779, 1780, 1781],
        [1782, 1783, 1784, 1785, 1786, 1787, 1788, 1789, 1790, 1791, 1792, 1793, 1794, 1795, 1796, 1797, 1798, 1799, 1800, 1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809, 1810, 1811, 1812, 1813, 1814, 1815, 1816, 1817, 1818, 1819, 1820, 1821, 1822, 1823, 1824, 1825, 1826, 1827, 1828, 1829, 1830, 1831, 1832, 1833, 1834, 1835, 1836, 1837, 1838, 1839, 1840, 1841, 1842, 1843, 1844, 1845, 1846, 1847, 1848, 1849, 1850, 1851, 1852, 1853, 1854, 1855, 1856, 1857, 1858, 1859, 1860, 1861, 1862],
        [1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870, 1871, 1872, 1873, 1874, 1875, 1876, 1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885, 1886, 1887, 1888, 1889, 1890, 1891, 1892, 1893, 1894, 1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 1950, 1951],
        [1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989],
        [1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050, 2051, 2052, 2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065, 2066, 2067, 2068, 2069, 2070, 2071, 2072, 2073, 2074, 2075, 2076, 2077, 2078, 2079, 2080, 2081, 2082, 2083, 2084, 2085, 2086, 2087, 2088, 2089, 2090, 2091, 2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099, 2100, 2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109, 2110, 2111, 2112, 2113, 2114, 2115, 2116, 2117, 2118, 2119, 2120, 2121, 2122, 2123, 2124, 2125, 2126, 2127, 2128, 2129, 2130, 2131, 2132, 2133, 2134, 2135, 2136, 2137, 2138, 2139, 2140, 2141, 2142, 2143, 2144, 2145, 2146, 2147, 2148, 2149, 2150, 2151, 2152, 2153, 2154, 2155, 2156, 2157, 2158, 2159, 2160, 2161, 2162, 2163, 2164, 2165, 2166, 2167, 2168, 2169, 2170, 2171, 2172, 2173, 2174, 2175, 2176, 2177, 2178, 2179, 2180, 2181, 2182, 2183, 2184, 2185, 2186, 2187, 2188, 2189, 2190, 2191, 2192, 2193, 2194, 2195, 2196, 2197, 2198, 2199, 2200, 2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208, 2209, 2210, 2211, 2212, 2213, 2214, 2215, 2216, 2217, 2218, 2219, 2220, 2221, 2222, 2223, 2224, 2225, 2226, 2227],
        [2228, 2229, 2230, 2231, 2232, 2233, 2234, 2235, 2236, 2237, 2238, 2239, 2240, 2241, 2242, 2243, 2244, 2245, 2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261, 2262],
        [2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2274, 2275, 2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290, 2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320, 2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335, 2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2351, 2352, 2353, 2354, 2355, 2356, 2357, 2358, 2359, 2360, 2361, 2362, 2363, 2364, 2365, 2366, 2367, 2368, 2369, 2370, 2371, 2372, 2373, 2374, 2375, 2376, 2377, 2378, 2379, 2380, 2381, 2382, 2383, 2384, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394, 2395, 2396, 2397, 2398, 2399, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2408, 2409, 2410, 2411, 2412, 2413, 2414, 2415, 2416, 2417, 2418, 2419, 2420, 2421, 2422, 2423, 2424, 2425, 2426, 2427, 2428, 2429, 2430, 2431, 2432, 2433, 2434, 2435, 2436, 2437, 2438, 2439, 2440, 2441, 2442, 2443, 2444, 2445, 2446, 2447, 2448, 2449, 2450, 2451, 2452, 2453, 2454, 2455, 2456, 2457, 2458, 2459, 2460, 2461, 2462],
        [2463, 2464, 2465, 2466, 2467, 2468, 2469, 2470, 2471, 2472, 2473, 2474, 2475, 2476, 2477, 2478, 2479, 2480, 2481, 2482, 2483, 2484, 2485, 2486, 2487, 2488, 2489, 2490, 2491, 2492, 2493, 2494, 2495, 2496, 2497, 2498, 2499, 2500, 2501, 2502, 2503, 2504, 2505, 2506, 2507, 2508, 2509, 2510, 2511, 2512, 2513, 2514, 2515, 2516, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526, 2527, 2528, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 2538, 2539, 2540, 2541, 2542, 2543, 2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552, 2553, 2554, 2555, 2556, 2557, 2558, 2559, 2560, 2561, 2562, 2563, 2564, 2565, 2566, 2567, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2575, 2576, 2577, 2578, 2579, 2580, 2581, 2582, 2583, 2584, 2585, 2586, 2587, 2588, 2589, 2590, 2591, 2592, 2593, 2594, 2595, 2596, 2597, 2598, 2599, 2600, 2601, 2602, 2603, 2604, 2605, 2606, 2607, 2608, 2609, 2610, 2611, 2612, 2613, 2614, 2615, 2616, 2617, 2618, 2619, 2620, 2621, 2622, 2623, 2624, 2625, 2626, 2627, 2628, 2629, 2630, 2631, 2632, 2633, 2634, 2635, 2636, 2637, 2638, 2639, 2640, 2641, 2642, 2643, 2644, 2645, 2646, 2647, 2648, 2649, 2650, 2651, 2652, 2653, 2654, 2655, 2656, 2657, 2658, 2659, 2660, 2661, 2662, 2663, 2664, 2665, 2666, 2667, 2668, 2669, 2670, 2671, 2672, 2673, 2674, 2675, 2676, 2677, 2678, 2679, 2680, 2681, 2682, 2683, 2684, 2685, 2686, 2687, 2688, 2689, 2690, 2691, 2692, 2693, 2694, 2695, 2696, 2697, 2698, 2699, 2700, 2701],
        [2702, 2703, 2704, 2705, 2706, 2707, 2708, 2709, 2710, 2711, 2712, 2713, 2714, 2715, 2716, 2717, 2718, 2719, 2720, 2721, 2722, 2723, 2724, 2725, 2726, 2727, 2728, 2729, 2730, 2731, 2732, 2733, 2734, 2735, 2736, 2737, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 2749, 2750, 2751, 2752, 2753, 2754, 2755, 2756, 2757, 2758, 2759, 2760, 2761, 2762, 2763, 2764, 2765, 2766, 2767, 2768, 2769, 2770, 2771, 2772, 2773, 2774, 2775, 2776, 2777, 2778, 2779, 2780, 2781, 2782, 2783, 2784, 2785, 2786, 2787, 2788, 2789, 2790, 2791, 2792, 2793, 2794, 2795, 2796, 2797, 2798, 2799, 2800, 2801, 2802, 2803, 2804, 2805, 2806, 2807, 2808, 2809, 2810, 2811, 2812, 2813, 2814, 2815, 2816, 2817, 2818, 2819, 2820, 2821, 2822, 2823, 2824, 2825, 2826, 2827, 2828, 2829, 2830, 2831, 2832, 2833, 2834, 2835, 2836, 2837, 2838, 2839, 2840, 2841, 2842, 2843, 2844, 2845, 2846, 2847, 2848, 2849, 2850, 2851, 2852, 2853, 2854, 2855, 2856, 2857, 2858, 2859, 2860, 2861, 2862, 2863, 2864, 2865, 2866, 2867, 2868, 2869, 2870, 2871, 2872, 2873, 2874, 2875, 2876, 2877, 2878, 2879, 2880, 2881, 2882, 2883, 2884, 2885, 2886, 2887, 2888, 2889, 2890, 2891, 2892, 2893, 2894, 2895, 2896, 2897, 2898, 2899, 2900, 2901, 2902, 2903, 2904, 2905, 2906, 2907],
        [2908, 2909, 2910, 2911, 2912, 2913, 2914, 2915, 2916, 2917, 2918, 2919, 2920, 2921, 2922, 2923, 2924, 2925, 2926, 2927, 2928, 2929, 2930, 2931, 2932, 2933, 2934, 2935, 2936, 2937, 2938, 2939, 2940, 2941, 2942],
        [2943, 2944, 2945, 2946, 2947, 2948, 2949, 2950, 2951, 2952, 2953, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 2961, 2962, 2963, 2964, 2965, 2966, 2967, 2968, 2969, 2970, 2971, 2972, 2973, 2974, 2975, 2976, 2977, 2978, 2979, 2980, 2981, 2982, 2983, 2984, 2985, 2986, 2987, 2988, 2989, 2990, 2991, 2992, 2993, 2994, 2995, 2996, 2997, 2998, 2999, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010, 3011, 3012, 3013, 3014, 3015, 3016, 3017, 3018, 3019, 3020, 3021, 3022, 3023, 3024, 3025, 3026, 3027, 3028, 3029, 3030, 3031, 3032, 3033, 3034, 3035, 3036, 3037, 3038, 3039, 3040, 3041, 3042, 3043, 3044, 3045, 3046, 3047, 3048, 3049, 3050, 3051, 3052, 3053, 3054, 3055, 3056, 3057, 3058, 3059, 3060, 3061, 3062, 3063, 3064, 3065, 3066, 3067, 3068, 3069, 3070, 3071, 3072, 3073, 3074, 3075, 3076, 3077, 3078, 3079, 3080, 3081, 3082, 3083, 3084, 3085, 3086, 3087, 3088, 3089, 3090, 3091, 3092, 3093, 3094, 3095, 3096, 3097, 3098, 3099, 3100, 3101, 3102, 3103, 3104, 3105, 3106, 3107, 3108, 3109, 3110, 3111, 3112, 3113, 3114, 3115, 3116, 3117, 3118, 3119, 3120, 3121, 3122, 3123, 3124, 3125, 3126, 3127, 3128, 3129, 3130, 3131, 3132, 3133, 3134, 3135, 3136, 3137, 3138, 3139, 3140, 3141, 3142, 3143, 3144, 3145, 3146, 3147, 3148, 3149, 3150, 3151, 3152, 3153, 3154, 3155, 3156, 3157, 3158, 3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 3171, 3172, 3173, 3174, 3175, 3176, 3177, 3178, 3179, 3180, 3181, 3182],
        [3183, 3184, 3185, 3186, 3187, 3188, 3189, 3190, 3191, 3192, 3193, 3194, 3195, 3196, 3197, 3198, 3199, 3200, 3201, 3202, 3203, 3204, 3205, 3206, 3207, 3208, 3209, 3210, 3211, 3212, 3213, 3214, 3215, 3216, 3217, 3218],
        [3219, 3220, 3221, 3222, 3223, 3224, 3225, 3226, 3227, 3228, 3229, 3230, 3231, 3232, 3233, 3234, 3235, 3236, 3237, 3238, 3239, 3240, 3241, 3242, 3243, 3244, 3245, 3246, 3247, 3248, 3249, 3250, 3251, 3252, 3253, 3254, 3255, 3256, 3257, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 3277, 3278, 3279, 3280, 3281, 3282, 3283, 3284, 3285, 3286, 3287, 3288, 3289, 3290, 3291, 3292, 3293, 3294, 3295, 3296, 3297, 3298, 3299, 3300, 3301, 3302, 3303, 3304, 3305, 3306, 3307, 3308, 3309, 3310, 3311, 3312, 3313, 3314, 3315, 3316, 3317, 3318, 3319, 3320, 3321, 3322, 3323, 3324, 3325, 3326, 3327, 3328, 3329, 3330, 3331, 3332, 3333, 3334, 3335, 3336, 3337, 3338, 3339, 3340, 3341, 3342, 3343, 3344, 3345, 3346, 3347, 3348, 3349, 3350, 3351, 3352, 3353, 3354, 3355, 3356, 3357, 3358, 3359, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 3381, 3382, 3383, 3384, 3385, 3386, 3387, 3388, 3389, 3390, 3391, 3392, 3393, 3394, 3395, 3396, 3397, 3398, 3399, 3400, 3401, 3402, 3403, 3404, 3405, 3406, 3407, 3408, 3409, 3410, 3411, 3412, 3413, 3414, 3415, 3416, 3417, 3418, 3419, 3420, 3421, 3422, 3423, 3424, 3425, 3426, 3427, 3428, 3429, 3430, 3431, 3432, 3433, 3434, 3435, 3436, 3437, 3438, 3439],
        [3440, 3441, 3442, 3443, 3444, 3445, 3446, 3447, 3448, 3449, 3450, 3451, 3452, 3453, 3454, 3455, 3456, 3457, 3458, 3459, 3460, 3461, 3462, 3463, 3464, 3465, 3466, 3467, 3468, 3469, 3470, 3471, 3472, 3473, 3474, 3475, 3476, 3477, 3478, 3479, 3480, 3481, 3482, 3483, 3484, 3485, 3486, 3487, 3488, 3489, 3490, 3491, 3492, 3493, 3494, 3495, 3496, 3497, 3498, 3499, 3500, 3501, 3502, 3503, 3504, 3505, 3506, 3507, 3508, 3509, 3510, 3511, 3512, 3513, 3514, 3515, 3516, 3517, 3518, 3519, 3520, 3521, 3522, 3523, 3524, 3525, 3526, 3527, 3528, 3529, 3530, 3531, 3532, 3533, 3534, 3535, 3536, 3537, 3538, 3539, 3540, 3541, 3542, 3543, 3544, 3545, 3546, 3547, 3548, 3549, 3550, 3551, 3552, 3553, 3554, 3555, 3556, 3557, 3558, 3559, 3560, 3561, 3562, 3563, 3564, 3565, 3566, 3567, 3568, 3569, 3570, 3571, 3572, 3573, 3574, 3575, 3576, 3577, 3578, 3579, 3580, 3581, 3582, 3583, 3584, 3585, 3586, 3587, 3588, 3589, 3590, 3591, 3592, 3593, 3594, 3595, 3596, 3597, 3598, 3599, 3600, 3601, 3602, 3603, 3604, 3605, 3606, 3607, 3608, 3609, 3610, 3611, 3612, 3613, 3614, 3615, 3616, 3617, 3618, 3619, 3620, 3621, 3622, 3623, 3624, 3625, 3626, 3627, 3628, 3629, 3630, 3631, 3632, 3633, 3634, 3635, 3636, 3637, 3638, 3639, 3640, 3641, 3642, 3643, 3644, 3645, 3646],
        [3647, 3648, 3649, 3650, 3651, 3652, 3653, 3654, 3655, 3656, 3657, 3658, 3659, 3660, 3661, 3662, 3663, 3664, 3665, 3666, 3667, 3668, 3669, 3670, 3671, 3672, 3673, 3674, 3675, 3676, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685, 3686, 3687, 3688, 3689, 3690, 3691, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699, 3700, 3701, 3702, 3703, 3704, 3705, 3706, 3707, 3708, 3709, 3710, 3711, 3712, 3713, 3714, 3715, 3716, 3717, 3718, 3719, 3720, 3721, 3722, 3723, 3724, 3725, 3726, 3727, 3728, 3729, 3730, 3731, 3732, 3733, 3734, 3735, 3736, 3737, 3738, 3739, 3740, 3741, 3742, 3743, 3744, 3745, 3746, 3747, 3748, 3749, 3750, 3751, 3752, 3753, 3754, 3755, 3756, 3757, 3758, 3759, 3760, 3761, 3762, 3763, 3764, 3765, 3766, 3767, 3768, 3769, 3770, 3771, 3772, 3773, 3774, 3775, 3776, 3777, 3778, 3779, 3780, 3781, 3782, 3783, 3784, 3785, 3786, 3787, 3788, 3789, 3790, 3791, 3792, 3793, 3794, 3795, 3796, 3797, 3798, 3799, 3800, 3801, 3802, 3803, 3804, 3805, 3806, 3807, 3808, 3809, 3810, 3811, 3812, 3813, 3814, 3815, 3816, 3817, 3818, 3819, 3820, 3821, 3822, 3823, 3824, 3825, 3826, 3827, 3828, 3829, 3830, 3831, 3832, 3833, 3834, 3835, 3836, 3837, 3838, 3839, 3840, 3841, 3842, 3843, 3844, 3845, 3846, 3847, 3848, 3849, 3850, 3851, 3852, 3853, 3854, 3855, 3856, 3857, 3858, 3859, 3860, 3861, 3862, 3863, 3864, 3865, 3866, 3867]
    ], convexity = 30);
}

module fabric_outline() {
    polygon(points = [
        [-271.3030, -333.6290], [-271.0850, -333.9550], [-270.6500, -334.3490], [-270.1200, -334.6000], [-269.7350, -334.6760],
        [-263.5390, -334.6860], [-262.5500, -334.7300], [-255.9210, -334.7610], [22.2070, -334.7510], [22.5920, -334.6750],
        [22.9540, -334.5250], [23.4250, -334.1750], [23.6740, -333.8720], [23.8590, -333.5260], [24.0010, -332.9570],
        [24.0010, -300.6700], [23.8590, -300.1000], [23.6740, -299.7540], [23.4250, -299.4510], [23.1220, -299.2030],
        [22.7760, -299.0180], [22.4010, -298.9040], [22.0110, -298.8660], [-257.6700, -298.8660], [-262.5500, -298.8960],
        [-263.5390, -298.9460], [-269.7350, -298.9550], [-270.1200, -299.0320], [-270.4820, -299.1820], [-270.9530, -299.5310],
        [-271.2020, -299.8340], [-271.3870, -300.1800], [-271.5010, -300.5550], [-271.5390, -300.9460], [-271.5390, -332.6860],
        [-271.5010, -333.0760]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
    ], convexity = 30);
    polygon(points = [
        [-447.3530, -279.5380], [-453.5300, -276.2930], [-457.4890, -274.0640], [-461.4360, -271.6550], [-466.4920, -268.4070],
        [-470.6710, -265.5620], [-474.3050, -262.9450], [-477.1490, -260.7540], [-479.9620, -258.4620], [-484.4820, -254.5930],
        [-486.9480, -252.3830], [-488.6550, -250.7480], [-497.4120, -242.1350], [-499.9660, -239.4540], [-502.5070, -236.5950],
        [-504.8560, -233.8070], [-507.2490, -230.8180], [-511.4420, -225.4090], [-513.5610, -222.4990], [-517.7550, -216.2550],
        [-519.5330, -213.5060], [-521.5350, -210.1670], [-523.8430, -206.0560], [-525.9700, -201.9920], [-528.9360, -196.0030],
        [-530.8580, -191.8810], [-532.5490, -187.9720], [-534.4910, -183.1370], [-536.4250, -177.9050], [-537.5760, -174.4350],
        [-539.0570, -169.4680], [-541.5810, -159.8850], [-542.0200, -158.0720], [-542.4100, -156.2290], [-544.6140, -143.6470],
        [-545.0500, -140.4240], [-545.2910, -137.7780], [-545.4220, -135.0610], [-545.6010, -128.1660], [-546.0800, -121.4390],
        [-546.2240, -117.6710], [-546.2580, -112.7890], [-546.2590, -88.9850], [-544.6950, -87.4000], [-88.9750, -87.4000],
        [-87.4110, -88.9850], [-87.3970, -269.5520], [-87.3580, -269.9420], [-87.1610, -270.4950], [-86.9430, -270.8210],
        [-86.6660, -271.0980], [-86.1620, -271.4000], [-85.7870, -271.5130], [-85.3970, -271.5520], [-53.5290, -271.5520],
        [-53.1390, -271.5130], [-52.7640, -271.4000], [-52.4180, -271.2150], [-52.1150, -270.9660], [-51.8670, -270.6630],
        [-51.6820, -270.3170], [-51.5680, -269.9420], [-51.5290, -269.5520], [-51.5320, -95.8350], [-51.5560, -92.3510],
        [-51.6240, -89.9460], [-51.7540, -87.9300], [-51.9330, -86.2980], [-52.1300, -85.0270], [-52.3760, -83.7890],
        [-52.6700, -82.5840], [-53.0080, -81.4070], [-53.4860, -79.9700], [-54.0170, -78.5560], [-54.5990, -77.1540],
        [-55.2350, -75.7600], [-56.5330, -73.2780], [-58.0170, -70.8500], [-59.8420, -68.2330], [-60.8140, -66.9590],
        [-61.8270, -65.7160], [-63.5580, -63.8140], [-64.4800, -62.9120], [-65.4370, -62.0470], [-67.6960, -60.2080],
        [-70.3250, -58.3030], [-72.5080, -56.9070], [-74.7470, -55.6780], [-77.0080, -54.6280], [-79.5600, -53.6160],
        [-81.2900, -53.0300], [-82.7720, -52.6070], [-84.6110, -52.1920], [-86.2000, -51.9300], [-87.8370, -51.7430],
        [-89.8550, -51.6050], [-91.9150, -51.5380], [-94.6970, -51.5080], [-542.2750, -51.5350], [-545.3720, -51.6160],
        [-547.0530, -51.7220], [-548.3680, -51.8520], [-549.6520, -52.0280], [-550.9040, -52.2530], [-552.1240, -52.5270],
        [-553.3120, -52.8460], [-554.4750, -53.2090], [-555.9000, -53.7150], [-557.3090, -54.2790], [-558.7100, -54.9030],
        [-560.1070, -55.5960], [-561.2220, -56.2030], [-562.6080, -57.0230], [-563.9810, -57.9020], [-566.3980, -59.6160],
        [-567.6960, -60.6440], [-568.7060, -61.5100], [-570.6320, -63.3530], [-571.5440, -64.3200], [-572.6340, -65.5630],
        [-574.4580, -67.8760], [-575.3960, -69.2040], [-576.1070, -70.2880], [-576.9430, -71.6690], [-577.5660, -72.7920],
        [-578.6820, -75.0880], [-579.7450, -77.7330], [-580.2610, -79.2190], [-580.7250, -80.7190], [-581.1290, -82.2410],
        [-581.4040, -83.4820], [-581.6310, -84.7480], [-581.8100, -86.0430], [-581.9430, -87.3640], [-582.0510, -89.0500],
        [-582.1250, -91.4560], [-582.1520, -94.9400], [-582.1340, -128.8700], [-582.0690, -131.6310], [-581.9440, -134.0070],
        [-581.3120, -141.6850], [-581.0850, -144.0000], [-580.7380, -146.5910], [-579.6910, -152.9300], [-578.7110, -159.6460],
        [-578.1480, -162.4290], [-575.9790, -171.4940], [-573.4850, -180.6970], [-572.5870, -183.6150], [-571.2470, -187.6290],
        [-567.9900, -196.7170], [-566.7870, -199.8590], [-565.5310, -202.9360], [-563.9820, -206.4750], [-562.4800, -209.7310],
        [-560.4820, -213.8200], [-558.1340, -218.4490], [-555.9870, -222.5060], [-554.1840, -225.7570], [-552.4420, -228.7270],
        [-550.6150, -231.6770], [-545.7830, -239.2940], [-543.4560, -242.7650], [-541.7500, -245.1150], [-539.5780, -247.9540],
        [-534.1670, -254.9000], [-530.7010, -259.1800], [-528.2670, -262.0410], [-525.7470, -264.8790], [-523.4700, -267.3230],
        [-521.2950, -269.5370], [-512.7800, -277.8270], [-510.9640, -279.4680], [-505.3650, -284.3650], [-502.8110, -286.4500],
        [-497.4090, -290.6670], [-494.5620, -292.8310], [-492.1870, -294.5550], [-487.5980, -297.7170], [-483.5290, -300.4310],
        [-479.7540, -302.8530], [-476.5640, -304.7670], [-471.7230, -307.5050], [-468.4630, -309.2770], [-461.1500, -313.0340],
        [-457.8930, -314.6320], [-454.3010, -316.2700], [-449.7950, -318.1940], [-444.0750, -320.4700], [-440.3570, -321.8810],
        [-435.5200, -323.5920], [-432.3490, -324.6140], [-425.9280, -326.5430], [-418.5090, -328.5710], [-416.4010, -329.1040],
        [-414.5580, -329.5110], [-409.5720, -330.4720], [-404.6520, -331.5050], [-402.7760, -331.8480], [-400.2150, -332.2160],
        [-393.3780, -333.0180], [-384.9970, -334.1620], [-381.3710, -334.5360], [-379.0010, -334.6720], [-376.2410, -334.7390],
        [-363.2900, -334.7570], [-362.7090, -334.6710], [-362.3470, -334.5210], [-362.0210, -334.3030], [-361.6270, -333.8680],
        [-361.3760, -333.3370], [-361.2900, -332.7570], [-361.2900, -300.8880], [-361.3280, -300.4980], [-361.5260, -299.9450],
        [-361.7440, -299.6190], [-362.1790, -299.2250], [-362.7090, -298.9740], [-363.0940, -298.8980], [-366.8470, -298.8760],
        [-369.9470, -298.7730], [-377.0100, -298.2520], [-381.7640, -298.0040], [-383.7720, -297.8580], [-386.0540, -297.5960],
        [-391.4720, -296.7670], [-397.5940, -295.9550], [-399.8080, -295.6000], [-401.6700, -295.2420], [-410.1800, -293.2960],
        [-412.2790, -292.7780], [-415.2160, -291.9470], [-421.9080, -289.9320], [-426.7790, -288.3130], [-430.1570, -287.0850],
        [-435.7490, -284.8900], [-440.5130, -282.8640], [-443.8270, -281.3210]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237]
    ], convexity = 30);
    polygon(points = [
        [-299.8570, 271.2020], [-300.3870, 271.4530], [-300.9680, 271.5390], [-332.7070, 271.5390], [-333.0980, 271.5010],
        [-333.4730, 271.3870], [-333.8190, 271.2020], [-334.1220, 270.9530], [-334.4710, 270.4820], [-334.6210, 270.1200],
        [-334.6980, 269.7350], [-334.7070, 263.5390], [-334.7530, 262.5300], [-334.7830, 255.9010], [-334.7830, -22.0110],
        [-334.6970, -22.5920], [-334.5470, -22.9540], [-334.3290, -23.2800], [-334.0520, -23.5570], [-333.7260, -23.7750],
        [-333.3640, -23.9250], [-332.9790, -24.0010], [-300.6910, -24.0010], [-300.3060, -23.9250], [-299.9440, -23.7750],
        [-299.4730, -23.4250], [-299.1230, -22.9540], [-298.9730, -22.5920], [-298.8970, -22.2070], [-298.8870, 257.6510],
        [-298.9180, 262.5300], [-298.9680, 263.5390], [-298.9780, 269.7350], [-299.0540, 270.1200], [-299.2040, 270.4820],
        [-299.4220, 270.8080]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
    ], convexity = 30);
    polygon(points = [
        [-496.8210, 242.7790], [-488.2100, 251.2260], [-485.2770, 253.9160], [-479.1390, 259.1680], [-476.5760, 261.2270],
        [-474.2470, 263.0070], [-471.6490, 264.8910], [-468.5270, 267.0590], [-465.6110, 269.0030], [-462.0850, 271.2610],
        [-458.8010, 273.2870], [-456.0960, 274.8740], [-452.8850, 276.6440], [-447.7700, 279.3280], [-444.7910, 280.8520],
        [-442.3250, 282.0420], [-439.5440, 283.2910], [-436.1760, 284.7150], [-432.2510, 286.2760], [-428.6200, 287.6560],
        [-425.4970, 288.7440], [-421.4780, 290.0610], [-413.0230, 292.5660], [-410.6350, 293.1730], [-403.0430, 294.9240],
        [-400.8870, 295.3770], [-399.0050, 295.7130], [-396.7720, 296.0480], [-391.2920, 296.7710], [-386.2120, 297.5530],
        [-384.2700, 297.7840], [-381.9410, 297.9610], [-376.8550, 298.2250], [-371.1510, 298.6530], [-369.1070, 298.7500],
        [-366.6890, 298.8040], [-126.6130, 298.8150], [-123.4770, 298.8360], [-121.8400, 298.8880], [-116.0390, 298.8880],
        [-115.6490, 298.9270], [-115.0960, 299.1240], [-114.7700, 299.3420], [-114.4930, 299.6190], [-114.2750, 299.9450],
        [-114.1250, 300.3080], [-114.0390, 300.8880], [-114.0390, 332.7610], [-114.0780, 333.1510], [-114.2750, 333.7040],
        [-114.4930, 334.0300], [-114.7700, 334.3070], [-115.2740, 334.6090], [-115.6490, 334.7230], [-116.0390, 334.7610],
        [-372.0890, 334.7600], [-378.0080, 334.7050], [-380.0600, 334.6220], [-381.7420, 334.5060], [-385.0330, 334.1570],
        [-394.0640, 332.9290], [-400.9020, 332.1280], [-402.8170, 331.8420], [-404.6940, 331.4980], [-409.3170, 330.5270],
        [-414.6250, 329.4990], [-417.3770, 328.8660], [-425.7000, 326.6050], [-432.9770, 324.4150], [-436.9720, 323.0880],
        [-442.6690, 321.0150], [-449.2530, 318.4190], [-454.8780, 316.0160], [-459.5460, 313.8350], [-466.3090, 310.3980],
        [-470.6630, 308.1150], [-475.5830, 305.4030], [-478.6160, 303.5980], [-482.2070, 301.3020], [-486.3040, 298.5940],
        [-491.4430, 295.0780], [-493.8360, 293.3650], [-496.1840, 291.6080], [-501.8540, 287.2050], [-504.1680, 285.3630],
        [-506.2060, 283.6510], [-510.7730, 279.6700], [-513.7750, 276.9140], [-523.2400, 267.4910], [-525.5820, 265.0530],
        [-527.6640, 262.7590], [-530.2990, 259.6740], [-533.3570, 255.9200], [-539.7820, 247.6920], [-541.9480, 244.8500],
        [-543.4610, 242.7580], [-544.7320, 240.9010], [-550.0610, 232.6770], [-551.7850, 229.8920], [-553.7270, 226.5700],
        [-555.5580, 223.2940], [-557.5830, 219.5030], [-559.6730, 215.4260], [-561.9690, 210.7920], [-563.5040, 207.5310],
        [-565.0750, 204.0040], [-566.4620, 200.6770], [-567.7880, 197.2580], [-570.3630, 190.1550], [-571.4490, 187.0370],
        [-572.6840, 183.3170], [-573.4020, 180.9930], [-575.6670, 172.7150], [-578.0710, 162.7560], [-578.5940, 160.2970],
        [-578.9090, 158.4010], [-579.7370, 152.6350], [-580.7840, 146.2910], [-581.0450, 144.3480], [-581.2810, 142.0380],
        [-581.9420, 134.0250], [-582.0680, 131.6490], [-582.1290, 129.2350], [-582.1520, 94.5980], [-582.1190, 91.1170],
        [-582.0150, 88.3780], [-581.8120, 86.0490], [-581.5290, 84.1220], [-581.1440, 82.2620], [-580.5780, 80.1730],
        [-579.8080, 77.8660], [-578.9160, 75.6090], [-578.0120, 73.6560], [-576.9730, 71.7180], [-575.6260, 69.5240],
        [-574.3200, 67.6420], [-572.8950, 65.8210], [-571.3470, 64.0800], [-569.6900, 62.4390], [-567.9540, 60.9050],
        [-566.1560, 59.4740], [-564.0290, 57.9560], [-561.8370, 56.5700], [-559.8910, 55.4900], [-557.9340, 54.5520],
        [-555.6810, 53.6330], [-553.6660, 52.9510], [-551.5730, 52.3950], [-549.6990, 52.0330], [-547.4230, 51.7480],
        [-545.7450, 51.6270], [-544.0350, 51.5580], [-538.8150, 51.5070], [-363.3500, 51.5590], [-362.9600, 51.5970],
        [-362.4070, 51.7950], [-362.0810, 52.0130], [-361.8040, 52.2900], [-361.5020, 52.7930], [-361.3880, 53.1680],
        [-361.3500, 53.5590], [-361.3500, 85.3820], [-361.3880, 85.7730], [-361.5020, 86.1480], [-361.8040, 86.6510],
        [-362.0810, 86.9290], [-362.4070, 87.1460], [-362.9600, 87.3440], [-363.3500, 87.3820], [-544.6700, 87.3970],
        [-546.2560, 88.9610], [-546.2630, 113.1120], [-546.2250, 117.9900], [-546.0890, 121.4110], [-545.6120, 128.1370],
        [-545.4120, 135.7160], [-545.2000, 139.0800], [-544.9080, 141.6940], [-544.5310, 144.2540], [-542.3750, 156.5050],
        [-541.6160, 159.8400], [-539.7370, 167.3310], [-538.9970, 169.9880], [-537.3630, 175.2080], [-536.1740, 178.6730],
        [-534.2170, 183.9010], [-532.1470, 188.9920], [-530.4340, 192.8800], [-528.4900, 196.9850], [-525.5040, 202.9620],
        [-523.3760, 206.9740], [-521.2940, 210.6540], [-519.3920, 213.7900], [-514.8260, 220.6910], [-512.7970, 223.6510],
        [-510.4810, 226.8000], [-507.8760, 230.1410], [-505.0240, 233.6460], [-502.1810, 236.9720], [-499.3960, 240.0730]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199]
    ], convexity = 30);
    polygon(points = [
        [291.9400, -415.2080], [289.9250, -421.9020], [288.3040, -426.7740], [287.0750, -430.1530], [284.8770, -435.7470],
        [282.8500, -440.5120], [281.3060, -443.8270], [279.5210, -447.3540], [276.2740, -453.5330], [274.0430, -457.4920],
        [271.6320, -461.4410], [268.3820, -466.4980], [265.5350, -470.6780], [262.9150, -474.3130], [260.7220, -477.1590],
        [258.4260, -479.9790], [254.2960, -484.8190], [252.0290, -487.3360], [250.1320, -489.2940], [241.3460, -498.1040],
        [239.0410, -500.2960], [236.4320, -502.6120], [233.8760, -504.7650], [231.1460, -506.9600], [225.7420, -511.1570],
        [222.8420, -513.2910], [216.8730, -517.3130], [213.8560, -519.2800], [211.0690, -520.9680], [207.7330, -522.8410],
        [201.4780, -526.1420], [197.1460, -528.3440], [192.7660, -530.4260], [188.8700, -532.1430], [183.7700, -534.2160],
        [178.2440, -536.2740], [174.4720, -537.5330], [169.4880, -539.0210], [166.5080, -539.8220], [159.2640, -541.6350],
        [157.1380, -542.1320], [155.2880, -542.5160], [143.6590, -544.5820], [140.4350, -545.0180], [137.7880, -545.2600],
        [135.0710, -545.3920], [128.1730, -545.5710], [121.4430, -546.0490], [117.6740, -546.1950], [112.7910, -546.2280],
        [88.9770, -546.2300], [87.3920, -544.6660], [87.3920, -88.9610], [88.9770, -87.3970], [269.5520, -87.3820],
        [269.9420, -87.3440], [270.4950, -87.1460], [270.8210, -86.9290], [271.0980, -86.6510], [271.4000, -86.1480],
        [271.5130, -85.7730], [271.5520, -85.3820], [271.5520, -53.5720], [271.5130, -53.1820], [271.4000, -52.8070],
        [271.2150, -52.4610], [270.9660, -52.1580], [270.6630, -51.9090], [270.3170, -51.7240], [269.9420, -51.6100],
        [269.5520, -51.5720], [263.5520, -51.5720], [259.6500, -51.5200], [95.8780, -51.7230], [90.3270, -51.8030],
        [88.2990, -51.9170], [86.6540, -52.0780], [85.3720, -52.2590], [84.1220, -52.4880], [82.9050, -52.7650],
        [81.4270, -53.1740], [79.9850, -53.6450], [78.5650, -54.1670], [75.7420, -55.3600], [73.4910, -56.4970],
        [71.2810, -57.8210], [68.8780, -59.4970], [66.3180, -61.5090], [64.3730, -63.2100], [62.5630, -65.0200],
        [61.7130, -65.9710], [60.6970, -67.2000], [58.9750, -69.4980], [57.3880, -71.8790], [55.9650, -74.3270],
        [54.7360, -76.8210], [54.1340, -78.2200], [53.5820, -79.6300], [52.9880, -81.3500], [52.5590, -82.8220],
        [52.1350, -84.6520], [51.8650, -86.2340], [51.6700, -87.8650], [51.5240, -89.8780], [51.4520, -91.9350],
        [51.4180, -95.0640], [51.4690, -542.2060], [51.5480, -545.3080], [51.7450, -547.9900], [51.9080, -549.2910],
        [52.1200, -550.5610], [52.3820, -551.7970], [52.6930, -552.9990], [53.0490, -554.1680], [53.5520, -555.5910],
        [54.1080, -556.9810], [54.8390, -558.6200], [55.5010, -559.9690], [56.2130, -561.3040], [56.9790, -562.6260],
        [57.8000, -563.9380], [58.6780, -565.2390], [59.6190, -566.5290], [60.6270, -567.8000], [61.4840, -568.7970],
        [63.3200, -570.7130], [64.2870, -571.6230], [65.5300, -572.7120], [67.8430, -574.5320], [70.2460, -576.1720],
        [71.6110, -576.9970], [72.7120, -577.6090], [73.8190, -578.1760], [75.2100, -578.8230], [77.7430, -579.8390],
        [79.1730, -580.3360], [80.6290, -580.7870], [82.1200, -581.1820], [83.3440, -581.4520], [84.5970, -581.6770],
        [85.8810, -581.8550], [87.1940, -581.9880], [88.8730, -582.0970], [91.2740, -582.1710], [95.1060, -582.1990],
        [129.0410, -582.1800], [131.8010, -582.1100], [134.1760, -581.9780], [141.8540, -581.3390], [144.1600, -581.1090],
        [146.7360, -580.7590], [152.7470, -579.7550], [159.4370, -578.7210], [162.2270, -578.1650], [171.0490, -576.1180],
        [173.4410, -575.5030], [180.2420, -573.6460], [183.1560, -572.7620], [187.4470, -571.3350], [195.6570, -568.3870],
        [198.7880, -567.1760], [203.8300, -565.1100], [207.1170, -563.6930], [209.8420, -562.4400], [213.9330, -560.4370],
        [218.8320, -557.9450], [222.8920, -555.7880], [226.4380, -553.8130], [229.7590, -551.8750], [232.5440, -550.1540],
        [239.9660, -545.3570], [243.1560, -543.1840], [246.5350, -540.6770], [254.0000, -534.8750], [257.3190, -532.2330],
        [260.7720, -529.3900], [263.3990, -527.1320], [265.5490, -525.1460], [275.8590, -514.8740], [278.6790, -511.8590],
        [285.0340, -504.5940], [287.1280, -502.0350], [289.5390, -498.9410], [292.6580, -494.7930], [294.9450, -491.6200],
        [298.2800, -486.7500], [300.9980, -482.6530], [303.4800, -478.7860], [305.2950, -475.7510], [307.2730, -472.1920],
        [309.3160, -468.3800], [312.7890, -461.6020], [314.2390, -458.6300], [315.7070, -455.3790], [318.4710, -449.0490],
        [320.1850, -444.7770], [321.7170, -440.7720], [323.4400, -435.9340], [324.5600, -432.4860], [326.5720, -425.7850],
        [328.6010, -418.3690], [329.0580, -416.5690], [329.4690, -414.7380], [330.4260, -409.7700], [331.3960, -405.1600],
        [331.8080, -402.9790], [332.1850, -400.4230], [333.0270, -393.2590], [334.1310, -385.2010], [334.3610, -383.2390],
        [334.5410, -381.2460], [334.6710, -378.8730], [334.7340, -376.1100], [334.7440, -363.2900], [334.6570, -362.7090],
        [334.5070, -362.3470], [334.2900, -362.0210], [334.0120, -361.7440], [333.5090, -361.4420], [333.1340, -361.3280],
        [332.7440, -361.2900], [300.8900, -361.2900], [300.5000, -361.3280], [300.1250, -361.4420], [299.7790, -361.6270],
        [299.3440, -362.0210], [299.0430, -362.5250], [298.9760, -362.7090], [298.9000, -363.0940], [298.8730, -367.5260],
        [298.7740, -370.6280], [298.6500, -372.6630], [298.2740, -377.3550], [297.8580, -383.7560], [297.5930, -386.0380],
        [296.8090, -391.1370], [295.9510, -397.5810], [295.5950, -399.7950], [295.2380, -401.6580], [293.2900, -410.1710],
        [292.7720, -412.2700]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240]
    ], convexity = 30);
    polygon(points = [
        [361.5860, -86.3250], [361.9360, -86.7960], [362.4070, -87.1460], [362.9600, -87.3440], [363.3500, -87.3820],
        [544.6480, -87.3970], [546.2330, -88.9610], [546.2320, -114.5030], [546.1680, -119.7150], [546.0390, -122.4400],
        [545.5800, -128.8250], [545.3880, -135.3590], [545.2900, -137.3960], [545.0270, -140.3770], [544.6410, -143.2810],
        [542.6800, -154.6170], [542.2080, -157.1060], [541.6620, -159.5450], [540.3300, -164.9870], [539.3800, -168.5700],
        [537.1000, -175.8190], [535.3530, -180.7390], [534.1380, -183.9310], [532.8830, -187.0550], [531.5850, -190.1340],
        [530.3470, -192.9030], [527.5960, -198.6380], [525.6880, -202.4400], [524.2890, -205.1300], [521.5000, -210.1440],
        [520.2620, -212.2360], [518.9560, -214.3240], [514.1670, -221.5130], [511.8900, -224.7080], [505.9030, -232.4090],
        [503.8980, -234.8650], [501.8630, -237.2540], [500.3600, -238.9220], [498.7590, -240.5970], [488.7670, -250.5880],
        [485.9460, -253.1970], [480.4000, -257.9760], [477.8550, -260.0740], [475.2770, -262.0930], [472.9410, -263.8300],
        [470.3400, -265.6690], [468.2420, -267.0820], [466.3550, -268.2560], [464.6800, -269.1900], [462.9530, -270.0510],
        [461.3800, -271.2700], [460.0400, -272.2360], [458.3980, -273.3250], [456.7340, -274.3430], [452.5850, -276.6630],
        [446.0530, -280.0740], [442.4030, -281.8230], [436.0420, -284.6220], [431.2620, -286.5510], [427.0570, -288.1120],
        [421.0430, -290.1040], [413.1760, -292.4370], [410.4960, -293.1250], [402.6030, -294.9460], [400.1310, -295.4480],
        [397.6020, -295.8640], [391.1650, -296.7250], [386.0890, -297.5080], [383.4900, -297.7990], [376.7380, -298.1810],
        [370.3610, -298.6480], [367.9630, -298.7360], [364.8380, -298.7760], [127.0110, -298.8020], [123.8740, -298.8190],
        [121.8400, -298.8710], [116.0390, -298.8710], [115.6490, -298.9100], [115.0960, -299.1080], [114.7700, -299.3250],
        [114.4930, -299.6030], [114.2750, -299.9290], [114.1250, -300.2910], [114.0390, -300.8710], [114.0390, -332.7630],
        [114.0780, -333.1530], [114.1920, -333.5280], [114.3760, -333.8740], [114.6250, -334.1770], [114.9280, -334.4260],
        [115.2740, -334.6100], [115.6490, -334.7240], [116.0390, -334.7630], [372.0800, -334.8380], [378.0000, -334.7850],
        [380.0520, -334.7030], [382.0670, -334.5610], [385.6760, -334.1590], [394.3820, -332.9760], [400.8960, -332.2180],
        [402.8110, -331.9320], [404.9970, -331.5250], [409.9140, -330.4630], [415.5160, -329.3430], [418.5590, -328.6280],
        [426.2860, -326.5390], [432.4010, -324.6990], [434.9940, -323.8730], [441.2600, -321.6570], [447.8410, -319.0910],
        [452.3210, -317.1830], [456.9610, -315.1340], [459.3980, -314.0070], [466.4260, -310.4610], [470.2330, -308.4410],
        [472.4030, -307.2030], [479.3970, -303.0860], [482.5810, -301.1450], [486.0090, -298.9200], [490.8370, -295.6400],
        [493.7690, -293.5570], [496.6360, -291.4070], [502.3040, -287.0000], [504.8720, -284.9350], [510.4570, -280.1040],
        [512.9750, -277.8360], [514.6920, -276.1810], [522.5200, -268.3980], [524.5600, -266.2990], [526.1620, -264.5500],
        [530.5060, -259.5320], [532.8320, -256.7460], [535.0830, -253.9200], [541.0790, -246.1980], [543.0040, -243.5990],
        [544.8320, -240.9540], [549.8090, -233.2800], [551.7210, -230.2170], [553.8280, -226.6170], [555.8020, -223.0730],
        [558.0990, -218.7410], [560.4490, -214.1170], [562.3230, -210.3040], [563.8390, -207.0470], [565.3980, -203.5160],
        [566.7740, -200.1690], [568.1910, -196.4560], [570.7470, -189.3700], [572.2010, -185.1010], [573.2190, -181.9300],
        [576.0420, -171.8950], [578.4910, -161.2630], [578.8850, -159.0690], [579.7130, -153.3060], [580.8110, -146.6480],
        [581.0770, -144.7090], [581.3190, -142.4030], [582.0300, -133.7150], [582.1410, -131.3290], [582.1950, -128.5610],
        [582.2040, -93.2360], [582.1040, -89.0960], [581.9910, -87.4140], [581.8540, -86.0970], [581.6720, -84.8080],
        [581.4430, -83.5500], [580.8550, -81.1230], [580.0230, -78.5080], [579.0390, -75.9650], [578.0100, -73.7370],
        [576.8060, -71.5270], [575.4330, -69.3430], [573.9060, -67.2120], [572.2180, -65.1680], [570.6140, -63.4750],
        [568.9160, -61.8860], [566.8930, -60.2010], [564.5260, -58.4570], [562.3480, -57.0430], [560.1300, -55.7880],
        [557.8930, -54.7170], [555.9210, -53.9140], [553.9100, -53.2220], [552.1280, -52.7270], [550.2750, -52.3360],
        [548.3490, -52.0520], [546.3560, -51.8710], [543.9690, -51.7630], [541.1930, -51.7190], [372.8630, -51.5400],
        [369.0550, -51.6450], [367.7000, -51.7530], [366.3730, -51.9240], [365.6800, -52.0490], [363.1540, -52.0590],
        [362.7690, -52.1360], [362.4070, -52.2860], [361.9360, -52.6350], [361.6870, -52.9380], [361.5020, -53.2840],
        [361.3880, -53.6590], [361.3500, -54.0490], [361.3500, -85.3820], [361.3880, -85.7720]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203]
    ], convexity = 30);
    polygon(points = [
        [300.6680, 24.0010], [300.2840, 23.9250], [299.9210, 23.7750], [299.5950, 23.5570], [299.3180, 23.2800],
        [299.1000, 22.9540], [298.9500, 22.5920], [298.8640, 22.0110], [298.8650, -257.6500], [298.8950, -262.5300],
        [298.9450, -263.5390], [298.9550, -269.7350], [299.0310, -270.1200], [299.1810, -270.4820], [299.5310, -270.9530],
        [300.0020, -271.3030], [300.3650, -271.4530], [300.7490, -271.5290], [332.8810, -271.5290], [333.4500, -271.3870],
        [333.7960, -271.2020], [334.0990, -270.9530], [334.4480, -270.4820], [334.6460, -269.9290], [334.6850, -269.5390],
        [334.6850, -263.5390], [334.7300, -262.5300], [334.7600, -255.9010], [334.7510, 22.2070], [334.6740, 22.5920],
        [334.5240, 22.9540], [334.1750, 23.4250], [333.8720, 23.6740], [333.5260, 23.8590], [332.9570, 24.0010]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34]
    ], convexity = 30);
    polygon(points = [
        [453.7020, 276.1900], [457.6580, 273.9530], [461.8700, 271.3670], [466.6620, 268.2810], [470.8370, 265.4320],
        [474.4710, 262.8060], [477.3130, 260.6070], [480.1300, 258.3060], [484.7140, 254.3950], [487.2330, 252.1340],
        [489.1920, 250.2410], [498.0160, 241.4450], [500.4070, 238.9300], [502.7270, 236.3110], [505.9090, 232.5130],
        [508.9510, 228.7130], [511.8950, 224.8540], [514.1280, 221.7510], [516.9230, 217.5650], [519.6690, 213.2680],
        [521.9050, 209.5060], [524.1200, 205.5240], [526.9270, 200.1770], [528.6450, 196.7170], [530.9950, 191.5470],
        [532.8980, 187.0740], [534.7110, 182.5010], [536.5230, 177.5620], [538.0440, 172.9400], [539.5590, 167.9880],
        [540.1900, 165.5960], [541.6710, 159.5490], [542.4610, 155.8740], [544.5960, 143.6320], [545.0280, 140.4170],
        [545.2910, 137.4370], [545.3890, 135.4000], [545.5800, 128.8640], [546.0610, 122.1390], [546.1960, 118.7160],
        [546.2350, 113.8370], [546.2360, 88.9860], [544.6720, 87.4000], [88.9520, 87.4000], [87.3880, 88.9860],
        [87.3740, 269.5520], [87.3360, 269.9420], [87.1380, 270.4950], [86.9200, 270.8210], [86.6430, 271.0980],
        [86.3170, 271.3160], [85.9550, 271.4660], [85.3740, 271.5520], [53.4920, 271.5520], [53.1020, 271.5130],
        [52.7260, 271.4000], [52.3810, 271.2150], [52.0780, 270.9660], [51.8290, 270.6630], [51.6440, 270.3170],
        [51.5300, 269.9420], [51.4920, 269.5520], [51.4890, 95.7000], [51.5100, 92.5640], [51.5720, 90.1540],
        [51.6920, 88.1320], [51.8620, 86.4930], [52.0510, 85.2170], [52.2880, 83.9730], [52.5730, 82.7610],
        [52.9920, 81.2890], [53.8960, 78.7200], [54.4710, 77.3170], [55.1000, 75.9220], [56.3850, 73.4350],
        [57.8660, 71.0000], [59.5200, 68.6340], [60.5010, 67.3580], [61.5190, 66.1170], [62.5740, 64.9180],
        [63.4480, 63.9940], [65.2890, 62.2360], [67.5010, 60.3830], [68.7800, 59.4070], [70.0850, 58.4750],
        [72.4930, 56.9270], [74.6850, 55.7070], [77.1910, 54.5210], [79.7320, 53.5100], [81.4650, 52.9300],
        [82.9530, 52.5160], [84.8010, 52.1130], [86.3980, 51.8620], [88.0410, 51.6850], [90.0650, 51.5580],
        [94.9140, 51.4720], [542.0920, 51.4220], [545.1940, 51.5040], [546.8800, 51.6110], [548.2010, 51.7410],
        [549.4930, 51.9190], [550.7520, 52.1440], [551.9780, 52.4180], [553.1730, 52.7370], [554.3390, 53.0990],
        [555.7680, 53.6040], [557.1780, 54.1660], [558.5800, 54.7890], [559.9770, 55.4810], [561.0920, 56.0860],
        [562.4780, 56.9040], [563.8510, 57.7820], [566.2680, 59.4930], [567.5670, 60.5200], [568.5770, 61.3850],
        [570.5050, 63.2260], [571.4180, 64.1930], [572.5080, 65.4350], [574.3330, 67.7470], [575.9840, 70.1580],
        [576.8210, 71.5370], [577.4450, 72.6600], [578.5630, 74.9550], [579.6270, 77.5990], [580.1440, 79.0840],
        [580.6090, 80.5830], [581.0150, 82.1040], [581.2900, 83.3450], [581.5180, 84.6100], [581.6990, 85.9040],
        [581.8320, 87.2240], [581.9420, 88.9090], [582.0160, 91.3140], [582.0430, 94.7970], [582.0220, 128.7230],
        [581.9570, 131.4850], [581.8320, 133.8630], [581.1980, 141.5430], [580.9740, 143.8520], [580.6320, 146.4320],
        [579.5830, 152.7610], [578.5470, 159.7970], [578.1120, 161.9640], [577.1060, 166.2000], [575.9590, 171.3890],
        [575.3420, 173.7830], [574.1750, 177.9120], [573.2260, 181.1350], [572.1100, 184.5980], [570.1570, 190.3920],
        [568.3630, 195.4200], [567.0080, 198.9120], [565.5090, 202.5710], [563.9620, 206.1140], [562.3360, 209.6410],
        [560.2000, 213.9980], [557.7140, 218.8840], [555.5590, 222.9340], [553.5790, 226.4760], [551.6350, 229.7990],
        [549.9090, 232.5850], [545.1110, 240.0020], [543.1200, 242.9260], [540.6190, 246.3050], [535.2230, 253.2530],
        [532.5890, 256.5810], [529.9370, 259.8110], [527.6850, 262.4300], [525.5170, 264.7940], [519.6060, 270.9150],
        [516.6050, 273.9350], [514.1920, 276.2770], [512.2260, 278.1000], [505.0240, 284.3970], [502.7250, 286.2710],
        [497.3180, 290.4900], [494.7260, 292.4630], [492.3550, 294.1940], [488.8610, 296.6170], [484.3490, 299.6560],
        [480.4390, 302.1890], [477.8220, 303.7830], [475.1430, 305.2350], [472.1060, 306.6720], [469.4980, 308.3860],
        [466.8220, 309.9120], [461.4120, 312.7170], [458.1530, 314.3330], [454.2840, 316.1120], [449.7780, 318.0460],
        [444.0580, 320.3340], [440.0480, 321.8570], [435.4900, 323.4750], [432.3220, 324.5020], [425.9040, 326.4430],
        [419.3610, 328.2300], [417.2530, 328.7670], [415.4150, 329.1860], [409.8150, 330.3140], [404.9040, 331.3850],
        [402.7160, 331.7960], [400.1500, 332.1690], [393.6250, 332.9400], [384.9060, 334.1400], [381.2720, 334.5160],
        [378.8960, 334.6510], [376.1300, 334.7180], [363.2900, 334.7410], [362.7090, 334.6550], [362.3470, 334.5050],
        [362.0210, 334.2870], [361.6270, 333.8520], [361.3760, 333.3210], [361.2900, 332.7410], [361.2900, 300.8490],
        [361.3280, 300.4590], [361.5260, 299.9070], [361.8760, 299.4350], [362.1790, 299.1860], [362.7090, 298.9350],
        [363.0940, 298.8590], [367.7370, 298.8390], [370.8340, 298.7460], [377.5560, 298.2590], [383.6210, 297.8730],
        [385.9060, 297.6150], [391.3230, 296.7850], [397.4520, 295.9750], [399.6700, 295.6220], [401.5350, 295.2670],
        [410.0450, 293.3200], [412.1460, 292.8050], [414.7930, 292.0640], [421.7780, 289.9650], [426.6500, 288.3490],
        [430.3110, 287.0200], [435.9090, 284.8180], [440.6730, 282.7810], [443.9830, 281.2330], [447.7840, 279.3030]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239]
    ], convexity = 30);
    polygon(points = [
        [262.5280, 298.8970], [263.5390, 298.9420], [269.5390, 298.9420], [269.9290, 298.9800], [270.4820, 299.1780],
        [270.9530, 299.5280], [271.3030, 299.9990], [271.5010, 300.5520], [271.5390, 300.9420], [271.5390, 332.6800],
        [271.5010, 333.0700], [271.3870, 333.4450], [271.0850, 333.9490], [270.8080, 334.2260], [270.4820, 334.4440],
        [269.9290, 334.6410], [269.5390, 334.6800], [263.5390, 334.6800], [262.5280, 334.7300], [257.6480, 334.7600],
        [-22.0110, 334.7610], [-22.5920, 334.6750], [-22.9540, 334.5250], [-23.2800, 334.3070], [-23.5570, 334.0300],
        [-23.7750, 333.7040], [-23.9250, 333.3420], [-24.0010, 332.9570], [-24.0010, 300.6700], [-23.9250, 300.2850],
        [-23.7750, 299.9230], [-23.4250, 299.4520], [-22.9540, 299.1020], [-22.5920, 298.9520], [-22.2070, 298.8760],
        [255.8980, 298.8660]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
    ], convexity = 30);
    polygon(points = [
        [333.4940, 114.2750], [333.8200, 114.4930], [334.2140, 114.9280], [334.4650, 115.4590], [334.5510, 116.0390],
        [334.7250, 369.5200], [334.6920, 377.1960], [334.5540, 380.6130], [334.2870, 383.6040], [333.9640, 386.2070],
        [332.9040, 393.9370], [332.0130, 401.4160], [331.4720, 404.5640], [330.4380, 409.4920], [329.4780, 414.4700],
        [328.9250, 416.9090], [326.9230, 424.3320], [326.0810, 427.2720], [324.0400, 433.9470], [322.4710, 438.5020],
        [320.8870, 442.7840], [318.5050, 448.7800], [315.2560, 456.2240], [313.5180, 460.0310], [311.6370, 463.8310],
        [309.0750, 468.6910], [305.7950, 474.6790], [303.8600, 477.9820], [300.4990, 483.2260], [296.8480, 488.6650],
        [294.0400, 492.7000], [290.9530, 496.8830], [287.9860, 500.7530], [285.2950, 504.0840], [283.1210, 506.6110],
        [278.2840, 512.0730], [276.4260, 514.0260], [268.0380, 522.5590], [265.5630, 524.9410], [262.9280, 527.3160],
        [258.9850, 530.6590], [254.7150, 534.1110], [247.8270, 539.5550], [243.7570, 542.5550], [239.7640, 545.2690],
        [232.0430, 550.2220], [230.6320, 551.0570], [229.2040, 551.8410], [226.2950, 553.2560], [224.7440, 554.3070],
        [223.4340, 555.1360], [221.8420, 556.0730], [219.9630, 557.1060], [216.9840, 558.6620], [213.1700, 560.5820],
        [210.1730, 562.0490], [207.7210, 563.1910], [203.3370, 565.0860], [196.8600, 567.7050], [189.7790, 570.2990],
        [185.2320, 571.8620], [180.8980, 573.2400], [172.3350, 575.6490], [170.5330, 576.1010], [166.2650, 577.0550],
        [161.7230, 578.1320], [158.9140, 578.6580], [152.8240, 579.5380], [146.8110, 580.5390], [144.8870, 580.8140],
        [142.9270, 581.0350], [133.5840, 581.8140], [131.1990, 581.9300], [128.0830, 581.9900], [92.4030, 582.0010],
        [89.9820, 581.9540], [88.2780, 581.8760], [86.6080, 581.7420], [85.3000, 581.5850], [83.7050, 581.3220],
        [82.1510, 580.9840], [80.6300, 580.5780], [79.1310, 580.1130], [77.3490, 579.4860], [75.5840, 578.7840],
        [74.1330, 578.1330], [72.7040, 577.4140], [71.2980, 576.6290], [69.6410, 575.6050], [68.2860, 574.6880],
        [66.9590, 573.7140], [65.6690, 572.6780], [64.6670, 571.8040], [63.4570, 570.6590], [62.3000, 569.4620],
        [61.1990, 568.2270], [59.9510, 566.7040], [58.9710, 565.4040], [57.8690, 563.8070], [57.0130, 562.4530],
        [56.0690, 560.8160], [55.2130, 559.1750], [54.4410, 557.5310], [53.7440, 555.8730], [53.2220, 554.4650],
        [52.7620, 553.0170], [52.3710, 551.5200], [52.1140, 550.2830], [51.8610, 548.6890], [51.6840, 547.0470],
        [51.5720, 545.3640], [51.4890, 542.6140], [51.4650, 537.7300], [51.4880, 373.6380], [51.5130, 370.5040],
        [51.5850, 368.4550], [51.7390, 366.8190], [51.9560, 365.6800], [51.9650, 363.1540], [52.0420, 362.7690],
        [52.1920, 362.4070], [52.5420, 361.9360], [53.0130, 361.5860], [53.5660, 361.3880], [53.9560, 361.3500],
        [85.3740, 361.3500], [85.7640, 361.3880], [86.1390, 361.5020], [86.6430, 361.8040], [86.9200, 362.0810],
        [87.1380, 362.4070], [87.3350, 362.9600], [87.3740, 363.3500], [87.3880, 544.6410], [88.9520, 546.2270],
        [113.1190, 546.2260], [117.9990, 546.1860], [121.4230, 546.0480], [128.1530, 545.5690], [135.7360, 545.3650],
        [137.7670, 545.2570], [139.4290, 545.1190], [142.0320, 544.8140], [144.5850, 544.4270], [154.9700, 542.6070],
        [157.1430, 542.1840], [159.5730, 541.6180], [167.3770, 539.5880], [172.6870, 538.0660], [176.7470, 536.7820],
        [180.7090, 535.3620], [185.9950, 533.2990], [191.0100, 531.1890], [194.8700, 529.4150], [198.6830, 527.5440],
        [205.9730, 523.7580], [209.6970, 521.7340], [212.3260, 520.1980], [215.2290, 518.3810], [220.0750, 515.2100],
        [222.9980, 513.1720], [225.8500, 511.0230], [232.2440, 506.0210], [234.9270, 503.8080], [237.7510, 501.3560],
        [240.3970, 498.9530], [242.8610, 496.5910], [251.4980, 487.7760], [253.1350, 486.0280], [255.1030, 483.8180],
        [257.0780, 481.5260], [258.8800, 479.3480], [261.0910, 476.5680], [262.8650, 474.2440], [264.5670, 471.9040],
        [266.3750, 469.2970], [267.4190, 467.7090], [268.4120, 466.0780], [269.1870, 464.6780], [270.0490, 462.9490],
        [271.4490, 461.1180], [272.7530, 459.2530], [273.9460, 457.3720], [275.2010, 455.2280], [276.8100, 452.2870],
        [279.6290, 446.8980], [281.0040, 444.1840], [282.0550, 441.9880], [283.4230, 438.9250], [284.8390, 435.5570],
        [286.5000, 431.3570], [287.6590, 428.2810], [288.7420, 425.1550], [290.0560, 421.1330], [292.5560, 412.6730],
        [293.1570, 410.2810], [294.9110, 402.6880], [295.3590, 400.5290], [295.6890, 398.6420], [296.0190, 396.4060],
        [296.6950, 391.2430], [297.4800, 386.1480], [297.7510, 383.8720], [297.9080, 381.8710], [298.1910, 377.1400],
        [298.5990, 371.7750], [298.6960, 369.7300], [298.7500, 367.3110], [298.8150, 126.5370], [298.8370, 123.4010],
        [298.8870, 121.8400], [298.8870, 116.0390], [298.9260, 115.6490], [299.0400, 115.2740], [299.2240, 114.9280],
        [299.6190, 114.4930], [299.9450, 114.2750], [300.3070, 114.1250], [300.8870, 114.0390], [332.5510, 114.0390],
        [332.9410, 114.0780]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220]
    ], convexity = 30);
    polygon(points = [
        [-249.0260, -490.4950], [-251.0770, -488.4050], [-252.4830, -486.8990], [-254.0840, -485.0930], [-257.6350, -480.9690],
        [-259.5380, -478.6910], [-261.5850, -476.1230], [-263.3500, -473.7920], [-265.2160, -471.1970], [-267.1900, -468.3420],
        [-269.3030, -465.1610], [-271.5610, -461.6200], [-273.2690, -458.8410], [-274.9040, -456.0450], [-276.5870, -452.9990],
        [-278.8890, -448.6390], [-280.5650, -445.3880], [-281.9010, -442.6540], [-283.1590, -439.8790], [-284.5900, -436.5180],
        [-285.7150, -433.7120], [-286.9890, -430.3470], [-288.0910, -427.2380], [-290.1300, -421.2510], [-292.4810, -413.3940],
        [-293.1730, -410.7150], [-294.8490, -403.4260], [-295.2990, -401.2670], [-295.6280, -399.3760], [-296.6650, -391.9580],
        [-297.5210, -386.5530], [-297.8030, -384.2850], [-297.9850, -381.9520], [-298.2510, -376.8630], [-298.6780, -371.1600],
        [-298.7750, -369.1170], [-298.8310, -366.6990], [-298.8330, -126.3400], [-298.8590, -123.2080], [-298.9110, -121.8400],
        [-298.9110, -116.0390], [-298.9490, -115.6490], [-299.1470, -115.0960], [-299.3650, -114.7700], [-299.6420, -114.4930],
        [-299.9680, -114.2750], [-300.3300, -114.1250], [-300.9110, -114.0390], [-332.7800, -114.0390], [-333.1700, -114.0780],
        [-333.5450, -114.1920], [-333.8910, -114.3760], [-334.3260, -114.7700], [-334.5430, -115.0960], [-334.6940, -115.4590],
        [-334.7800, -116.0390], [-334.6450, -371.3530], [-334.5850, -377.2700], [-334.4990, -379.3210], [-334.3560, -381.3370],
        [-333.9340, -385.2870], [-332.7530, -394.3450], [-332.0330, -400.5370], [-331.7540, -402.4570], [-331.4150, -404.3380],
        [-329.1900, -414.7990], [-328.4030, -418.1410], [-326.4470, -425.6240], [-324.1660, -433.1980], [-323.4130, -435.4930],
        [-321.2720, -441.4720], [-320.2810, -444.0470], [-318.2220, -449.1730], [-315.3270, -455.7780], [-314.0960, -458.4900],
        [-313.0510, -460.6500], [-309.7700, -467.0750], [-308.2820, -469.8510], [-305.0220, -475.6030], [-302.7140, -480.1370],
        [-301.8660, -481.6110], [-300.9370, -483.0610], [-295.3870, -491.1570], [-292.7250, -494.8640], [-288.2050, -500.8160],
        [-286.3590, -503.1310], [-284.6560, -505.1740], [-279.1140, -511.5130], [-276.5570, -514.2450], [-269.1050, -521.7350],
        [-266.7310, -524.0740], [-264.0260, -526.6140], [-261.4650, -528.8640], [-258.3070, -531.5010], [-255.0080, -534.1510],
        [-247.2870, -540.1620], [-244.4390, -542.3140], [-242.6040, -543.6270], [-240.4740, -545.0700], [-231.9420, -550.5710],
        [-228.8760, -552.4320], [-225.2950, -554.4900], [-222.0340, -556.2790], [-218.2440, -558.2750], [-213.8830, -560.4830],
        [-210.0600, -562.3560], [-206.5290, -563.9870], [-202.9940, -565.5330], [-199.9210, -566.7840], [-196.7820, -567.9830],
        [-189.6930, -570.5430], [-185.9940, -571.8140], [-181.0690, -573.3880], [-171.8780, -575.9580], [-170.0640, -576.3930],
        [-162.4330, -578.0880], [-159.6450, -578.6450], [-152.9590, -579.6760], [-146.2990, -580.7780], [-144.3550, -581.0370],
        [-142.0430, -581.2720], [-134.0210, -581.9310], [-131.6410, -582.0540], [-129.2240, -582.1120], [-94.5800, -582.1220],
        [-91.1000, -582.0880], [-88.3660, -581.9850], [-86.3720, -581.8190], [-84.4400, -581.5510], [-82.5690, -581.1750],
        [-80.4460, -580.6100], [-78.0620, -579.8240], [-75.9970, -579.0280], [-73.9640, -578.1150], [-71.9760, -577.0710],
        [-70.0320, -575.9010], [-68.1340, -574.6180], [-66.2950, -573.2200], [-64.5330, -571.6990], [-62.8680, -570.0650],
        [-61.3090, -568.3460], [-59.8590, -566.5640], [-58.3330, -564.4590], [-56.9530, -562.2960], [-55.7320, -560.1090],
        [-54.6640, -557.9180], [-53.7330, -555.7060], [-53.0340, -553.7120], [-52.4660, -551.6300], [-52.0960, -549.7620],
        [-51.8050, -547.4890], [-51.6790, -545.8130], [-51.6080, -544.1040], [-51.5520, -538.8850], [-51.5280, -372.6100],
        [-51.5860, -369.1500], [-51.7310, -367.1560], [-51.8720, -366.2150], [-51.9980, -365.6800], [-51.9980, -363.3500],
        [-52.0370, -362.9600], [-52.2340, -362.4070], [-52.4520, -362.0810], [-52.7300, -361.8040], [-53.2330, -361.5020],
        [-53.6080, -361.3880], [-53.9980, -361.3500], [-85.3970, -361.3500], [-85.7870, -361.3880], [-86.1620, -361.5020],
        [-86.6650, -361.8040], [-86.9430, -362.0810], [-87.1600, -362.4070], [-87.3580, -362.9600], [-87.3970, -363.3500],
        [-87.4110, -544.6410], [-88.9750, -546.2260], [-113.1220, -546.2340], [-117.9990, -546.1960], [-121.4200, -546.0600],
        [-128.1440, -545.5830], [-135.7220, -545.3830], [-139.0860, -545.1720], [-141.6990, -544.8800], [-144.2590, -544.5040],
        [-156.5130, -542.3470], [-159.2580, -541.7340], [-166.7920, -539.8470], [-170.3440, -538.8640], [-175.5610, -537.2230],
        [-179.3170, -535.9190], [-184.5380, -533.9460], [-189.8960, -531.7390], [-193.7770, -529.9980], [-197.8760, -528.0250],
        [-204.8890, -524.4070], [-208.8910, -522.2670], [-211.7830, -520.6090], [-214.3960, -518.9920], [-221.0460, -514.5720],
        [-223.4640, -512.8980], [-226.0860, -510.9450], [-231.9840, -506.3500], [-234.9430, -503.9460], [-237.5700, -501.7040],
        [-239.2400, -500.1890], [-240.9150, -498.5770]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206]
    ], convexity = 30);
    polygon(points = [
        [-65.6610, 572.7970], [-67.7140, 574.4220], [-69.5710, 575.7300], [-71.7500, 577.0840], [-73.9660, 578.2740],
        [-76.2150, 579.3060], [-78.5140, 580.2040], [-80.5860, 580.8780], [-82.7300, 581.4180], [-84.9500, 581.8100],
        [-87.2460, 582.0620], [-89.9540, 582.2070], [-93.7670, 582.2640], [-129.1000, 582.2520], [-131.8600, 582.1830],
        [-134.2360, 582.0540], [-143.5760, 581.2600], [-146.8210, 580.8360], [-152.8400, 579.8330], [-158.5770, 578.9600],
        [-160.4630, 578.6300], [-162.6220, 578.1810], [-170.2690, 576.4800], [-172.6800, 575.8830], [-181.2680, 573.4600],
        [-183.5990, 572.7340], [-189.5980, 570.7050], [-195.2520, 568.6710], [-198.9730, 567.2830], [-203.1840, 565.5800],
        [-210.3240, 562.4880], [-212.3330, 561.7100], [-214.3940, 560.9990], [-216.4800, 559.6040], [-218.3370, 558.4730],
        [-225.6440, 554.4250], [-230.3490, 551.6810], [-233.4160, 549.7590], [-240.8290, 544.9490], [-244.0120, 542.7560],
        [-247.3350, 540.3160], [-249.5290, 538.6140], [-256.7350, 532.8770], [-260.4550, 529.8130], [-263.5390, 527.1200],
        [-266.1660, 524.6510], [-272.5250, 518.4730], [-275.6360, 515.3230], [-277.8960, 512.9270], [-285.0530, 504.7730],
        [-286.7420, 502.7270], [-288.5760, 500.4070], [-292.8890, 494.7000], [-295.5510, 490.9790], [-300.4420, 483.8480],
        [-301.9400, 481.5270], [-302.9340, 479.7460], [-304.2870, 477.0180], [-305.0770, 475.5030], [-308.1750, 470.0600],
        [-309.6700, 467.2880], [-312.8180, 461.1760], [-314.0070, 458.7500], [-315.4880, 455.4990], [-318.3900, 448.8800],
        [-319.7730, 445.4640], [-321.3320, 441.4570], [-322.7830, 437.4640], [-323.8640, 434.3290], [-326.4480, 425.8980],
        [-328.8090, 417.2860], [-329.5060, 414.2380], [-330.4080, 409.5760], [-331.5110, 404.3450], [-331.9010, 402.1440],
        [-332.2130, 399.8920], [-332.9010, 394.0220], [-334.0110, 385.6080], [-334.3140, 382.9860], [-334.5280, 380.6590],
        [-334.6680, 378.2870], [-334.7420, 375.5260], [-334.7750, 363.2900], [-334.7370, 362.9000], [-334.5390, 362.3470],
        [-334.3210, 362.0210], [-334.0440, 361.7440], [-333.7180, 361.5260], [-333.3560, 361.3760], [-332.7750, 361.2900],
        [-300.9570, 361.2900], [-300.5670, 361.3280], [-300.1920, 361.4420], [-299.8460, 361.6270], [-299.4110, 362.0210],
        [-299.1930, 362.3470], [-299.1100, 362.5250], [-299.0430, 362.7090], [-298.9670, 363.0940], [-298.9410, 366.7360],
        [-298.8240, 369.8380], [-298.2820, 376.9020], [-298.0110, 381.9930], [-297.8570, 383.9960], [-297.5830, 386.2710],
        [-296.6780, 391.9990], [-295.7390, 398.7750], [-295.3680, 400.9850], [-294.9930, 402.8380], [-293.2510, 410.4340],
        [-292.6460, 412.8240], [-290.5010, 420.1260], [-288.9220, 425.0200], [-287.4290, 429.2730], [-285.0340, 435.4240],
        [-282.8930, 440.4690], [-281.0830, 444.3290], [-277.6010, 451.0800], [-275.4500, 455.0770], [-273.3120, 458.7590],
        [-270.5090, 463.2530], [-267.3760, 468.0380], [-264.1050, 472.7220], [-261.3870, 476.3460], [-257.9750, 480.6030],
        [-254.7560, 484.3640], [-252.1700, 487.1940], [-243.5470, 495.9930], [-240.5790, 498.9060], [-237.5010, 501.7080],
        [-233.5730, 505.0480], [-229.3020, 508.4980], [-225.1890, 511.6550], [-221.8270, 514.0830], [-218.1700, 516.5350],
        [-213.6160, 519.4590], [-209.5830, 521.8680], [-205.6370, 524.1110], [-202.7440, 525.6520], [-197.1090, 528.3950],
        [-192.4540, 530.5780], [-188.8340, 532.1670], [-184.3090, 534.0130], [-179.9540, 535.6640], [-176.1920, 536.9920],
        [-171.5600, 538.4700], [-168.6330, 539.3390], [-159.0040, 541.7770], [-155.6290, 542.4990], [-145.5670, 544.2700],
        [-143.0290, 544.6810], [-140.4440, 545.0200], [-138.1320, 545.2370], [-136.1070, 545.3550], [-129.8970, 545.5050],
        [-127.8440, 545.5890], [-122.1320, 546.0060], [-119.7560, 546.1360], [-117.3420, 546.2010], [-114.2050, 546.2260],
        [-89.0000, 546.2300], [-87.4140, 544.6660], [-87.4140, 88.9610], [-89.0000, 87.3970], [-269.5520, 87.3830],
        [-269.9420, 87.3440], [-270.4950, 87.1470], [-270.8210, 86.9290], [-271.0980, 86.6520], [-271.4000, 86.1480],
        [-271.5130, 85.7730], [-271.5520, 85.3830], [-271.5520, 53.5980], [-271.4660, 53.0170], [-271.2150, 52.4870],
        [-270.8210, 52.0520], [-270.3170, 51.7500], [-269.9420, 51.6360], [-269.5520, 51.5980], [-263.5520, 51.5980],
        [-260.4540, 51.5410], [-99.5300, 51.7320], [-92.2010, 51.7710], [-89.4560, 51.8660], [-87.1180, 52.0550],
        [-85.1830, 52.3260], [-83.0190, 52.7780], [-80.6610, 53.4610], [-78.3870, 54.2920], [-76.1490, 55.2550],
        [-73.9350, 56.3670], [-71.4910, 57.7990], [-69.1110, 59.3930], [-66.5550, 61.3190], [-64.6020, 62.9860],
        [-62.9940, 64.5630], [-61.2910, 66.4980], [-59.5270, 68.7930], [-57.8990, 71.1630], [-56.4230, 73.5940],
        [-55.1320, 76.0770], [-54.0310, 78.5920], [-53.0980, 81.1510], [-52.4270, 83.5180], [-51.9900, 85.6930],
        [-51.8080, 86.9800], [-51.6720, 88.2980], [-51.5180, 91.0050], [-51.4630, 94.1220], [-51.5700, 541.9210],
        [-51.6390, 545.0300], [-51.7870, 547.3920], [-52.0630, 549.6740], [-52.4870, 551.8580], [-53.1430, 554.2350],
        [-53.9520, 556.5190], [-55.0220, 559.0410], [-56.1390, 561.2570], [-57.4320, 563.4340], [-58.8920, 565.5600],
        [-60.5080, 567.6280], [-62.0450, 569.3730], [-63.6870, 571.0300]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222]
    ], convexity = 30);
}

module letter_outline() {
    polygon(points = [
        [-399.8210, 0.1630], [-399.9150, -5.0720], [-399.9200, -10.2660], [-399.8380, -15.4930], [-399.6680, -20.7250],
        [-399.4120, -25.9610], [-399.0700, -31.1990], [-398.6420, -36.4370], [-398.1290, -41.6720], [-397.5320, -46.9050],
        [-396.8500, -52.1320], [-396.0850, -57.3510], [-395.2370, -62.5610], [-394.3070, -67.7610], [-393.2950, -72.9480],
        [-392.2020, -78.1200], [-391.0280, -83.2750], [-389.7730, -88.4130], [-388.4390, -93.5300], [-387.0250, -98.6250],
        [-385.5330, -103.6970], [-383.9630, -108.7430], [-382.3150, -113.7620], [-380.5910, -118.7510], [-378.7890, -123.7100],
        [-376.9120, -128.6350], [-374.9590, -133.5260], [-372.9310, -138.3800], [-370.8290, -143.1960], [-368.6530, -147.9720],
        [-366.4030, -152.7060], [-364.0810, -157.3960], [-361.6870, -162.0400], [-359.2200, -166.6370], [-356.6830, -171.1840],
        [-354.0750, -175.6810], [-351.3970, -180.1240], [-348.6490, -184.5130], [-345.8320, -188.8450], [-342.9460, -193.1180],
        [-339.9930, -197.3320], [-336.9720, -201.4830], [-333.8840, -205.5700], [-330.7300, -209.5920], [-327.5100, -213.5460],
        [-324.2240, -217.4300], [-320.8740, -221.2440], [-317.4600, -224.9840], [-313.9810, -228.6490], [-310.4400, -232.2380],
        [-306.8360, -235.7480], [-303.1920, -239.1570], [-155.5990, -239.1570], [-158.6950, -237.4400], [-162.0140, -235.5400],
        [-165.2860, -233.6050], [-168.5100, -231.6370], [-171.6870, -229.6350], [-174.8170, -227.6010], [-177.9000, -225.5330],
        [-180.9360, -223.4330], [-183.9250, -221.3000], [-186.8670, -219.1350], [-189.7630, -216.9380], [-192.6130, -214.7100],
        [-195.4170, -212.4500], [-198.1750, -210.1580], [-200.8860, -207.8360], [-203.5530, -205.4820], [-206.1730, -203.0980],
        [-208.7490, -200.6840], [-211.2790, -198.2400], [-213.7640, -195.7650], [-216.2040, -193.2610], [-218.6000, -190.7280],
        [-220.9500, -188.1650], [-223.2570, -185.5730], [-225.5190, -182.9530], [-227.7370, -180.3040], [-229.9110, -177.6260],
        [-232.0410, -174.9210], [-234.1270, -172.1870], [-236.1700, -169.4260], [-238.1690, -166.6380], [-240.1260, -163.8220],
        [-242.0390, -160.9800], [-243.9090, -158.1110], [-245.7360, -155.2150], [-247.5210, -152.2930], [-249.2630, -149.3450],
        [-250.9630, -146.3710], [-252.6210, -143.3720], [-254.2370, -140.3470], [-255.8110, -137.2970], [-257.3430, -134.2230],
        [-258.8330, -131.1230], [-260.2820, -127.9990], [-261.6900, -124.8510], [-263.0570, -121.6790], [-264.3830, -118.4840],
        [-265.6680, -115.2650], [-266.9120, -112.0220], [-268.1160, -108.7560], [-269.2800, -105.4680], [-270.4030, -102.1570],
        [-271.4860, -98.8240], [-272.5300, -95.4680], [-273.5330, -92.0910], [-274.4980, -88.6920], [-275.4220, -85.2710],
        [-276.3080, -81.8300], [-277.1540, -78.3670], [-277.9610, -74.8830], [-278.7290, -71.3790], [-279.4590, -67.8550],
        [-280.1500, -64.3110], [-280.8030, -60.7460], [-281.4180, -57.1620], [-281.9950, -53.5590], [-283.0340, -46.2950],
        [-283.4980, -42.6350], [-284.3120, -35.2600], [-284.6640, -31.5450], [-285.2560, -24.0620], [-285.7010, -16.5090],
        [-286.0010, -8.8900], [-286.1000, -4.9200], [-286.1800, 2.6630], [-286.1680, 6.5450], [-286.0390, 14.3570],
        [-285.7690, 22.2290], [-285.3590, 30.1590], [-284.8120, 38.1420], [-284.7430, 46.6610], [-284.5400, 54.9640],
        [-284.3880, 59.0350], [-283.9850, 67.0140], [-283.4520, 74.7780], [-283.1370, 78.5800], [-282.4110, 86.0240],
        [-282.0010, 89.6660], [-281.0870, 96.7930], [-280.5830, 100.2780], [-279.4850, 107.0900], [-278.2660, 113.6940],
        [-277.6110, 116.9190], [-276.9280, 120.0920], [-275.4730, 126.2830], [-274.4950, 130.0800], [-273.0750, 135.1880],
        [-272.2200, 138.0540], [-271.3360, 140.8710], [-270.4260, 143.6360], [-268.5210, 149.0170], [-267.5280, 151.6330],
        [-266.5080, 154.1990], [-265.4620, 156.7150], [-264.3900, 159.1820], [-263.2910, 161.5990], [-262.1670, 163.9680],
        [-261.0180, 166.2870], [-259.8430, 168.5570], [-258.6430, 170.7790], [-257.4170, 172.9530], [-256.1670, 175.0780],
        [-254.8920, 177.1540], [-253.5940, 179.1820], [-252.2720, 181.1630], [-250.9250, 183.0960], [-249.5550, 184.9820],
        [-248.1610, 186.8190], [-246.7450, 188.6090], [-245.3060, 190.3530], [-243.8440, 192.0480], [-242.3590, 193.6990],
        [-240.8530, 195.3000], [-239.3250, 196.8570], [-237.7740, 198.3660], [-236.2030, 199.8290], [-234.6090, 201.2460],
        [-232.9960, 202.6180], [-231.3600, 203.9430], [-229.7050, 205.2220], [-228.0290, 206.4570], [-226.3340, 207.6450],
        [-224.6180, 208.7880], [-222.8830, 209.8870], [-221.1270, 210.9400], [-219.3530, 211.9490], [-217.5600, 212.9130],
        [-215.7490, 213.8330], [-213.9180, 214.7080], [-212.0700, 215.5390], [-210.2030, 216.3260], [-208.3190, 217.0700],
        [-206.4170, 217.7690], [-204.4970, 218.4240], [-202.5610, 219.0370], [-200.6080, 219.6060], [-198.6380, 220.1320],
        [-196.6510, 220.6150], [-194.6480, 221.0550], [-192.6300, 221.4520], [-190.5950, 221.8080], [-188.5460, 222.1210],
        [-186.4800, 222.3910], [-184.4000, 222.6200], [-182.3050, 222.8060], [-180.1950, 222.9510], [-178.0710, 223.0540],
        [-175.9330, 223.1160], [-173.7810, 223.1370], [-171.0230, 223.1130], [-168.2990, 223.0400], [-165.6090, 222.9210],
        [-162.9530, 222.7530], [-160.3310, 222.5350], [-157.7430, 222.2710], [-155.1890, 221.9580], [-152.6680, 221.5950],
        [-150.1810, 221.1850], [-147.7270, 220.7260], [-145.3070, 220.2170], [-142.9200, 219.6610], [-140.5670, 219.0550],
        [-138.2470, 218.4010], [-135.9600, 217.6970], [-133.7060, 216.9440], [-131.4850, 216.1420], [-129.2970, 215.2910],
        [-127.1420, 214.3900], [-125.0200, 213.4400], [-122.9300, 212.4400], [-120.8730, 211.3910], [-118.8490, 210.2910],
        [-116.8570, 209.1430], [-114.8970, 207.9450], [-112.9700, 206.6970], [-111.0760, 205.3980], [-109.2140, 204.0500],
        [-107.3830, 202.6510], [-105.5850, 201.2020], [-103.8190, 199.7040], [-102.0850, 198.1540], [-99.9200, 196.1040],
        [-98.7110, 194.9040], [-97.0720, 193.2040], [-95.4650, 191.4520], [-93.8890, 189.6500], [-92.3440, 187.7980],
        [-90.8310, 185.8940], [-89.3500, 183.9400], [-87.9000, 181.9340], [-86.4800, 179.8770], [-85.0920, 177.7700],
        [-83.7350, 175.6110], [-82.4090, 173.4010], [-81.1140, 171.1390], [-79.8490, 168.8260], [-78.6160, 166.4620],
        [-77.4130, 164.0460], [-76.2400, 161.5780], [-75.0980, 159.0590], [-73.9860, 156.4880], [-72.9050, 153.8650],
        [-71.8540, 151.1900], [-70.8330, 148.4630], [-69.8420, 145.6830], [-68.8810, 142.8520], [-67.9500, 139.9690],
        [-67.0490, 137.0330], [-66.1780, 134.0440], [-64.5250, 127.9100], [-63.7420, 124.7640], [-62.9890, 121.5660],
        [-62.2660, 118.3140], [-61.5720, 115.0100], [-60.2710, 108.2420], [-59.6640, 104.7790], [-58.5370, 97.6920],
        [-57.5260, 90.3930], [-56.6300, 82.8790], [-55.8480, 75.1510], [-55.1790, 67.2080], [-54.6240, 59.0490],
        [-54.1800, 50.6740], [-53.8490, 42.0810], [-53.7250, 37.7040], [-53.5600, 28.7850], [-53.5180, 24.2440],
        [-53.5050, -5.0400], [-53.5050, -239.1570], [38.7940, -239.1570], [38.8080, 24.2440], [38.8490, 28.7850],
        [39.0140, 37.7040], [39.2900, 46.4050], [39.4700, 50.6740], [39.6770, 54.8880], [40.1770, 63.1560],
        [40.7890, 71.2070], [41.5140, 79.0420], [42.3530, 86.6630], [43.3070, 94.0690], [43.8270, 97.6920],
        [44.9530, 104.7790], [46.1960, 111.6520], [47.5550, 118.3140], [49.0310, 124.7640], [49.8140, 127.9100],
        [51.4670, 134.0440], [52.3390, 137.0330], [53.2400, 139.9690], [54.1710, 142.8520], [55.1310, 145.6830],
        [56.1220, 148.4630], [57.1430, 151.1900], [58.1940, 153.8650], [59.2760, 156.4880], [60.3870, 159.0590],
        [61.5290, 161.5780], [62.7020, 164.0460], [63.9050, 166.4620], [65.1390, 168.8260], [66.4030, 171.1390],
        [67.6980, 173.4010], [69.0240, 175.6110], [70.3820, 177.7700], [71.7700, 179.8770], [73.1890, 181.9340],
        [74.6390, 183.9400], [76.1210, 185.8940], [77.6340, 187.7980], [79.1780, 189.6500], [80.7540, 191.4520],
        [82.3610, 193.2040], [84.0000, 194.9040], [85.6710, 196.5550], [87.3730, 198.1540], [89.1080, 199.7030],
        [90.8740, 201.2020], [92.6720, 202.6510], [94.5030, 204.0500], [96.3650, 205.3980], [98.2600, 206.6960],
        [99.9200, 207.7770], [102.1460, 209.1430], [104.1390, 210.2920], [106.1620, 211.3910], [108.2200, 212.4400],
        [110.3090, 213.4390], [112.4310, 214.3900], [114.5870, 215.2910], [116.7750, 216.1420], [118.9950, 216.9440],
        [121.2490, 217.6970], [123.5360, 218.4010], [125.8570, 219.0550], [128.2090, 219.6610], [130.5970, 220.2180],
        [133.0170, 220.7260], [135.4700, 221.1850], [137.9570, 221.5950], [140.4780, 221.9580], [143.0320, 222.2710],
        [145.6210, 222.5350], [148.2430, 222.7530], [150.8990, 222.9210], [153.5890, 223.0400], [156.3120, 223.1130],
        [159.0700, 223.1370], [161.8320, 223.1130], [164.5660, 223.0410], [167.2730, 222.9210], [169.9510, 222.7540],
        [172.6030, 222.5390], [175.2260, 222.2760], [177.8220, 221.9660], [180.3900, 221.6080], [182.9290, 221.2040],
        [185.4410, 220.7510], [187.9240, 220.2520], [190.3790, 219.7050], [192.8060, 219.1110], [195.2050, 218.4700],
        [197.5750, 217.7830], [199.9170, 217.0480], [202.2300, 216.2670], [204.5140, 215.4400], [206.7700, 214.5650],
        [208.9960, 213.6440], [211.1950, 212.6760], [213.3630, 211.6620], [215.5030, 210.6020], [217.6140, 209.4950],
        [219.6950, 208.3430], [221.7470, 207.1440], [223.7700, 205.8990], [225.7630, 204.6090], [227.7260, 203.2730],
        [229.6600, 201.8900], [231.5650, 200.4620], [233.4400, 198.9890], [235.2840, 197.4690], [237.0980, 195.9050],
        [238.8830, 194.2950], [240.6380, 192.6410], [242.3620, 190.9390], [244.0560, 189.1950], [245.7200, 187.4030],
        [247.3540, 185.5680], [248.9570, 183.6870], [250.5290, 181.7620], [252.0700, 179.7920], [253.5810, 177.7770],
        [255.0620, 175.7180], [256.5110, 173.6130], [257.9290, 171.4660], [259.3170, 169.2730], [260.6740, 167.0360],
        [261.9990, 164.7550], [263.2930, 162.4300], [264.5560, 160.0600], [265.7870, 157.6470], [266.9870, 155.1900],
        [268.1540, 152.6890], [269.2910, 150.1440], [270.3970, 147.5550], [271.4700, 144.9230], [272.5110, 142.2480],
        [273.5210, 139.5280], [274.4980, 136.7660], [275.4440, 133.9610], [276.7220, 129.9200], [278.0870, 125.2850],
        [278.9030, 122.3070], [279.6870, 119.2860], [280.4390, 116.2220], [281.1580, 113.1160], [281.8440, 109.9670],
        [283.1180, 103.5410], [283.7060, 100.2640], [284.7820, 93.5840], [285.7260, 86.7340], [286.5370, 79.7170],
        [286.8930, 76.1450], [287.5030, 68.8760], [287.7580, 65.1790], [288.1660, 57.6600], [288.4390, 49.9760],
        [288.5760, 42.1260], [288.5930, 38.1420], [289.1270, 29.5550], [289.4970, 21.0500], [289.6200, 16.8290],
        [289.7020, 12.6300], [289.7430, 8.4530], [289.7430, 4.2980], [289.7020, 0.1650], [289.4970, -8.0320],
        [289.3320, -12.0960], [289.1270, -16.1370], [288.8810, -20.1540], [288.5930, -24.1480], [288.2630, -28.1170],
        [287.8930, -32.0640], [287.4830, -35.9850], [287.0310, -39.8810], [286.5380, -43.7530], [286.0030, -47.5990],
        [285.4270, -51.4200], [284.8120, -55.2150], [284.1540, -58.9860], [283.4540, -62.7300], [282.7150, -66.4470],
        [281.9340, -70.1380], [281.1120, -73.8030], [280.2490, -77.4400], [279.3450, -81.0490], [278.3990, -84.6330],
        [277.4120, -88.1880], [276.3850, -91.7160], [275.3160, -95.2140], [274.2060, -98.6860], [273.0550, -102.1280],
        [271.8630, -105.5420], [270.6300, -108.9260], [269.3560, -112.2820], [268.0410, -115.6080], [266.6840, -118.9050],
        [265.2870, -122.1710], [263.8480, -125.4080], [262.3680, -128.6140], [260.8470, -131.7890], [259.2850, -134.9330],
        [257.6820, -138.0470], [256.0380, -141.1300], [254.3520, -144.1800], [252.6260, -147.1990], [250.8580, -150.1860],
        [249.0490, -153.1410], [247.2000, -156.0630], [245.3090, -158.9530], [243.3760, -161.8100], [241.4030, -164.6340],
        [239.3890, -167.4250], [237.3330, -170.1820], [235.2370, -172.9040], [233.1000, -175.5940], [230.9210, -178.2490],
        [228.7010, -180.8690], [226.4410, -183.4540], [224.1380, -186.0050], [221.7950, -188.5200], [219.4110, -191.0010],
        [216.9850, -193.4460], [214.5200, -195.8540], [212.0110, -198.2270], [209.4630, -200.5620], [206.8730, -202.8620],
        [204.2420, -205.1260], [201.5700, -207.3510], [198.8570, -209.5400], [196.1030, -211.6920], [193.3070, -213.8050],
        [190.4710, -215.8810], [187.5930, -217.9180], [184.6750, -219.9170], [181.7150, -221.8780], [178.7140, -223.7990],
        [175.6730, -225.6820], [172.5900, -227.5260], [169.4660, -229.3290], [166.3000, -231.0940], [163.0940, -232.8180],
        [159.8460, -234.5010], [156.5580, -236.1450], [153.2280, -237.7480], [150.1870, -239.1570], [164.3980, -239.1380],
        [171.5200, -239.0920], [178.5340, -239.0010], [183.7210, -238.8960], [188.8470, -238.7520], [193.9100, -238.5630],
        [198.9130, -238.3220], [202.2130, -238.1300], [208.7320, -237.6620], [215.1400, -237.0700], [218.3040, -236.7230],
        [221.4390, -236.3390], [224.5470, -235.9160], [227.6280, -235.4550], [230.6820, -234.9510], [233.7080, -234.4020],
        [236.7060, -233.8080], [239.6770, -233.1680], [242.6210, -232.4770], [245.5370, -231.7360], [248.4260, -230.9420],
        [251.2870, -230.0930], [254.1200, -229.1870], [256.9270, -228.2230], [259.7060, -227.1990], [262.4570, -226.1120],
        [265.1820, -224.9620], [267.8780, -223.7460], [270.5470, -222.4620], [273.1890, -221.1100], [275.8030, -219.6860],
        [278.3900, -218.1900], [280.9500, -216.6180], [283.4820, -214.9690], [285.9870, -213.2430], [292.7380, -208.3120],
        [296.9290, -205.1110], [301.0370, -201.8300], [305.0610, -198.4720], [309.0040, -195.0410], [312.8650, -191.5360],
        [316.6420, -187.9590], [320.3380, -184.3130], [323.9500, -180.6000], [327.4800, -176.8210], [330.9260, -172.9790],
        [334.2890, -169.0730], [337.5700, -165.1080], [340.7670, -161.0840], [343.8810, -157.0040], [346.9120, -152.8680],
        [349.8590, -148.6810], [352.7230, -144.4410], [355.5040, -140.1520], [358.2000, -135.8170], [360.8140, -131.4350],
        [363.3440, -127.0100], [365.7890, -122.5430], [368.1510, -118.0340], [370.4280, -113.4890], [372.6220, -108.9060],
        [374.7320, -104.2890], [376.7570, -99.6380], [378.6980, -94.9570], [380.5540, -90.2470], [382.3270, -85.5090],
        [384.0140, -80.7460], [385.6170, -75.9590], [387.1360, -71.1500], [388.5690, -66.3210], [389.9180, -61.4730],
        [391.1830, -56.6100], [392.3620, -51.7320], [393.4550, -46.8400], [394.4640, -41.9380], [395.3880, -37.0270],
        [396.2260, -32.1090], [396.9790, -27.1850], [397.6470, -22.2570], [398.2280, -17.3280], [398.7240, -12.3980],
        [399.1350, -7.4700], [399.3040, -4.9200], [399.4600, -2.5460], [399.6990, 2.3720], [399.8530, 7.2830],
        [399.9200, 12.1850], [399.9010, 17.0770], [399.7960, 21.9550], [399.6050, 26.8180], [399.3280, 31.6660],
        [398.9640, 36.4950], [398.5140, 41.3030], [397.9780, 46.0900], [397.3550, 50.8540], [396.6450, 55.5910],
        [395.8480, 60.3010], [394.9650, 64.9820], [393.9950, 69.6320], [392.9380, 74.2490], [391.7940, 78.8310],
        [390.5620, 83.3770], [389.2440, 87.8850], [387.8380, 92.3520], [386.3450, 96.7770], [384.7650, 101.1580],
        [383.0970, 105.4940], [381.3420, 109.7820], [379.4990, 114.0210], [377.5680, 118.2090], [375.5490, 122.3440],
        [373.4430, 126.4240], [371.4490, 130.0800], [368.9660, 134.4120], [366.5970, 138.3160], [364.1370, 142.1590],
        [361.5910, 145.9380], [358.9560, 149.6500], [356.2330, 153.2960], [353.4210, 156.8720], [350.5200, 160.3770],
        [347.5320, 163.8080], [344.4540, 167.1660], [341.2880, 170.4450], [338.0330, 173.6480], [334.6880, 176.7680],
        [331.5910, 179.5100], [328.4590, 182.1900], [325.2950, 184.8090], [322.0970, 187.3660], [318.8680, 189.8620],
        [315.6080, 192.2960], [312.3180, 194.6690], [308.9980, 196.9790], [305.6480, 199.2280], [302.2680, 201.4160],
        [298.8620, 203.5420], [295.4270, 205.6060], [291.9660, 207.6080], [288.4790, 209.5490], [284.9660, 211.4290],
        [281.4270, 213.2460], [277.8640, 215.0030], [274.2780, 216.6970], [270.6680, 218.3300], [267.0350, 219.9010],
        [263.3800, 221.4110], [259.7040, 222.8590], [256.0070, 224.2450], [252.2900, 225.5700], [248.5530, 226.8340],
        [244.7970, 228.0350], [241.0220, 229.1750], [237.2300, 230.2530], [233.4200, 231.2700], [229.5950, 232.2250],
        [225.7520, 233.1190], [221.8950, 233.9500], [218.0230, 234.7210], [214.1370, 235.4290], [210.2370, 236.0760],
        [206.3240, 236.6620], [202.3990, 237.1850], [198.4630, 237.6470], [194.5150, 238.0480], [190.5560, 238.3870],
        [186.5880, 238.6650], [182.6100, 238.8800], [178.6240, 239.0340], [174.6290, 239.1260], [170.6280, 239.1570],
        [166.6190, 239.1270], [162.6040, 239.0340], [158.5830, 238.8800], [154.5590, 238.6640], [150.5280, 238.3870],
        [146.4940, 238.0480], [142.4580, 237.6470], [138.4170, 237.1850], [134.3760, 236.6620], [130.3330, 236.0760],
        [126.2900, 235.4290], [122.2460, 234.7210], [118.2030, 233.9500], [114.1600, 233.1180], [110.1190, 232.2240],
        [106.0810, 231.2690], [102.0450, 230.2530], [98.0130, 229.1740], [93.9850, 228.0340], [89.9620, 226.8330],
        [85.9440, 225.5700], [81.9320, 224.2450], [77.9270, 222.8580], [73.9290, 221.4100], [69.9380, 219.9000],
        [65.9560, 218.3290], [61.9830, 216.6960], [58.0190, 215.0010], [54.0660, 213.2450], [50.1230, 211.4270],
        [46.1920, 209.5480], [42.2720, 207.6060], [38.3660, 205.6040], [34.4720, 203.5390], [30.5930, 201.4130],
        [26.7280, 199.2260], [22.8780, 196.9760], [19.0430, 194.6650], [15.2250, 192.2930], [11.4240, 189.8590],
        [7.6400, 187.3630], [3.8750, 184.8060], [0.1280, 182.1860], [-3.6000, 179.5060], [-7.3630, 176.7230],
        [-10.2080, 179.5130], [-13.0520, 182.1930], [-15.9410, 184.8120], [-18.8750, 187.3690], [-21.8520, 189.8640],
        [-24.8720, 192.2980], [-27.9340, 194.6700], [-31.0360, 196.9810], [-34.1770, 199.2290], [-37.3570, 201.4170],
        [-40.5740, 203.5430], [-43.8280, 205.6070], [-47.1160, 207.6090], [-50.4390, 209.5500], [-53.7940, 211.4290],
        [-57.1820, 213.2470], [-60.6000, 215.0030], [-64.0490, 216.6980], [-67.5260, 218.3300], [-71.0310, 219.9020],
        [-74.5620, 221.4110], [-78.1190, 222.8590], [-81.7000, 224.2460], [-85.3050, 225.5700], [-88.9330, 226.8340],
        [-92.5810, 228.0350], [-96.2500, 229.1750], [-99.9210, 230.2480], [-103.6440, 231.2700], [-107.3670, 232.2250],
        [-111.1060, 233.1180], [-114.8600, 233.9500], [-118.6280, 234.7210], [-122.4090, 235.4290], [-126.2010, 236.0760],
        [-130.0050, 236.6620], [-133.8170, 237.1860], [-137.6380, 237.6480], [-141.4670, 238.0480], [-145.3010, 238.3870],
        [-149.1410, 238.6640], [-152.9870, 238.8800], [-156.8340, 239.0340], [-160.6840, 239.1260], [-164.5350, 239.1570],
        [-168.3870, 239.1270], [-172.2360, 239.0340], [-176.0840, 238.8800], [-179.9280, 238.6640], [-183.7690, 238.3870],
        [-187.6040, 238.0480], [-191.4320, 237.6470], [-195.2540, 237.1850], [-199.0660, 236.6610], [-202.8700, 236.0760],
        [-206.6620, 235.4290], [-210.4420, 234.7210], [-214.2100, 233.9510], [-217.9650, 233.1180], [-221.7040, 232.2250],
        [-225.4260, 231.2700], [-229.1330, 230.2530], [-232.8210, 229.1750], [-236.4890, 228.0350], [-240.1380, 226.8330],
        [-243.7650, 225.5700], [-247.3700, 224.2460], [-250.9520, 222.8590], [-254.5090, 221.4110], [-258.0400, 219.9010],
        [-261.5450, 218.3310], [-265.0220, 216.6980], [-268.4710, 215.0030], [-271.8890, 213.2470], [-275.2760, 211.4300],
        [-278.6320, 209.5500], [-281.9550, 207.6090], [-285.2430, 205.6070], [-288.4960, 203.5430], [-291.7140, 201.4170],
        [-294.8930, 199.2300], [-298.0350, 196.9800], [-301.1370, 194.6700], [-304.1990, 192.2980], [-307.2190, 189.8640],
        [-310.1960, 187.3680], [-313.1290, 184.8120], [-316.0190, 182.1930], [-318.8630, 179.5130], [-321.6610, 176.7690],
        [-325.6140, 173.3370], [-329.4560, 169.8270], [-333.1890, 166.2380], [-336.8130, 162.5730], [-340.3300, 158.8340],
        [-343.7410, 155.0200], [-347.0450, 151.1360], [-350.2440, 147.1820], [-353.3370, 143.1610], [-356.3250, 139.0750],
        [-359.2090, 134.9240], [-362.4040, 130.0510], [-364.6670, 126.4380], [-367.2420, 122.1060], [-369.7150, 117.7180],
        [-372.0860, 113.2750], [-374.3560, 108.7790], [-376.5260, 104.2320], [-378.5960, 99.6360], [-380.5660, 94.9920],
        [-382.4380, 90.3020], [-384.2110, 85.5690], [-385.8860, 80.7940], [-387.4640, 75.9780], [-388.9450, 71.1240],
        [-390.3300, 66.2340], [-391.6200, 61.3080], [-392.8140, 56.3500], [-393.9130, 51.3610], [-394.9190, 46.3430],
        [-395.8300, 41.2970], [-396.6490, 36.2260], [-397.3760, 31.1310], [-398.0100, 26.0140], [-398.5530, 20.8760],
        [-399.0050, 15.7210], [-399.3660, 10.5490], [-399.6380, 5.3630]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881, 882]
    ], convexity = 30);
}

module photo_loop_1() {
    polygon(points = [
        [-509.8410, 114.0950], [-504.2560, 114.0660], [-373.0190, 114.0610], [-369.5510, 114.1190], [-367.1670, 114.2450],
        [-364.8370, 114.4740], [-362.2210, 114.8340], [-361.9000, 117.1680], [-361.6810, 119.5400], [-361.5720, 121.9510],
        [-361.5270, 125.0860], [-361.4470, 256.3520], [-361.4700, 261.5890], [-361.5690, 264.6860], [-361.7870, 267.3710],
        [-362.2210, 270.6480], [-364.8900, 271.0080], [-367.6050, 271.2240], [-370.3540, 271.2850], [-373.0900, 271.2160],
        [-376.4480, 270.9800], [-383.0760, 270.3430], [-389.0050, 269.7200], [-391.9000, 269.3250], [-394.7030, 268.8010],
        [-402.0710, 267.2290], [-404.2080, 266.7340], [-406.6060, 266.1070], [-410.7320, 264.9360], [-413.6340, 264.0390],
        [-419.6120, 261.9950], [-422.6930, 260.8560], [-425.7040, 259.6170], [-429.2090, 258.0630], [-432.7090, 256.4200],
        [-435.9640, 254.8000], [-439.7720, 252.7800], [-443.8710, 250.5090], [-446.3340, 249.0390], [-448.7640, 247.4750],
        [-453.7560, 244.1460], [-456.0880, 242.5170], [-458.9210, 240.3920], [-463.8090, 236.5730], [-465.5900, 235.0920],
        [-467.0860, 233.7670], [-473.3240, 227.9830], [-475.0280, 226.3480], [-477.3310, 223.9410], [-481.2360, 219.5960],
        [-483.8040, 216.5980], [-486.5960, 213.1850], [-488.4610, 210.7690], [-490.4640, 208.0080], [-492.8530, 204.5510],
        [-495.4110, 200.7060], [-497.4920, 197.4120], [-499.2480, 194.4360], [-500.8690, 191.4780], [-503.5450, 186.3500],
        [-504.7560, 183.8900], [-505.7660, 181.6710], [-507.0660, 178.5830], [-508.5560, 174.8940], [-509.8750, 171.4400],
        [-510.9160, 168.5360], [-512.1530, 164.7460], [-513.3220, 160.9630], [-513.9680, 158.5910], [-515.7680, 151.3880],
        [-516.2450, 149.2470], [-516.5940, 147.3690], [-517.6360, 140.3290], [-518.3930, 135.5670], [-518.6010, 133.9480],
        [-518.7520, 132.2940], [-518.8590, 130.2630], [-518.9120, 127.5010], [-518.8890, 114.9230], [-515.6180, 114.4440],
        [-512.9360, 114.2050]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80]
    ], convexity = 30);
}

module photo_loop_2() {
    polygon(points = [
        [-132.2520, 518.7120], [-133.9110, 518.5660], [-135.5340, 518.3630], [-140.3050, 517.6090], [-147.6730, 516.5100],
        [-149.5490, 516.1520], [-151.6880, 515.6660], [-158.9020, 513.8590], [-161.2720, 513.2050], [-165.6440, 511.8420],
        [-168.8580, 510.7850], [-172.9260, 509.3270], [-176.3800, 508.0180], [-179.5030, 506.7290], [-182.5830, 505.3640],
        [-185.0620, 504.1800], [-188.0510, 502.6580], [-192.4170, 500.3530], [-195.4500, 498.6740], [-198.9160, 496.6300],
        [-201.7050, 494.8540], [-205.0130, 492.5960], [-209.1350, 489.6810], [-211.6070, 487.8500], [-214.0260, 485.9480],
        [-217.4800, 483.0950], [-220.2350, 480.7070], [-224.3300, 476.9980], [-226.7680, 474.6280], [-233.7640, 467.1650],
        [-235.3150, 465.4160], [-236.7900, 463.6300], [-240.9540, 458.1930], [-243.3000, 455.0340], [-245.1750, 452.3370],
        [-248.6270, 447.1680], [-250.1880, 444.6730], [-251.8110, 441.8810], [-253.4650, 438.8410], [-255.1430, 435.5520],
        [-256.7230, 432.2400], [-258.9960, 427.2120], [-260.5750, 423.5450], [-261.7090, 420.7040], [-262.8350, 417.5590],
        [-264.1670, 413.5370], [-265.9270, 407.7120], [-266.7560, 404.7660], [-267.4100, 402.0440], [-269.0550, 394.3600],
        [-269.4700, 392.1690], [-269.8050, 389.9220], [-270.6560, 382.0090], [-271.1680, 376.7030], [-271.3820, 374.0260],
        [-271.4870, 371.9870], [-271.5430, 369.9180], [-271.5750, 363.2820], [-269.5850, 361.2920], [-115.6290, 361.4180],
        [-114.9010, 364.2220], [-114.6530, 365.5000], [-114.4650, 366.8070], [-114.3360, 368.1420], [-114.2550, 369.5000],
        [-114.1750, 373.6580], [-114.0810, 507.6500], [-114.1280, 511.1220], [-114.2390, 513.5110], [-114.4520, 515.8480],
        [-114.8490, 518.7930], [-127.4490, 518.8540], [-130.2160, 518.8110]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
    ], convexity = 30);
}

module photo_loop_3() {
    polygon(points = [
        [271.2920, 374.7430], [270.7980, 380.3970], [269.9980, 388.3310], [269.6890, 390.9380], [269.3430, 393.1650],
        [268.8530, 395.6470], [267.4180, 402.0830], [266.9060, 404.2130], [266.3420, 406.3040], [264.6950, 411.8710],
        [263.6910, 415.0550], [262.0570, 419.9050], [260.7980, 423.2560], [259.3060, 426.8000], [257.4710, 430.8380],
        [255.5150, 434.8930], [253.4500, 438.9450], [251.8640, 441.8700], [250.1970, 444.7580], [248.1000, 448.1730],
        [245.8820, 451.6200], [244.2510, 453.9920], [242.5310, 456.3350], [238.1440, 462.0070], [236.0920, 464.5760],
        [234.7970, 466.0930], [233.4580, 467.5770], [227.9340, 473.5330], [226.2910, 475.2280], [223.8520, 477.5350],
        [219.4730, 481.4630], [216.7190, 483.8150], [213.2960, 486.6150], [210.8730, 488.4850], [207.8610, 490.6740],
        [203.4790, 493.7410], [200.4580, 495.7480], [197.3540, 497.6510], [194.0890, 499.5220], [189.7000, 501.8780],
        [185.3620, 504.1110], [183.1670, 505.1590], [180.6610, 506.2600], [176.1400, 508.1200], [172.6980, 509.4630],
        [168.0530, 511.1360], [161.6450, 513.1730], [158.9850, 513.9140], [151.7750, 515.7120], [149.9420, 516.1200],
        [148.0680, 516.4690], [141.6890, 517.4260], [135.0330, 518.5100], [132.4020, 518.7870], [129.3380, 518.9310],
        [124.4750, 518.9620], [122.4080, 518.9230], [121.0630, 518.8530], [119.4570, 518.6730], [118.5570, 518.4880],
        [117.9920, 518.3240], [117.2090, 518.0040], [116.7350, 517.7370], [116.3030, 517.4250], [115.9150, 517.0670],
        [115.4170, 516.4440], [115.0190, 515.7240], [114.7140, 514.9190], [114.4310, 513.7360], [114.2570, 512.4630],
        [114.1610, 511.1310], [114.0990, 509.0730], [114.0790, 506.2860], [114.1650, 372.2670], [114.2690, 368.8200],
        [114.4840, 366.4790], [114.8790, 364.2220], [115.6070, 361.4180], [269.5620, 361.2920], [271.4260, 362.9790],
        [271.4580, 370.3080], [271.4010, 372.7130]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81]
    ], convexity = 30);
}

module photo_loop_4() {
    polygon(points = [
        [362.1330, 267.5720], [361.9590, 266.6100], [361.7880, 265.2970], [361.6780, 263.9540], [361.5680, 260.5100],
        [361.4280, 124.3970], [361.4780, 122.3310], [361.5620, 120.9870], [361.7190, 119.6950], [361.9830, 118.4850],
        [362.2730, 117.6520], [362.5160, 117.1390], [362.8040, 116.6650], [363.3190, 116.0310], [363.9340, 115.4960],
        [364.6440, 115.0600], [365.4380, 114.7170], [366.6040, 114.3890], [367.8620, 114.1800], [369.1820, 114.0570],
        [370.8840, 113.9810], [372.9630, 113.9490], [507.6550, 114.0490], [511.1270, 114.1020], [513.5170, 114.2160],
        [515.8540, 114.4320], [518.7980, 114.8340], [518.9540, 118.6670], [518.9940, 122.5110], [518.9170, 128.1000],
        [518.7620, 131.5360], [518.6150, 133.2110], [518.3690, 135.1720], [517.5440, 140.2660], [516.4480, 147.6390],
        [516.0390, 149.8300], [515.4940, 152.2770], [514.2310, 157.3980], [513.4220, 160.3720], [512.4320, 163.5780],
        [510.8270, 168.5330], [509.8950, 171.1530], [508.5790, 174.6170], [507.0890, 178.3200], [505.6730, 181.6950],
        [504.6670, 183.9130], [503.5970, 186.1010], [501.0530, 190.9920], [499.1090, 194.5760], [497.0730, 198.0870],
        [495.3190, 200.9060], [493.2820, 203.9380], [490.2020, 208.3270], [488.2020, 211.0670], [486.5250, 213.2380],
        [483.9400, 216.4060], [481.3840, 219.4080], [477.4660, 223.7850], [475.1590, 226.2220], [473.2440, 228.0720],
        [467.0010, 233.8670], [465.2520, 235.4130], [463.4650, 236.8880], [458.5590, 240.7190], [455.9340, 242.6810],
        [453.5130, 244.3670], [448.0780, 247.9970], [445.5980, 249.5880], [443.0860, 251.0910], [440.0290, 252.7980],
        [437.0100, 254.3820], [433.9900, 255.8720], [430.3820, 257.5470], [426.1800, 259.4250], [422.5040, 260.9780],
        [419.3700, 262.1760], [415.0740, 263.6480], [411.8890, 264.6570], [406.3200, 266.3090], [404.2290, 266.8760],
        [402.0990, 267.3910], [395.6520, 268.8310], [393.1570, 269.3250], [390.9180, 269.6760], [388.3020, 269.9890],
        [381.0240, 270.7320], [374.7030, 271.3150], [372.6720, 271.4380], [370.2660, 271.5160], [363.2820, 271.5540],
        [362.7810, 270.0500], [362.4260, 268.8260]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91]
    ], convexity = 30);
}

module photo_loop_5() {
    polygon(points = [
        [361.7110, -265.2760], [361.8710, -266.5840], [362.0330, -267.5410], [362.3020, -268.7860], [363.0680, -271.4970],
        [369.6990, -271.5020], [371.7690, -271.4600], [373.8110, -271.3690], [378.4800, -270.9850], [388.3600, -269.9920],
        [390.9540, -269.6600], [393.4820, -269.2280], [401.4870, -267.5360], [404.2340, -266.8980], [407.7940, -265.9070],
        [414.2020, -263.9610], [419.0690, -262.3130], [422.4830, -261.0130], [427.5470, -258.8510], [433.6590, -256.0550],
        [437.4940, -254.1210], [442.6770, -251.2990], [444.8680, -250.0340], [446.7780, -248.8590], [453.1320, -244.6550],
        [456.2410, -242.4820], [459.8430, -239.7440], [463.7080, -236.7160], [465.9970, -234.7800], [467.4900, -233.4060],
        [470.8880, -230.1530], [474.1410, -227.1530], [475.4550, -225.8780], [477.8030, -223.3900], [481.9580, -218.7250],
        [485.2760, -214.7520], [487.7590, -211.6070], [490.3140, -208.1040], [493.4380, -203.5450], [496.1390, -199.4120],
        [498.4590, -195.5970], [499.6770, -193.4430], [501.1180, -190.7520], [503.0780, -186.9770], [504.4250, -184.2520],
        [505.3120, -182.3180], [506.1510, -180.3610], [508.7860, -173.8280], [509.8700, -170.9390], [510.6910, -168.6110],
        [512.8290, -161.9120], [513.6500, -158.9560], [515.6570, -150.8340], [516.0460, -148.9840], [516.3790, -147.0940],
        [517.3160, -140.6840], [518.1860, -135.2770], [518.4920, -132.6500], [518.6620, -129.9350], [518.7460, -126.8150],
        [518.7690, -123.6840], [518.7310, -121.6240], [518.6270, -119.9510], [518.4240, -118.3440], [518.1740, -117.1180],
        [517.7560, -115.6600], [517.1490, -113.9850], [372.3320, -114.1980], [368.8900, -114.3090], [367.5470, -114.4200],
        [366.2350, -114.5920], [365.2730, -114.7660], [364.0200, -115.0600], [362.7960, -115.4160], [361.2930, -115.9180],
        [361.4990, -260.4950], [361.6060, -263.9360]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76]
    ], convexity = 30);
}

module photo_loop_6() {
    polygon(points = [
        [114.7620, -365.2730], [114.5390, -366.5600], [114.3850, -367.8810], [114.2870, -369.2310], [114.1890, -373.3790],
        [114.0760, -507.7270], [114.1270, -511.1980], [114.2480, -513.5860], [114.4800, -515.9200], [114.9150, -518.8610],
        [127.8520, -518.8760], [130.6110, -518.8130], [132.6360, -518.6930], [134.2840, -518.5270], [135.8960, -518.3070],
        [141.2740, -517.4160], [147.3400, -516.5150], [149.8460, -516.0620], [152.2830, -515.5050], [160.0820, -513.5380],
        [162.7200, -512.7580], [167.6720, -511.1770], [171.1650, -509.9480], [175.4850, -508.2930], [180.5830, -506.2050],
        [183.9280, -504.7140], [188.2930, -502.5200], [193.7770, -499.5770], [198.4180, -496.8410], [202.3070, -494.3990],
        [207.2220, -491.0260], [211.4850, -487.9220], [213.4190, -486.4140], [215.6130, -484.6330], [217.8550, -482.7550],
        [219.6050, -481.2240], [224.3970, -476.7920], [226.3980, -474.8590], [233.2040, -467.7550], [235.4230, -465.2870],
        [238.2600, -461.7500], [241.4410, -457.6520], [243.1750, -455.3300], [245.6880, -451.6860], [249.3050, -446.0810],
        [250.6170, -443.9160], [252.0050, -441.5010], [253.3180, -439.0880], [254.7230, -436.3640], [256.8910, -431.8250],
        [258.9700, -427.2010], [260.3290, -424.0720], [261.8090, -420.3780], [263.4060, -415.8030], [264.7830, -411.4690],
        [266.6650, -405.0360], [267.4050, -402.0280], [269.0300, -394.6900], [269.4890, -392.1730], [269.8430, -389.5860],
        [270.7630, -380.6760], [271.1760, -376.3650], [271.3600, -374.0210], [271.4650, -371.9810], [271.5200, -369.9130],
        [271.5520, -363.2820], [269.7760, -361.3490], [115.9100, -361.2920], [115.4090, -362.7960], [115.0550, -364.0200]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]
    ], convexity = 30);
}

module photo_loop_7() {
    polygon(points = [
        [-271.3350, -374.7020], [-270.7520, -381.0220], [-270.0370, -387.9620], [-269.7200, -390.5660], [-269.3640, -392.7870],
        [-268.9330, -394.9540], [-267.3470, -402.3290], [-266.9130, -404.1580], [-266.3510, -406.2520], [-264.6990, -411.8210],
        [-263.5970, -415.2950], [-262.1210, -419.5910], [-260.9150, -422.7230], [-259.3560, -426.3960], [-257.2220, -431.1540],
        [-255.6680, -434.4780], [-254.1780, -437.4790], [-252.6220, -440.4300], [-250.9930, -443.3320], [-249.4160, -445.9430],
        [-247.7320, -448.5380], [-244.7670, -452.9470], [-243.1340, -455.2730], [-238.6730, -461.1990], [-236.4630, -464.0360],
        [-234.9710, -465.8140], [-233.1850, -467.7910], [-228.2710, -472.9870], [-225.8430, -475.4720], [-223.1970, -478.0040],
        [-219.8010, -481.0870], [-217.0470, -483.4590], [-213.8490, -486.0920], [-211.6740, -487.8010], [-209.2040, -489.6330],
        [-205.5980, -492.1840], [-202.4970, -494.2900], [-199.6650, -496.0700], [-194.5850, -499.0550], [-191.3240, -500.8970],
        [-187.8020, -502.7840], [-184.8050, -504.3090], [-182.3140, -505.4910], [-179.2210, -506.8520], [-176.0910, -508.1330],
        [-172.6330, -509.4340], [-168.8550, -510.7860], [-165.6410, -511.8430], [-161.2700, -513.2050], [-158.9000, -513.8600],
        [-151.6860, -515.6660], [-149.5470, -516.1520], [-147.6710, -516.5100], [-140.3030, -517.6090], [-135.5330, -518.3630],
        [-133.9100, -518.5660], [-132.2510, -518.7120], [-130.2150, -518.8110], [-127.4480, -518.8540], [-114.8490, -518.7920],
        [-114.4520, -515.8480], [-114.2390, -513.5110], [-114.1280, -511.1210], [-114.0810, -507.6490], [-114.1750, -373.6580],
        [-114.2550, -369.5000], [-114.3360, -368.1410], [-114.4650, -366.8070], [-114.6530, -365.5000], [-114.9010, -364.2210],
        [-115.6290, -361.4180], [-269.5850, -361.2920], [-271.5750, -363.2820], [-271.5360, -370.2640], [-271.4580, -372.6710]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74]
    ], convexity = 30);
}

module photo_loop_8() {
    polygon(points = [
        [-518.7470, -132.2110], [-518.6020, -133.8670], [-518.3990, -135.4880], [-517.6470, -140.2510], [-516.5510, -147.6080],
        [-516.1950, -149.4820], [-515.7100, -151.6170], [-513.9090, -158.8200], [-513.2570, -161.1880], [-511.8970, -165.5520],
        [-510.8390, -168.7600], [-509.6840, -171.9510], [-508.3550, -175.4000], [-506.7400, -179.3680], [-505.5430, -182.1730],
        [-504.3840, -184.6610], [-503.0120, -187.3850], [-500.4200, -192.2980], [-498.7040, -195.3710], [-496.8460, -198.4600],
        [-494.6950, -201.7990], [-492.1190, -205.6290], [-489.7380, -209.0250], [-487.7270, -211.7380], [-485.8240, -214.1460],
        [-483.1750, -217.3460], [-481.2170, -219.5920], [-476.1900, -225.0370], [-474.3370, -226.9590], [-472.6440, -228.5920],
        [-467.0710, -233.7800], [-465.3230, -235.3210], [-463.2800, -236.9960], [-458.6350, -240.6120], [-456.0120, -242.5690],
        [-453.5930, -244.2500], [-447.9000, -248.0370], [-445.7170, -249.4160], [-443.2500, -250.8620], [-438.8820, -253.2610],
        [-435.6060, -254.9700], [-432.5730, -256.4340], [-428.1130, -258.4580], [-424.4570, -260.0490], [-421.6250, -261.2070],
        [-418.4870, -262.3600], [-414.1880, -263.8000], [-410.7020, -264.8730], [-405.7110, -266.3320], [-403.6070, -266.8740],
        [-401.4660, -267.3570], [-394.4050, -268.8620], [-391.5890, -269.3760], [-388.6820, -269.7580], [-382.0870, -270.4410],
        [-376.1170, -271.0090], [-372.7520, -271.2310], [-370.0110, -271.2840], [-367.2640, -271.2050], [-364.8900, -271.0080],
        [-362.2210, -270.6480], [-361.8200, -267.7030], [-361.6040, -265.3640], [-361.4900, -262.9740], [-361.4390, -259.5010],
        [-361.3660, -125.1130], [-361.4000, -123.0340], [-361.4830, -121.3390], [-361.6200, -120.0320], [-361.7850, -119.0980],
        [-362.0210, -118.2200], [-362.3420, -117.4130], [-362.7590, -116.6880], [-363.2760, -116.0560], [-363.8930, -115.5220],
        [-364.6050, -115.0870], [-365.4000, -114.7450], [-366.5670, -114.4170], [-367.8270, -114.2090], [-369.1480, -114.0870],
        [-370.8510, -114.0110], [-372.9310, -113.9790], [-507.6730, -114.0510], [-511.1470, -114.1030], [-513.5370, -114.2170],
        [-515.8750, -114.4320], [-518.8210, -114.8340], [-518.8860, -127.4140], [-518.8450, -130.1780]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88]
    ], convexity = 30);
}



// M ATTACHMENT. Values and coordinates below are finished millimetres.
// Records: [M section (0-based), knot section (0-based), XY].
// Locator records also store [secondary slot?, baseline angle].
mount_bearing_z = letter_back_z*uniform_scale;
screw_pilot_diameter = 3.175;
screw_pilot_depth = 8.7;
screw_clearance_diameter = 4;
screw_counterbore_diameter = 12;
screw_seat_skin = 4;
washer_thickness = 1;
screw_length = 12.7;
dowel_diameter = 4;
dowel_projection = 3;
dowel_hole_depth = 3.3;
assert(abs(mount_bearing_z-13.5)<.000001);
assert(letter_depth*uniform_scale-screw_pilot_depth>=1.8-.000001);
assert(screw_pilot_depth-(screw_length-washer_thickness-screw_seat_skin)>=1-.000001);
assert(dowel_clearance>=.1 && dowel_clearance<=.4);
assert(dowel_slot_relief>=.4 && dowel_slot_relief<=1.2);
assert(mount_index>=1 && mount_index<=len(screw_mounts) && floor(mount_index)==mount_index);

module mount_xy(xy) { translate([xy[0],xy[1],0]) children(); }

module M_pilot() {
    // Blind bore wholly inside the original M body; no geometry below its rear.
    translate([0,0,-.02]) cylinder(d=screw_pilot_diameter,h=screw_pilot_depth+.02,$fn=64);
}
module frame_screw_cuts() {
    seat_rear=mount_bearing_z-screw_seat_skin;
    // Rear counterbore and straight clearance through the full-height knot rail.
    translate([0,0,-.02]) cylinder(d=screw_counterbore_diameter,h=seat_rear+.02,$fn=96);
    translate([0,0,seat_rear-.01]) cylinder(d=screw_clearance_diameter,h=screw_seat_skin+.03,$fn=64);
}
module locating_dowel() {
    // Root directly in the full-height knot rail. No pedestal over the weave.
    top=letter_back_z*uniform_scale;
    translate([0,0,top-.02]) cylinder(d=dowel_diameter,h=dowel_projection-.5+.02,$fn=64);
    translate([0,0,top+dowel_projection-.5]) cylinder(d1=dowel_diameter,d2=dowel_diameter-.6,h=.5,$fn=64);
}
module locating_hole(secondary,angle) {
    rotate([0,0,angle]) {
        // Relief is axial only; the pair constrains both translation and rotation.
        hull() for(x=secondary ? [-dowel_slot_relief/2,dowel_slot_relief/2] : [0])
            translate([x,0,-.02]) cylinder(d=dowel_diameter+dowel_clearance,h=dowel_hole_depth+.02,$fn=64);
        hull() for(x=secondary ? [-dowel_slot_relief/2,dowel_slot_relief/2] : [0])
            translate([x,0,-.01]) cylinder(d1=dowel_diameter+dowel_clearance+.6,d2=dowel_diameter+dowel_clearance,h=.46,$fn=64);
    }
}
module section_evaluate() {
    // A close-up evaluates its entire boolean tree once. Nested F5 renders
    // would tessellate and re-import intermediate frame solids in OpenSCAD 2021.
    if($preview && (view_mode=="mount_detail" || view_mode=="joint_detail")) children();
    else render(convexity=50) children();
}
module section_csg(kind,i) {
    section_evaluate() difference() {
        union() {
            unmounted_section_csg(kind,i);
            if(kind=="frame") for(d=dowel_mounts) if(d[1]==i) mount_xy(d[2]) locating_dowel();
        }
        if(kind=="M") {
            for(m=screw_mounts) if(m[0]==i) mount_xy(m[2]) M_pilot();
            for(d=dowel_mounts) if(d[0]==i) mount_xy(d[2]) locating_hole(d[3],d[4]);
        } else for(m=screw_mounts) if(m[1]==i) mount_xy(m[2]) frame_screw_cuts();
    }
}
module screw_preview() {
    // Nominal envelope only, not a printable or specified thread/head model.
    // 12.7 mm under-head length; selected metal #6-19 pan-head screw.
    under_head=mount_bearing_z-screw_seat_skin-washer_thickness;
    translate([0,0,under_head]) cylinder(d=3.5,h=screw_length,$fn=40);
    translate([0,0,under_head-2.5]) cylinder(d=7,h=2.5,$fn=64);
}
module mount_hardware_preview() {
    // Background modifiers keep metal hardware and loose washers out of exports.
    if($preview && show_mount_hardware) for(m=screw_mounts) mount_xy(m[2]) {
        %color([.55,.57,.6]) screw_preview();
        %color([.85,.65,.25]) translate([0,0,mount_bearing_z-screw_seat_skin-washer_thickness]) tested_mount_washer();
    }
}
module mount_detail() {
    m=screw_mounts[mount_index-1];
    // Use native CSG for boolean close-ups; avoid re-booleaning preview meshes.
    translate([-m[2][0],-m[2][1],0]) {
        color(knot_colour) render(convexity=50) intersection() {
            section_csg("frame",m[1]);
            mount_xy(m[2]) translate([-22,mount_cutaway ? 0 : -22,-4]) cube([44,mount_cutaway ? 22 : 44,40]);
        }
        color(letter_colour) translate([0,0,letter_back_z*uniform_scale+mount_explode])
            render(convexity=50) intersection() {
                section_csg("M",m[0]);
                mount_xy(m[2]) translate([-22,mount_cutaway ? 0 : -22,-7]) cube([44,mount_cutaway ? 22 : 44,22]);
            }
        if($preview && show_mount_hardware) mount_xy(m[2]) {
            %color([.5,.53,.57]) screw_preview();
            %color([.85,.65,.25]) translate([0,0,mount_bearing_z-screw_seat_skin-washer_thickness]) tested_mount_washer();
        }
    }
}
module mount_map() {
    // Plan for inspection; mount labels are never added to the print geometry.
    color([.82,.85,.82]) linear_extrude(height=.05)
        scale([uniform_scale,uniform_scale]) fabric_outline();
    color([.61,.69,.64]) translate([0,0,.07]) linear_extrude(height=.02)
        scale([uniform_scale,uniform_scale]) knot_outline();
    color(letter_colour) translate([0,0,.1]) linear_extrude(height=.05)
        scale([uniform_scale,uniform_scale]) letter_outline();
    for(k=[0:len(screw_mounts)-1]) mount_xy(screw_mounts[k][2]) translate([0,0,.3]) {
        color("firebrick") linear_extrude(height=.05) circle(d=12,$fn=48);
        color("black") translate([8,0]) linear_extrude(height=.05) text(str("S",k+1),size=6);
    }
    for(k=[0:len(dowel_mounts)-1]) mount_xy(dowel_mounts[k][2]) translate([0,0,.4]) {
        color("steelblue") linear_extrude(height=.05) circle(d=4,$fn=32);
        color("black") translate([5,0]) linear_extrude(height=.05) text(str("D",k+1),size=5);
    }
}

// Exact washer polyhedron from the tested SCAD reference.
module tested_mount_washer() {
 polyhedron(points=[[-4.263200759887695,-2.612492799758911,0.0],[-4.0450849533081055,-2.9389262199401855,0.0],[-4.263200759887695,-2.612492799758911,1.0],[-3.802029848098755,-3.2472403049468994,0.0],[-4.0450849533081055,-2.9389262199401855,1.0],[-3.2472403049468994,-3.802029848098755,0.0],[-2.9389262199401855,-4.0450849533081055,0.0],[-3.2472403049468994,-3.802029848098755,1.0],[-2.612492799758911,-4.263200759887695,0.0],[-2.9389262199401855,-4.0450849533081055,1.0],[-3.535533905029297,-3.535533905029297,1.0],[-3.535533905029297,-3.535533905029297,0.0],[-3.802029848098755,-3.2472403049468994,1.0],[-4.455032825469971,-2.2699525356292725,0.0],[-4.6193976402282715,-1.9134172201156616,0.0],[-4.455032825469971,2.2699525356292725,0.0],[-4.755282402038574,-1.5450849533081055,0.0],[-4.861849784851074,-1.167226791381836,0.0],[-4.755282402038574,1.5450849533081055,0.0],[-4.938441753387451,-0.7821723222732544,0.0],[-4.861849784851074,1.167226791381836,0.0],[-4.984586715698242,-0.3922954797744751,0.0],[-4.938441753387451,0.7821723222732544,0.0],[-4.6193976402282715,1.9134172201156616,0.0],[-4.263200759887695,2.612492799758911,0.0],[-4.0450849533081055,2.9389262199401855,0.0],[-3.802029848098755,3.2472403049468994,0.0],[-2.9389262199401855,4.0450849533081055,0.0],[-2.612492799758911,4.263200759887695,0.0],[-3.535533905029297,3.535533905029297,0.0],[-3.2472403049468994,3.802029848098755,0.0],[-4.455032825469971,-2.2699525356292725,1.0],[-4.6193976402282715,-1.9134172201156616,1.0],[-4.755282402038574,-1.5450849533081055,1.0],[-4.861849784851074,-1.167226791381836,1.0],[-4.938441753387451,-0.7821723222732544,1.0],[-4.984586715698242,-0.3922954797744751,1.0],[-5.0,-0.0,1.0],[-5.0,-0.0,0.0],[-1.5450849533081055,-4.755282402038574,0.0],[-1.111140489578247,-1.662939190864563,0.0],[-1.167226791381836,-4.861849784851074,0.0],[-2.2699525356292725,-4.455032825469971,0.0],[-1.8477590084075928,-0.7653668522834778,0.0],[-1.9134172201156616,-4.6193976402282715,0.0],[-1.4142135381698608,-1.4142135381698608,0.0],[-1.2687865495681763,-1.5460208654403687,0.0],[-0.7653668522834778,-1.8477590084075928,0.0],[-0.7821723222732544,-4.938441753387451,0.0],[-0.39018064737319946,-1.9615705013275146,0.0],[-0.3922954797744751,-4.984586715698242,0.0],[0.0,-2.0,0.0],[0.0,-5.0,0.0],[-0.9427934885025024,-1.7638425827026367,0.0],[-0.580569326877594,-1.913880705833435,0.0],[-0.1960342824459076,-1.990369439125061,0.0],[-2.2699525356292725,-4.455032825469971,1.0],[-2.612492799758911,-4.263200759887695,1.0],[-1.9134172201156616,-4.6193976402282715,1.0],[-1.5450849533081055,-4.755282402038574,1.0],[-1.167226791381836,-4.861849784851074,1.0],[-0.7821723222732544,-4.938441753387451,1.0],[-0.3922954797744751,-4.984586715698242,1.0],[-1.913880705833435,-0.580569326877594,0.0],[-2.2699525356292725,4.455032825469971,0.0],[-1.9615705013275146,-0.39018064737319946,0.0],[-1.990369439125061,-0.1960342824459076,0.0],[-2.0,0.0,0.0],[-1.990369439125061,0.1960342824459076,0.0],[-1.7638425827026367,-0.9427934885025024,0.0],[-1.662939190864563,-1.111140489578247,0.0],[-1.5460208654403687,-1.2687865495681763,0.0],[-4.455032825469971,2.2699525356292725,1.0],[-4.755282402038574,1.5450849533081055,1.0],[-4.861849784851074,1.167226791381836,1.0],[-4.938441753387451,0.7821723222732544,1.0],[-4.6193976402282715,1.9134172201156616,1.0],[-4.263200759887695,2.612492799758911,1.0],[-4.0450849533081055,2.9389262199401855,1.0],[-3.802029848098755,3.2472403049468994,1.0],[-2.9389262199401855,4.0450849533081055,1.0],[-2.612492799758911,4.263200759887695,1.0],[-3.535533905029297,3.535533905029297,1.0],[-3.2472403049468994,3.802029848098755,1.0],[0.0,-5.0,1.0],[-1.913880705833435,-0.580569326877594,1.0],[-1.5460208654403687,-1.2687865495681763,1.0],[-1.2687865495681763,-1.5460208654403687,1.0],[-1.4142135381698608,-1.4142135381698608,1.0],[-0.9427934885025024,-1.7638425827026367,1.0],[-0.580569326877594,-1.913880705833435,1.0],[0.0,-2.0,1.0],[-1.111140489578247,-1.662939190864563,1.0],[-0.7653668522834778,-1.8477590084075928,1.0],[-0.1960342824459076,-1.990369439125061,1.0],[-0.39018064737319946,-1.9615705013275146,1.0],[-1.8477590084075928,-0.7653668522834778,1.0],[-2.2699525356292725,4.455032825469971,1.0],[-1.9615705013275146,-0.39018064737319946,1.0],[-1.990369439125061,-0.1960342824459076,1.0],[-2.0,-0.0,1.0],[-1.990369439125061,0.1960342824459076,1.0],[-1.662939190864563,-1.111140489578247,1.0],[-1.7638425827026367,-0.9427934885025024,1.0],[-4.984586715698242,0.3922954797744751,0.0],[-4.984586715698242,0.3922954797744751,1.0],[-1.9134172201156616,4.6193976402282715,0.0],[-1.9615705013275146,0.39018064737319946,0.0],[-1.913880705833435,0.580569326877594,0.0],[-1.8477590084075928,0.7653668522834778,0.0],[-1.7638425827026367,0.9427934885025024,0.0],[-1.5450849533081055,4.755282402038574,0.0],[-1.662939190864563,1.111140489578247,0.0],[-1.5460208654403687,1.2687865495681763,0.0],[-1.4142135381698608,1.4142135381698608,0.0],[-1.167226791381836,4.861849784851074,0.0],[-1.2687865495681763,1.5460208654403687,0.0],[-1.111140489578247,1.662939190864563,0.0],[-0.9427934885025024,1.7638425827026367,0.0],[-0.7821723222732544,4.938441753387451,0.0],[-0.7653668522834778,1.8477590084075928,0.0],[-0.580569326877594,1.913880705833435,0.0],[-0.3922954797744751,4.984586715698242,0.0],[-0.39018064737319946,1.9615705013275146,0.0],[-0.1960342824459076,1.990369439125061,0.0],[-0.0,5.0,0.0],[0.0,2.0,0.0],[-1.9134172201156616,4.6193976402282715,1.0],[-1.5450849533081055,4.755282402038574,1.0],[-1.167226791381836,4.861849784851074,1.0],[-0.7821723222732544,4.938441753387451,1.0],[-0.3922954797744751,4.984586715698242,1.0],[0.0,5.0,1.0],[-1.9615705013275146,0.39018064737319946,1.0],[-1.913880705833435,0.580569326877594,1.0],[-1.8477590084075928,0.7653668522834778,1.0],[-1.7638425827026367,0.9427934885025024,1.0],[-1.662939190864563,1.111140489578247,1.0],[-1.5460208654403687,1.2687865495681763,1.0],[-1.4142135381698608,1.4142135381698608,1.0],[-1.2687865495681763,1.5460208654403687,1.0],[-1.111140489578247,1.662939190864563,1.0],[-0.9427934885025024,1.7638425827026367,1.0],[-0.7653668522834778,1.8477590084075928,1.0],[-0.580569326877594,1.913880705833435,1.0],[-0.39018064737319946,1.9615705013275146,1.0],[-0.1960342824459076,1.990369439125061,1.0],[0.0,2.0,1.0],[0.1960342824459076,-1.990369439125061,0.0],[0.3922954797744751,-4.984586715698242,0.0],[0.580569326877594,-1.913880705833435,0.0],[0.7821723222732544,-4.938441753387451,0.0],[0.9427934885025024,-1.7638425827026367,0.0],[1.167226791381836,-4.861849784851074,0.0],[0.39018064737319946,-1.9615705013275146,0.0],[0.7653668522834778,-1.8477590084075928,0.0],[1.111140489578247,-1.662939190864563,0.0],[1.2687865495681763,-1.5460208654403687,0.0],[1.4142135381698608,-1.4142135381698608,0.0],[1.5450849533081055,-4.755282402038574,0.0],[1.7638425827026367,-0.9427934885025024,0.0],[1.9134172201156616,-4.6193976402282715,0.0],[0.3922954797744751,-4.984586715698242,1.0],[0.7821723222732544,-4.938441753387451,1.0],[1.167226791381836,-4.861849784851074,1.0],[1.5450849533081055,-4.755282402038574,1.0],[2.2699525356292725,-4.455032825469971,0.0],[1.9134172201156616,-4.6193976402282715,1.0],[2.612492799758911,-4.263200759887695,0.0],[2.2699525356292725,-4.455032825469971,1.0],[1.5460208654403687,-1.2687865495681763,0.0],[1.662939190864563,-1.111140489578247,0.0],[1.8477590084075928,-0.7653668522834778,0.0],[1.913880705833435,-0.580569326877594,0.0],[1.9615705013275146,-0.39018064737319946,0.0],[1.990369439125061,-0.1960342824459076,0.0],[2.2699525356292725,4.455032825469971,0.0],[2.612492799758911,4.263200759887695,0.0],[2.9389262199401855,-4.0450849533081055,0.0],[2.612492799758911,-4.263200759887695,1.0],[3.2472403049468994,-3.802029848098755,0.0],[2.9389262199401855,-4.0450849533081055,1.0],[3.535533905029297,-3.535533905029297,0.0],[3.2472403049468994,-3.802029848098755,1.0],[3.802029848098755,-3.2472403049468994,0.0],[3.535533905029297,-3.535533905029297,1.0],[4.0450849533081055,-2.9389262199401855,0.0],[3.802029848098755,-3.2472403049468994,1.0],[4.263200759887695,-2.612492799758911,0.0],[4.0450849533081055,-2.9389262199401855,1.0],[2.9389262199401855,4.0450849533081055,0.0],[3.2472403049468994,3.802029848098755,0.0],[3.535533905029297,3.535533905029297,0.0],[3.802029848098755,3.2472403049468994,0.0],[4.0450849533081055,2.9389262199401855,0.0],[4.263200759887695,2.612492799758911,0.0],[4.455032825469971,2.2699525356292725,0.0],[4.455032825469971,-2.2699525356292725,0.0],[4.6193976402282715,1.9134172201156616,0.0],[4.6193976402282715,-1.9134172201156616,0.0],[4.755282402038574,1.5450849533081055,0.0],[4.755282402038574,-1.5450849533081055,0.0],[4.861849784851074,1.167226791381836,0.0],[4.861849784851074,-1.167226791381836,0.0],[4.938441753387451,0.7821723222732544,0.0],[4.938441753387451,-0.7821723222732544,0.0],[4.984586715698242,0.3922954797744751,0.0],[4.984586715698242,-0.3922954797744751,0.0],[4.263200759887695,-2.612492799758911,1.0],[4.455032825469971,-2.2699525356292725,1.0],[4.6193976402282715,-1.9134172201156616,1.0],[4.755282402038574,-1.5450849533081055,1.0],[4.861849784851074,-1.167226791381836,1.0],[4.938441753387451,-0.7821723222732544,1.0],[5.0,0.0,0.0],[4.984586715698242,-0.3922954797744751,1.0],[0.39018064737319946,-1.9615705013275146,1.0],[0.7653668522834778,-1.8477590084075928,1.0],[0.1960342824459076,-1.990369439125061,1.0],[0.580569326877594,-1.913880705833435,1.0],[0.9427934885025024,-1.7638425827026367,1.0],[1.111140489578247,-1.662939190864563,1.0],[1.2687865495681763,-1.5460208654403687,1.0],[1.662939190864563,-1.111140489578247,1.0],[1.4142135381698608,-1.4142135381698608,1.0],[1.5460208654403687,-1.2687865495681763,1.0],[1.7638425827026367,-0.9427934885025024,1.0],[1.8477590084075928,-0.7653668522834778,1.0],[1.913880705833435,-0.580569326877594,1.0],[1.9615705013275146,-0.39018064737319946,1.0],[1.990369439125061,-0.1960342824459076,1.0],[2.2699525356292725,4.455032825469971,1.0],[2.612492799758911,4.263200759887695,1.0],[5.0,0.0,1.0],[2.9389262199401855,4.0450849533081055,1.0],[3.2472403049468994,3.802029848098755,1.0],[3.535533905029297,3.535533905029297,1.0],[3.802029848098755,3.2472403049468994,1.0],[4.0450849533081055,2.9389262199401855,1.0],[4.263200759887695,2.612492799758911,1.0],[4.455032825469971,2.2699525356292725,1.0],[4.6193976402282715,1.9134172201156616,1.0],[4.755282402038574,1.5450849533081055,1.0],[4.861849784851074,1.167226791381836,1.0],[4.938441753387451,0.7821723222732544,1.0],[4.984586715698242,0.3922954797744751,1.0],[1.9134172201156616,4.6193976402282715,0.0],[1.8477590084075928,0.7653668522834778,0.0],[1.7638425827026367,0.9427934885025024,0.0],[1.662939190864563,1.111140489578247,0.0],[1.5460208654403687,1.2687865495681763,0.0],[1.4142135381698608,1.4142135381698608,0.0],[2.0,0.0,0.0],[1.990369439125061,0.1960342824459076,0.0],[1.9615705013275146,0.39018064737319946,0.0],[1.913880705833435,0.580569326877594,0.0],[0.3922954797744751,4.984586715698242,0.0],[0.1960342824459076,1.990369439125061,0.0],[0.39018064737319946,1.9615705013275146,0.0],[0.7821723222732544,4.938441753387451,0.0],[0.580569326877594,1.913880705833435,0.0],[0.7653668522834778,1.8477590084075928,0.0],[1.167226791381836,4.861849784851074,0.0],[1.111140489578247,1.662939190864563,0.0],[0.9427934885025024,1.7638425827026367,0.0],[1.5450849533081055,4.755282402038574,0.0],[1.2687865495681763,1.5460208654403687,0.0],[0.3922954797744751,4.984586715698242,1.0],[0.7821723222732544,4.938441753387451,1.0],[1.167226791381836,4.861849784851074,1.0],[1.5450849533081055,4.755282402038574,1.0],[1.9134172201156616,4.6193976402282715,1.0],[1.4142135381698608,1.4142135381698608,1.0],[1.5460208654403687,1.2687865495681763,1.0],[1.7638425827026367,0.9427934885025024,1.0],[1.8477590084075928,0.7653668522834778,1.0],[1.662939190864563,1.111140489578247,1.0],[2.0,0.0,1.0],[1.990369439125061,0.1960342824459076,1.0],[1.9615705013275146,0.39018064737319946,1.0],[1.913880705833435,0.580569326877594,1.0],[0.1960342824459076,1.990369439125061,1.0],[0.39018064737319946,1.9615705013275146,1.0],[0.580569326877594,1.913880705833435,1.0],[0.7653668522834778,1.8477590084075928,1.0],[0.9427934885025024,1.7638425827026367,1.0],[1.111140489578247,1.662939190864563,1.0],[1.2687865495681763,1.5460208654403687,1.0]],
 faces=[[2,1,0],[1,4,3],[7,6,5],[9,8,6],[11,10,5],[12,11,3],[15,14,13],[18,17,16],[20,19,17],[22,21,19],[23,16,14],[24,13,0],[1,25,0],[26,1,3],[6,27,5],[8,28,6],[11,29,3],[30,11,5],[13,31,0],[14,32,13],[16,33,14],[17,34,16],[19,35,17],[21,36,19],[38,37,21],[41,40,39],[44,43,42],[39,45,44],[46,45,39],[40,46,39],[48,47,41],[50,49,48],[52,51,50],[47,53,41],[53,40,41],[54,47,48],[49,54,48],[55,49,50],[51,55,50],[56,44,42],[57,42,8],[58,39,44],[59,41,39],[60,48,41],[61,50,48],[62,52,50],[43,63,42],[42,64,8],[63,65,42],[65,66,42],[66,67,42],[67,68,42],[70,69,44],[45,71,44],[71,70,44],[69,43,44],[4,12,3],[2,4,1],[7,9,6],[9,57,8],[12,10,11],[10,7,5],[32,31,13],[34,33,16],[33,32,14],[31,2,0],[35,34,17],[36,35,19],[37,36,21],[32,72,31],[34,73,33],[35,74,34],[36,75,35],[33,76,32],[31,77,2],[78,4,2],[4,79,12],[80,9,7],[81,57,9],[82,10,12],[10,83,7],[57,56,42],[56,58,44],[58,59,39],[59,60,41],[60,61,48],[61,62,50],[84,52,62],[85,58,56],[86,59,58],[87,60,59],[88,87,59],[89,61,60],[90,62,61],[91,84,62],[87,92,60],[92,89,60],[89,93,61],[93,90,61],[95,94,62],[90,95,62],[94,91,62],[85,96,58],[97,56,57],[98,85,56],[99,98,56],[100,99,56],[101,100,56],[103,102,58],[102,86,58],[96,103,58],[86,88,59],[104,38,21],[22,104,21],[20,22,19],[18,20,17],[23,18,16],[15,23,14],[24,15,13],[25,24,0],[26,25,1],[29,26,3],[30,29,11],[27,30,5],[28,27,6],[104,105,38],[22,75,104],[20,74,22],[18,73,20],[23,76,18],[15,72,23],[24,77,15],[25,78,24],[26,79,25],[29,82,26],[30,83,29],[27,80,30],[28,81,27],[68,106,42],[64,28,8],[106,64,42],[68,107,106],[107,108,106],[108,109,106],[109,110,106],[110,112,111],[112,113,111],[113,114,111],[114,116,115],[110,111,106],[114,115,111],[116,117,115],[117,118,115],[118,120,119],[120,121,119],[121,123,122],[123,124,122],[124,126,125],[118,119,115],[121,122,119],[124,125,122],[64,97,28],[106,127,64],[111,128,106],[115,129,111],[119,130,115],[122,131,119],[125,132,122],[105,37,38],[75,105,104],[74,75,22],[73,74,20],[76,73,18],[72,76,23],[77,72,15],[37,105,36],[105,75,36],[75,74,35],[74,73,34],[73,76,33],[76,72,32],[72,77,31],[77,78,2],[78,79,4],[79,82,12],[82,83,10],[83,80,7],[80,81,9],[78,77,24],[79,78,25],[82,79,26],[83,82,29],[80,83,30],[81,80,27],[127,101,56],[81,97,57],[97,127,56],[133,101,127],[134,133,127],[135,134,127],[136,135,127],[137,136,127],[138,137,128],[139,138,128],[97,81,28],[127,97,64],[128,127,106],[129,128,111],[130,129,115],[131,130,119],[132,131,122],[140,139,128],[128,137,127],[129,140,128],[141,140,129],[142,141,129],[143,142,129],[144,143,130],[145,144,130],[146,145,131],[147,146,131],[130,143,129],[131,145,130],[132,147,131],[149,148,52],[151,150,149],[153,152,151],[148,51,52],[154,148,149],[150,154,149],[155,150,151],[152,155,151],[156,152,153],[157,156,153],[159,158,153],[161,160,159],[158,157,153],[84,149,52],[162,151,149],[163,153,151],[164,159,153],[165,161,159],[167,166,161],[169,168,166],[170,158,159],[171,170,159],[160,171,159],[172,160,161],[173,172,161],[174,173,161],[175,174,161],[166,176,161],[168,177,166],[176,175,161],[179,178,168],[181,180,178],[183,182,180],[185,184,182],[187,186,184],[189,188,186],[178,190,168],[180,191,178],[182,192,180],[184,193,182],[186,194,184],[188,195,186],[197,196,188],[199,198,197],[201,200,199],[203,202,201],[205,204,203],[207,206,205],[208,197,188],[209,199,197],[210,201,199],[211,203,201],[212,205,203],[213,207,205],[215,214,207],[84,162,149],[162,163,151],[163,164,153],[164,165,159],[165,167,161],[167,169,166],[169,179,168],[91,162,84],[216,163,162],[217,164,163],[91,218,162],[218,216,162],[216,219,163],[219,217,163],[217,220,164],[220,221,164],[221,222,164],[222,165,164],[223,167,165],[222,224,165],[224,225,165],[225,223,165],[223,226,167],[226,227,167],[227,228,167],[228,229,167],[229,230,167],[231,169,167],[232,179,169],[230,231,167],[179,181,178],[181,183,180],[183,185,182],[185,187,184],[187,189,186],[189,208,188],[208,209,197],[209,210,199],[210,211,201],[211,212,203],[212,213,205],[213,215,207],[233,214,215],[234,181,179],[235,183,181],[236,185,183],[237,187,185],[238,189,187],[239,208,189],[240,209,208],[241,210,209],[242,211,210],[243,212,211],[244,213,212],[245,215,213],[248,247,246],[250,249,246],[251,250,246],[249,248,246],[252,175,176],[253,252,176],[254,253,176],[255,254,176],[177,176,166],[247,255,176],[126,257,256],[257,258,256],[258,260,259],[260,261,259],[264,263,262],[261,264,262],[126,256,125],[258,259,256],[261,262,259],[263,266,265],[266,251,265],[251,246,265],[247,176,246],[263,265,262],[256,267,125],[259,268,256],[262,269,259],[265,270,262],[246,271,265],[177,232,176],[176,231,246],[192,191,180],[193,192,182],[190,177,168],[191,190,178],[194,193,184],[195,194,186],[196,195,188],[200,198,199],[214,206,207],[206,204,205],[204,202,203],[202,200,201],[198,196,197],[233,206,214],[245,204,206],[244,202,204],[243,200,202],[242,198,200],[241,196,198],[240,195,196],[193,237,192],[236,191,192],[190,234,177],[191,235,190],[238,193,194],[195,239,194],[273,272,270],[275,274,271],[276,273,271],[274,276,271],[230,277,231],[277,278,231],[278,279,231],[279,280,231],[231,232,169],[280,275,271],[267,132,125],[268,267,256],[269,268,259],[270,269,262],[271,270,265],[231,271,246],[232,231,176],[281,147,267],[283,282,267],[282,281,267],[284,283,268],[285,284,268],[286,285,269],[287,286,269],[267,147,132],[268,283,267],[269,285,268],[272,287,270],[270,287,269],[271,273,270],[231,280,271],[233,245,206],[245,244,204],[244,243,202],[240,239,195],[242,241,198],[243,242,200],[241,240,196],[235,236,183],[236,237,185],[232,234,179],[234,235,181],[237,238,187],[238,239,189],[239,240,208],[241,242,210],[245,233,215],[244,245,213],[243,244,212],[242,243,211],[240,241,209],[236,235,191],[237,236,192],[234,232,177],[235,234,190],[239,238,194],[238,237,193],[86,71,45],[88,45,46],[85,63,43],[98,65,63],[99,66,65],[100,67,66],[103,69,70],[102,70,71],[96,43,69],[87,46,40],[92,40,53],[89,53,47],[93,47,54],[90,54,49],[95,49,55],[51,94,55],[88,86,45],[87,88,46],[85,98,63],[98,99,65],[99,100,66],[86,102,71],[102,103,70],[69,103,96],[96,85,43],[54,90,93],[40,92,87],[89,92,53],[47,93,89],[49,95,90],[55,94,95],[91,94,51],[101,68,67],[133,107,68],[134,108,107],[135,109,108],[136,110,109],[137,112,110],[138,113,112],[139,114,113],[140,116,114],[141,117,116],[142,118,117],[143,120,118],[144,121,120],[145,123,121],[146,124,123],[147,126,124],[100,101,67],[101,133,68],[133,134,107],[108,134,135],[135,136,109],[136,137,110],[137,138,112],[113,138,139],[139,140,114],[140,141,116],[141,142,117],[118,142,143],[143,144,120],[121,144,145],[145,146,123],[124,146,147],[91,51,148],[218,148,154],[216,154,150],[219,150,155],[217,155,152],[220,152,156],[221,156,157],[222,157,158],[224,158,170],[225,170,171],[223,171,160],[226,160,172],[227,172,173],[228,173,174],[229,174,175],[252,230,175],[148,218,91],[216,218,154],[150,219,216],[217,219,155],[152,220,217],[221,220,156],[222,221,157],[224,222,158],[170,225,224],[223,225,171],[226,223,160],[227,226,172],[173,228,227],[229,228,174],[230,229,175],[277,230,252],[281,257,126],[282,258,257],[283,260,258],[284,261,260],[285,264,261],[286,263,264],[287,266,263],[275,247,248],[276,249,250],[274,248,249],[253,277,252],[278,253,254],[279,254,255],[280,255,247],[272,251,266],[273,250,251],[147,281,126],[257,281,282],[258,282,283],[261,284,285],[285,286,264],[263,286,287],[260,283,284],[275,280,247],[248,274,275],[276,274,249],[273,276,250],[278,277,253],[279,278,254],[280,279,255],[287,272,266],[272,273,251]], convexity=20);
}
screw_mounts = [[0,6,[-76.0,162.0]],[0,8,[-262.0,71.0]],[1,6,[-28.0,76.0]],[2,4,[213.0,148.0]],[2,9,[282.0,28.0]],[3,10,[-261.0,-5.0]],[3,15,[-213.0,-170.0]],[4,13,[-29.0,-62.0]],[5,11,[261.0,-25.0]],[5,17,[213.0,-148.0]]];
dowel_mounts = [[0,6,[-23.0,141.0],0,-161.12768730955727],[0,8,[-219.0,74.0],1,-161.12768730955727],[1,3,[33.0,127.0],0,-127.92107839538778],[1,6,[-34.0,41.0],1,-127.92107839538778],[2,3,[71.0,165.0],0,-35.53767779197438],[2,9,[267.0,25.0],1,-35.53767779197438],[3,8,[-219.0,39.0],0,-90.0],[3,15,[-219.0,-157.0],1,-90.0],[4,13,[-35.0,-40.0],0,-84.88268515002737],[4,13,[-23.0,-174.0],1,-84.88268515002737],[5,11,[266.0,-40.0],0,-121.5042667192042],[5,17,[209.0,-133.0],1,-121.5042667192042]];
mount_cache_screws = [[0,6,[-76.0,162.0]],[0,8,[-262.0,71.0]],[1,6,[-28.0,76.0]],[2,4,[213.0,148.0]],[2,9,[282.0,28.0]],[3,10,[-261.0,-5.0]],[3,15,[-213.0,-170.0]],[4,13,[-29.0,-62.0]],[5,11,[261.0,-25.0]],[5,17,[213.0,-148.0]]];
mount_cache_dowels = [[0,6,[-23.0,141.0],0,-161.12768730955727],[0,8,[-219.0,74.0],1,-161.12768730955727],[1,3,[33.0,127.0],0,-127.92107839538778],[1,6,[-34.0,41.0],1,-127.92107839538778],[2,3,[71.0,165.0],0,-35.53767779197438],[2,9,[267.0,25.0],1,-35.53767779197438],[3,8,[-219.0,39.0],0,-90.0],[3,15,[-219.0,-157.0],1,-90.0],[4,13,[-35.0,-40.0],0,-84.88268515002737],[4,13,[-23.0,-174.0],1,-84.88268515002737],[5,11,[266.0,-40.0],0,-121.5042667192042],[5,17,[209.0,-133.0],1,-121.5042667192042]];
mount_preview_ready = false; // Refreshed from the validated native sections with mounts.

// Section geometry is authored in finished mm outside the artwork scale.
assert(overall_width==914.4 && knot_depth==18 && letter_depth==14 &&
       fabric_back_z==12 && fabric_depth==.8 && letter_back_z==18,
       "Section map and tested fits require the original 36-inch dimensions");
assert(show_knot && show_fabric, "Section geometry requires the complete frame core");
assert(part_family=="frame" || part_family=="M");
a1_plate_size = 256;
a1_edge_allowance = 1.5;
function print_footprints(kind) = kind=="frame" ? frame_print_footprints : M_print_footprints;
function part_count(kind) = kind=="frame" ? 20 : 6;
function joint_list(kind) = kind=="frame" ? frame_joints : M_joints;
function placement_list(kind) = kind=="frame" ? frame_placements : M_placements;
function part_colour(i) = [[.72,.81,.85],[.92,.74,.51],[.65,.76,.58],
                           [.82,.64,.69],[.66,.67,.84],[.89,.85,.64]][i%6];
assert(section_index>=1 && section_index<=part_count(part_family) && floor(section_index)==section_index,
       "Select a section in the chosen family (frame 1..20, M 1..6)");

module original_body_mm(kind) {
    scale([uniform_scale,uniform_scale,uniform_scale])
        if(kind=="M") translate([0,0,-letter_back_z]) letter_reference();
        else union() { photo_frame(); fabric_reference(); }
}
module section_envelope(kind,i) {
    union() {
        part_mask(kind,i);
        for(k=[0:len(joint_list(kind))-1])
            if(joint_list(kind)[k][0]==i) joint_domain(kind,k);
    }
}
module local_frame_artwork(i,artwork) {
    intersection() {
        section_envelope("frame",i);
        scale([uniform_scale,uniform_scale])
            if(artwork=="knot") knot_outline();
            else if(artwork=="core") offset(delta=.15) fabric_outline();
            else fabric_pattern();
    }
}
module section_body_mm(kind,i) {
    if(kind=="M") original_body_mm(kind);
    else union() {
        // Clip the 2D artwork first so F5/F6 do not evaluate the entire frame
        // for each section. These are the unchanged source depths and pockets.
        section_evaluate() difference() {
            union() {
                linear_extrude(height=knot_depth*uniform_scale,convexity=30) local_frame_artwork(i,"knot");
                linear_extrude(height=fabric_back_z*uniform_scale,convexity=30) local_frame_artwork(i,"core");
            }
            for(p=frame_photos[i]) translate([0,0,-.02])
                linear_extrude(height=backer_thickness+photo_allowance+.02,convexity=20)
                    scale([uniform_scale,uniform_scale]) offset(delta=u(rabbet_overlap)) photo_opening(p);
            for(t=frame_retainers[i]) scale([uniform_scale,uniform_scale,uniform_scale])
                at_retainer(floor(t/4),t%4) photo_pilot_mm();
        }
        translate([0,0,fabric_back_z*uniform_scale])
            linear_extrude(height=fabric_depth*uniform_scale,convexity=30) local_frame_artwork(i,"weave");
    }
}
module joint_at(j) {
    translate([j[2][0],j[2][1],0]) rotate([0,0,j[3]]) children();
}
module shoulder_prism(socket, span) {
    // The polygon's Y coordinate becomes Z; extrusion runs along the rail width.
    rotate([90,0,0]) linear_extrude(height=span+44,center=true,convexity=10)
        if(socket) tested_socket_void_xz(); else tested_tongue_xz();
}
module joint_tool(kind,k,socket=false) {
    j=joint_list(kind)[k];
    intersection() {
        translate([0,0,-.1]) linear_extrude(height=7) joint_domain(kind,k);
        joint_at(j) union() {
            shoulder_prism(socket,j[4]);
            for(y=j[5]) translate([0,y,socket ? 4.94 : 4.79])
                linear_extrude(height=socket ? 1.36 : 1.21,convexity=10)
                    if(socket) tested_key_pocket(); else tested_key();
        }
    }
}
// OpenSCAD 2021's 32-bit CGAL cache can fail when all complex sections are
// evaluated together in F5. The self-contained preview below uses the checked
// section tessellations; all native CSG construction remains editable above.
// Changing a body parameter automatically falls back to the native CSG preview.
// F6, section export and geometry checks always use the native construction.
function cached_shape_matches(kind) = fabric_style=="woven" && fabric_pitch==8 &&
    fabric_thread_width==2 && backer_thickness==1.6 && photo_allowance==.4 &&
    rabbet_overlap==4 &&
    (kind=="M" || (photo_preview_ready && photo_pilot_diameter==3.175 &&
                   photo_pilot_depth==10.7 && photo_pivot_offset==9.5)) &&
    (kind=="frame" || (dowel_clearance==.2 && dowel_slot_relief==.8)) &&
    screw_mounts==mount_cache_screws && dowel_mounts==mount_cache_dowels &&
    mount_bearing_z==13.5 &&
    screw_pilot_diameter==3.175 && screw_pilot_depth==8.7 &&
    screw_clearance_diameter==4 && screw_counterbore_diameter==12 &&
    screw_seat_skin==4 &&
    dowel_diameter==4 && dowel_projection==3 && dowel_hole_depth==3.3 && mount_preview_ready;
module section_shape(kind,i) {
    if($preview && fast_preview && cached_shape_matches(kind)) preview_section(kind,i);
    else section_csg(kind,i);
}
module unmounted_section_csg(kind,i) {
    section_evaluate() difference() {
        intersection() {
            section_body_mm(kind,i);
            union() {
                translate([0,0,-5]) linear_extrude(height=35,convexity=30) part_mask(kind,i);
                for(k=[0:len(joint_list(kind))-1])
                    if(joint_list(kind)[k][0]==i) joint_tool(kind,k);
            }
        }
        for(k=[0:len(joint_list(kind))-1])
            if(joint_list(kind)[k][1]==i) joint_tool(kind,k,true);
    }
}
module print_section(kind,i) {
    dims=print_footprints(kind)[i];
    assert(max(dims[0],dims[1])<=a1_plate_size-2*a1_edge_allowance, "Section exceeds A1 bed allowance");
    p=placement_list(kind)[i];
    // M has no added rear projections; retain its original rear-down placement.
    // Frame and M both rest on their original rear plane, with zero Z lift.
    translate([-p[1][0],-p[1][1],p[3]]) rotate([0,0,p[0]]) section_shape(kind,i);
}
module preview_id(kind,i,z=15) {
    if(show_section_ids && $preview) {
        p=placement_list(kind)[i][2];
        %color("black") translate([p[0],p[1],z])
            linear_extrude(height=.2) text(str(kind=="frame" ? "F" : "M",i+1),size=9,halign="center",valign="center");
    }
}
module section_group(kind,spread=0) {
    for(i=[0:part_count(kind)-1]) {
        p=placement_list(kind)[i][2];
        translate([spread*p[0]/450,spread*p[1]/450,0]) {
            color(colour_sections ? part_colour(i) : kind=="frame" ? knot_colour : letter_colour)
                section_shape(kind,i);
            preview_id(kind,i);
        }
    }
}
module a1_plate_outline() {
    // Background geometry never appears in a native render/export.
    %color([.3,.35,.4,.3]) translate([0,0,-.5]) linear_extrude(height=.3)
        difference() { square([256,256],center=true); square([253,253],center=true); }
}
module sectioned_model() {
    if(view_mode=="washer") tested_mount_washer();
    else if(view_mode=="mount_detail") mount_detail();
    else if(view_mode=="mount_map") mount_map();
    else if(view_mode=="section") {
        print_section(part_family,section_index-1);
        if($preview && show_plate_outline) a1_plate_outline();
        echo(section=str(part_family=="frame" ? "F" : "M",section_index),
             footprint_mm=print_footprints(part_family)[section_index-1],
             flat_rotation_deg=placement_list(part_family)[section_index-1][0]);
    }
    else if(view_mode=="layout") {
        for(i=[0:part_count(part_family)-1]) translate([(i%5)*280,-floor(i/5)*280,0]) {
            color(part_colour(i)) print_section(part_family,i);
            if($preview) {
                a1_plate_outline();
                %color("black") translate([-123,-123,17]) linear_extrude(height=.2)
                    text(str(part_family=="frame" ? "F" : "M",i+1),size=10);
            }
        }
    } else if(view_mode=="joint_detail") {
        assert(joint_index>=1 && joint_index<=len(joint_list(part_family)));
        j=joint_list(part_family)[joint_index-1];
        for(side=[0:1]) color(part_colour(side)) translate([0,0,side*joint_separation])
            render(convexity=50) intersection() {
                rotate([0,0,-j[3]]) translate([-j[2][0],-j[2][1],0]) section_csg(part_family,j[side]);
                translate([-24,-j[4]/2-12,-4]) cube([65,j[4]+24,22]);
            }
    } else if(view_mode=="frame") section_group("frame");
    else if(view_mode=="M") section_group("M");
    else if(view_mode=="assembly" || view_mode=="exploded") {
        section_group("frame",view_mode=="exploded" ? exploded_distance : 0);
        if(view_mode=="assembly") mount_hardware_preview();
        if(show_letter) translate([0,0,letter_back_z*uniform_scale+(view_mode=="exploded" ? exploded_distance : 0)])
            section_group("M",view_mode=="exploded" ? exploded_distance : 0);
        scale([uniform_scale,uniform_scale,uniform_scale]) {
            if(show_backers) color(backer_colour)
                translate([0,0,view_mode=="exploded" ? -u(exploded_distance) : 0])
                    for(i=[0:7]) photo_backer(i);
            if(show_retainers)
                for(i=[0:7],j=[0:3]) at_retainer(i,j)
                    translate([0,0,view_mode=="exploded" ? -exploded_distance-8 : 0]) photo_retainer_assembly_mm();
        }
    } else scale([uniform_scale,uniform_scale,uniform_scale]) working_model();
}

// Fixed seam schedule: [tongue part, socket part, XY, normal angle, span, key Y offsets].
// Assembly orders are 1-based section IDs; the joint records are 0-based.
frame_joints = [[6,3,[-2.071036265216451,237.31725],0.5,67.30606280863447,[-22.653031404317233,22.346968595682767]],[13,16,[2.071036265216451,-237.31725],0.5,67.30606280863447,[-22.653031404317233,22.346968595682767]],[10,8,[-237.33374999999998,6.071332572077939],89.5,67.30756286575203,[-22.653781432876016,22.346218567123984]],[11,9,[237.31687499999998,-1.929119320901904],90.5,67.30831289431077,[-22.654156447155387,22.345843552844613]],[0,2,[-199.343731684595,373.7923089617217],246.27549818129464,71.79476649477542,[-23.897383247387708,24.102616752612292]],[0,6,[-51.46624470438752,308.80319287203827],246.27549818129464,74.57082549816008,[-24.785412749080038,24.714587250919962]],[2,6,[-94.87122143068353,237.3205426486964],3.0956855258699223,67.56818862726256,[-22.28409431363128,22.71590568636872]],[8,6,[-84.83934196107339,51.82853089626736],3.0956855258699223,67.83802826522013,[-22.419014132610066,22.580985867389934]],[2,5,[-256.9502785508733,235.5391648359575],240.4340507930166,129.16856717650322,[-43.08428358825161,42.91571641174839]],[8,5,[-270.59446108078447,79.03689218416812],132.3328373539281,181.22952372423623,[-60.614761862118115,60.385238137881885]],[18,15,[-235.1122431448957,-301.48022821791994],92.55983623506293,68.49978561041394,[-22.74989280520697,22.75010719479303]],[18,13,[-51.478000828369815,-293.2704331789108],92.55983623506293,68.35428794923101,[-22.677143974615504,22.822856025384496]],[15,12,[-299.65110479706766,-235.3571430581449],175.22774875992204,68.09000398395618,[-22.54500199197809,22.45499800802191]],[10,12,[-284.3155316944427,-51.66380235008155],175.22774875992204,67.88418393425337,[-22.442091967126686,22.557908032873314]],[13,15,[-113.14135327523721,-237.32608490353485],167.03290686727414,69.18311215684032,[-23.09155607842016,22.90844392157984]],[13,10,[-74.14324822238393,-67.96300950015868],167.03290686727414,101.6896398577948,[-33.8448199288974,16.1551800711026]],[10,15,[-237.32879557737652,-125.87183350224907],260.04466308707504,68.45045716433582,[-22.725228582167908,22.774771417832092]],[7,4,[290.9729472052753,236.47994775182224],186.09197319342016,69.29542470009368,[-23.147712350046838,22.852287649953162]],[7,9,[310.69030922590787,51.73500383305869],186.09197319342016,67.87744379037845,[-22.438721895189225,22.561278104810775]],[9,3,[51.68400090044645,91.54314166129507],97.19982173644301,68.04842845216704,[-22.524214226083522,22.475785773916478]],[9,4,[237.33334848822935,114.99552152488454],97.19982173644301,68.06540155741911,[-22.532700778709554,22.467299221290446]],[1,3,[51.76994329757464,341.06213323435054],263.064085517535,68.13210096873851,[-22.566050484369256,22.933949515630744]],[1,4,[229.94618131794877,319.3871096153132],263.064085517535,74.9936261610327,[-24.996813080516347,25.003186919483653]],[4,3,[87.70516870192756,236.91443384526184],179.7404143791258,68.2969433084908,[-22.648471654245398,22.851528345754602]],[14,11,[293.58021184960097,-51.75707130910992],181.82819387346964,67.77201711347882,[-22.386008556739412,22.613991443260588]],[14,17,[299.4405104991239,-235.35708488389156],181.82819387346964,68.27655010604187,[-22.638275053020934,22.861724946979066]],[16,11,[51.39931318451354,-122.89123761445123],90.11856589142248,68.14167540477398,[-22.57083770238699,22.92916229761301]],[17,11,[237.29453882481215,-122.50655195717937],90.11856589142248,67.45172590326939,[-22.725862951634696,22.274137048365304]],[19,16,[51.747198790420995,-355.75938694981653],95.50892191539832,67.98119428892389,[-22.490597144461944,22.509402855538056]],[19,17,[221.0864266834741,-339.427260029702],95.50892191539832,80.46127608868356,[-26.73063804434178,24.26936195565822]],[17,16,[99.66565534938579,-237.28519343313695],181.8196089178243,67.4118324385687,[-22.705916219284347,22.294083780715653]]];
frame_placements = [[60.55,[-356.5525053112046,81.39010299680619],[-51.48915126544857,376.12912500000004],0],[67.9,[-287.25664742875654,254.0815906336483],[175.27957046968828,386.07075],0],[67.45,[-322.2830365160553,-86.38512779343586],[-236.0548516103708,296.12625],0],[45.075,[-119.60799136886924,186.43638323172578],[42.81797872882296,237.31725],0],[0.24999999999999994,[181.21341103519794,218.185199803996],[189.2929192403249,237.36362414031004],0],[2.0000000000000004,[-333.9923678338689,130.07413366500955],[-412.9401849161467,142.16362500000002],0],[46.275000000000006,[-170.09625740762434,75.50962751620699],[-51.448628372899705,138.644625],0],[18.025,[289.94735078443466,234.76838923275682],[412.06872460063295,144.13725],0],[35.324999999999996,[-185.58291062668386,-73.84508790262119],[-192.7067083390698,51.7208111021755],0],[51.85000000000001,[54.08118089666526,172.17129831733467],[164.7275113644408,57.68625],0],[12.950000000000001,[-173.94769460728187,-106.57481043233274],[-177.39465565840342,-51.93038909623876],0],[31.625,[170.00194165998968,30.202324586783583],[156.12780939164176,-63.471374999999995],0],[29.974999999999998,[-247.9330845490531,-276.5348259221449],[-412.4604705659508,-143.277],0],[38.975,[74.19625057342651,-172.40104518877834],[-51.43868405525326,-154.1574954039199],0],[65.5,[253.55434883664321,268.6036082121649],[412.00222790840013,-144.17849999999999],0],[12.975000000000001,[-159.63838877110982,-264.94310781598665],[-206.357875297921,-236.5576850789729],0],[45.925,[200.12176875608054,-124.19299543822345],[50.868855007399866,-237.31725],0],[84.50000000000001,[241.3335771924042,166.30778975380989],[199.56312958381318,-236.63436648520673],0],[64.475,[264.35189076876753,-257.44196908469416],[-193.21485345485056,-374.98199999999997],0],[25.900000000000002,[273.82927786610287,-277.43119284227146],[121.38339583333334,-396.65175],0]];
frame_assembly_order = [1,2,8,15,19,20,3,14,18,11,17,9,16,12,6,7,13,10,5,4];
frame_print_footprints = [[218.70762805290033,218.69092941204204,13.5],[228.8071076700174,228.85599650351907,13.5],[250.63777576151324,250.65743382013636,13.5],[224.21866172925732,224.21618576567397,16.5],[225.1044031914634,213.13564252184779,13.5],[252.4620273979345,252.48346869089136,13.5],[246.1463799890269,246.16626077838367,16.5],[252.00896626568982,252.05580636616003,13.5],[244.12041426888757,244.14507045966863,16.5],[251.83679902308134,251.82503756976868,16.5],[233.87186064938697,177.76011204429582,13.5],[251.60029193209908,251.63535089944986,16.5],[240.89805190143434,240.88421328184316,13.5],[251.91418032183066,251.9149694181428,16.5],[247.73355215475075,247.68259048884255,13.5],[205.3527379226027,181.6030001354123,16.5],[225.3040664001727,225.3463615640864,13.5],[235.45497317399617,222.76487387398737,16.5],[247.8686342603628,247.86940082072877,13.5],[217.6080112227068,217.55730166600097,13.5]];
frame_retainers = [[4,7],[10,11],[5,6],[9],[8,15],[0,1,2,3],[],[12,13,14],[],[],[29],[],[28,31],[],[17,18,19],[24,30],[23],[16,20,21],[25,26,27],[22]];
frame_photos = [[1],[2],[1],[2],[2,3],[0],[1],[3],[0],[3],[7],[4],[7],[6],[4],[6,7],[5],[4,5],[6],[5]];
module frame_mask_0() {
    polygon(points = [
        [-228.0455, 393.4623], [-232.4503, 388.1781], [-232.3431, 388.1310], [-232.2182, 388.2809], [-166.4120, 359.3604],
        [-166.5642, 359.2225], [-166.4514, 359.1729], [-165.0768, 360.4180], [-163.0131, 362.2067], [-160.4254, 364.3442],
        [-158.6142, 365.7682], [-156.7633, 367.1392], [-153.6742, 369.3238], [-151.1962, 371.0153], [-149.1086, 372.3446],
        [-146.5131, 373.8753], [-144.2414, 375.1328], [-140.9692, 376.8603], [-138.7301, 378.0005], [-136.8745, 378.8867],
        [-134.5682, 379.9088], [-132.2298, 380.8740], [-129.6426, 381.8545], [-126.5948, 382.9469], [-124.1872, 383.7386],
        [-120.9117, 384.7598], [-119.1383, 385.2492], [-113.7312, 386.6036], [-112.1311, 386.9671], [-110.7296, 387.2346],
        [-105.2060, 388.0585], [-101.6295, 388.6237], [-100.4174, 388.7753], [-99.1788, 388.8843], [-97.6572, 388.9583],
        [-95.5859, 388.9905], [-86.2680, 388.9454], [-85.9881, 386.8692], [-85.8289, 385.1230], [-85.7460, 383.3370],
        [-85.7108, 380.7365], [-85.7508, 323.7067], [-85.6383, 323.6573], [-85.6382, 323.8620], [-17.2943, 293.8263],
        [-17.2941, 293.6214], [-17.1816, 293.5719], [-17.2860, 397.7594], [-17.3205, 402.2108], [-17.4423, 405.0384],
        [-17.9333, 410.5367], [-18.1017, 412.0130], [-18.3117, 413.4616], [-18.7392, 415.8196], [-19.2689, 418.3757],
        [-19.7197, 420.2021], [-20.1858, 421.7721], [-20.8686, 423.7679], [-21.6167, 425.7393], [-22.3376, 427.4474],
        [-23.1295, 429.1155], [-24.0071, 430.7630], [-25.0907, 432.6099], [-26.3940, 434.6648], [-27.5104, 436.2950],
        [-28.8510, 438.0780], [-30.2802, 439.8036], [-31.7989, 441.4907], [-33.4092, 443.1184], [-34.8961, 444.4667],
        [-36.5862, 445.8598], [-38.6466, 447.4345], [-40.5731, 448.7881], [-42.3788, 449.9460], [-44.2349, 451.0140],
        [-46.1236, 451.9712], [-48.2377, 452.9380], [-50.5882, 453.9174], [-52.7739, 454.7230], [-54.7909, 455.3607],
        [-56.6363, 455.8226], [-59.2323, 456.3150], [-62.8130, 456.8919], [-64.7785, 457.1177], [-66.8087, 457.2442],
        [-70.9811, 457.3050], [-93.0595, 457.3088], [-96.1895, 457.2652], [-98.7371, 457.1291], [-100.4799, 456.9682],
        [-105.6564, 456.3961], [-107.4097, 456.2508], [-111.7114, 455.9605], [-113.2050, 455.8131], [-114.9191, 455.6018],
        [-117.0746, 455.2689], [-121.0632, 454.5322], [-125.1077, 453.8572], [-126.5156, 453.5887], [-127.8965, 453.2818],
        [-131.0758, 452.4986], [-134.9600, 451.5893], [-139.6580, 450.3298], [-142.5280, 449.4993], [-147.3429, 447.9576],
        [-149.5332, 447.1992], [-154.6800, 445.3450], [-157.2186, 444.3641], [-159.5733, 443.3757], [-166.4995, 440.2959],
        [-168.8106, 439.2350], [-171.0696, 438.1243], [-175.8887, 435.6469], [-178.5857, 434.3811], [-180.5504, 433.0778],
        [-184.4078, 430.7589], [-186.6408, 429.3458], [-190.2107, 426.9984], [-194.2345, 424.2556], [-196.2375, 422.8286],
        [-198.1983, 421.3597], [-202.8422, 417.7461], [-204.7676, 416.1931], [-209.1256, 412.4924], [-212.1293, 409.8947],
        [-213.9274, 408.2888], [-215.5130, 406.7822], [-220.5589, 401.7332], [-221.9855, 400.2615], [-223.1908, 398.9405]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129]
    ], convexity = 30);
}

module frame_mask_1() {
    polygon(points = [
        [17.8853, 404.3301], [17.8030, 345.0431], [17.9155, 345.0294], [17.9158, 345.2183], [85.6242, 336.9816],
        [85.6243, 336.7927], [85.7368, 336.7790], [85.7093, 379.7140], [85.7242, 381.8020], [85.7706, 383.3406],
        [85.8420, 384.3317], [85.9709, 385.2743], [86.1792, 386.1450], [86.4007, 386.7298], [86.6879, 387.2493],
        [87.0463, 387.6977], [87.3224, 387.9524], [87.6322, 388.1762], [87.9722, 388.3677], [88.5434, 388.6012],
        [88.9538, 388.7203], [89.6163, 388.8564], [90.8095, 388.9902], [91.8113, 389.0423], [93.3572, 389.0715],
        [96.9995, 389.0483], [99.2901, 388.9406], [101.2548, 388.7338], [106.2436, 387.9213], [111.0261, 387.2038],
        [112.4265, 386.9430], [113.7968, 386.6380], [119.2005, 385.2905], [121.1909, 384.7360], [125.9916, 383.2099],
        [129.4708, 381.9568], [132.0492, 380.9508], [135.4370, 379.5570], [137.3128, 378.7329], [138.9548, 377.9489],
        [142.2052, 376.2757], [145.4940, 374.5103], [147.9390, 373.1092], [150.2628, 371.6845], [152.5247, 370.1818],
        [155.8086, 367.8834], [158.0648, 366.2437], [159.8787, 364.8438], [162.4430, 362.7462], [164.5059, 360.9844],
        [167.7874, 358.0409], [169.6128, 356.3143], [170.8416, 355.0465], [174.9828, 350.5815], [175.9850, 349.4708],
        [176.9533, 348.3365], [178.4901, 346.4126], [181.7784, 342.1610], [183.0660, 340.4071], [184.2866, 338.6319],
        [185.9480, 336.0499], [187.5189, 333.4917], [188.7671, 331.3292], [189.9547, 329.1389], [191.5019, 326.1031],
        [192.6243, 323.7762], [192.7570, 323.7600], [192.6602, 323.9607], [267.1996, 314.8930], [267.2418, 314.6990],
        [267.3601, 314.6846], [266.7470, 317.4980], [266.2924, 319.3039], [264.9613, 324.2113], [264.2654, 326.6450],
        [262.9991, 330.8004], [260.9030, 337.0061], [259.9762, 339.5325], [258.5049, 343.2723], [257.0421, 346.7512],
        [255.5266, 350.2108], [254.1810, 353.0693], [251.5121, 358.4439], [250.4271, 360.5547], [249.2873, 362.6443],
        [246.9852, 366.7584], [245.7790, 368.8254], [243.8573, 371.9212], [241.7353, 375.2126], [240.3484, 377.2520],
        [235.9569, 383.5087], [234.0797, 386.0431], [232.3399, 388.2718], [227.8473, 393.6441], [221.9420, 400.2571],
        [220.3887, 401.8666], [215.4106, 406.8418], [214.1496, 408.0570], [212.8918, 409.2027], [209.4555, 412.1685],
        [204.5296, 416.3455], [202.4091, 418.0426], [197.5675, 421.7960], [194.9946, 423.6811], [191.3423, 426.1947],
        [187.8632, 428.5084], [184.5425, 430.6301], [182.2647, 431.9748], [176.1532, 435.3911], [172.5590, 437.3147],
        [169.7227, 438.7602], [167.0124, 440.0339], [161.6007, 442.4381], [158.4589, 443.7711], [155.1567, 445.1035],
        [152.5891, 446.0693], [147.2509, 447.9332], [143.3835, 449.2174], [140.9901, 449.9556], [136.3475, 451.2712],
        [134.7767, 451.6840], [125.6098, 453.7343], [116.9149, 455.3131], [115.4827, 455.5409], [113.7804, 455.7680],
        [111.2963, 456.0182], [105.7416, 456.4112], [99.0784, 457.1305], [96.2836, 457.2944], [92.3695, 457.3447],
        [73.7121, 457.3500], [69.2496, 457.3410], [66.9099, 457.2944], [64.8766, 457.1755], [62.9071, 456.9564],
        [59.3263, 456.3841], [56.7298, 455.8977], [54.8817, 455.4441], [53.0841, 454.8876], [51.1090, 454.1816],
        [47.2234, 452.6852], [44.9886, 451.9421], [43.0363, 450.4703], [39.7105, 448.1627], [38.2019, 447.0720],
        [36.1757, 445.4923], [34.1362, 443.7394], [32.2893, 441.9873], [30.7056, 440.3147], [29.2391, 438.5727],
        [27.7323, 436.5724], [26.3359, 434.5249], [24.7896, 432.0581], [24.0725, 430.8255], [23.4021, 429.5915],
        [22.8810, 428.5561], [22.2977, 427.3007], [21.7536, 426.0214], [21.1588, 424.4965], [20.6002, 422.9500],
        [20.0857, 421.3929], [19.6949, 420.0443], [19.3530, 418.6743], [18.5883, 414.9519], [18.3423, 413.5274],
        [18.1728, 412.3157], [18.0688, 411.3251], [17.9792, 410.0620], [17.9108, 407.9978]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168]
    ], convexity = 30);
}

module frame_mask_2() {
    polygon(points = [
        [-309.0252, 268.4299], [-313.5429, 267.4713], [-313.3954, 267.3876], [-313.1188, 267.4463], [-200.6439, 203.6400],
        [-200.9960, 203.6242], [-200.8121, 203.5199], [-199.0707, 203.5980], [-194.6132, 203.6415], [-92.8884, 203.4354],
        [-92.8945, 203.5479], [-93.0823, 203.5483], [-96.7353, 271.0928], [-96.5475, 271.0930], [-96.5536, 271.2055],
        [-202.1267, 271.1191], [-203.5310, 272.5233], [-203.5073, 277.4361], [-203.4654, 278.9844], [-203.3868, 280.5097],
        [-203.2266, 282.5141], [-202.8428, 286.4915], [-202.2049, 292.4224], [-201.9546, 294.1017], [-201.6442, 295.7403],
        [-200.4112, 301.4998], [-199.9218, 303.5366], [-199.3012, 305.7420], [-197.9822, 310.1075], [-196.9844, 313.1204],
        [-196.1414, 315.4749], [-195.2927, 317.6013], [-194.1098, 320.3484], [-192.4062, 324.1168], [-191.2227, 326.5976],
        [-189.9660, 329.0608], [-188.7275, 331.3372], [-187.5125, 333.4273], [-186.3443, 335.2945], [-183.7573, 339.1683],
        [-182.3532, 341.1880], [-180.5957, 343.5544], [-177.4751, 347.6291], [-176.3723, 348.9644], [-175.2121, 350.2727],
        [-169.9689, 355.8659], [-168.1448, 357.6391], [-166.2078, 359.3936], [-166.3206, 359.4432], [-166.4729, 359.3053],
        [-232.2682, 388.2210], [-232.1432, 388.3709], [-232.2504, 388.4180], [-232.5232, 388.0907], [-233.9653, 386.2293],
        [-235.3764, 384.3038], [-240.2445, 377.4469], [-241.4996, 375.6216], [-244.2820, 371.3020], [-246.3056, 367.9952],
        [-249.4215, 362.4599], [-250.6365, 360.2267], [-251.7756, 357.9958], [-254.6968, 352.0678], [-256.0357, 349.1332],
        [-258.1017, 344.3099], [-259.1918, 341.6193], [-260.4740, 338.2795], [-261.0758, 336.5831], [-262.9541, 331.0187],
        [-264.1580, 327.0856], [-264.8622, 324.6601], [-266.3141, 319.3093], [-266.7148, 317.7307], [-268.1713, 311.0558],
        [-268.5448, 309.1959], [-268.8612, 307.2974], [-269.5617, 302.4779], [-270.3149, 297.9589], [-270.5075, 296.4999],
        [-270.6586, 295.0137], [-271.0864, 290.0053], [-271.2134, 287.9707], [-271.2832, 285.3776], [-271.3342, 278.8357],
        [-271.3977, 277.3013], [-271.5087, 276.0606], [-271.7003, 274.8668], [-271.9853, 273.7240], [-272.3576, 272.6243],
        [-272.9373, 271.2129], [-285.1870, 271.1385], [-287.5266, 271.0746], [-289.8215, 270.9341], [-295.3333, 270.4590],
        [-297.3020, 270.2387], [-302.0810, 269.4898], [-306.6555, 268.8342]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97]
    ], convexity = 30);
}

module frame_mask_3() {
    polygon(points = [
        [16.5276, 271.1190], [-2.5160, 271.1190], [-2.5150, 271.0065], [-2.3275, 271.0065], [-1.7395, 203.6280],
        [-1.9270, 203.6280], [-1.9261, 203.5155], [16.5284, 203.5155], [16.8512, 202.3502], [17.0530, 201.4961],
        [17.2151, 200.6326], [17.3641, 199.5321], [17.4836, 198.1691], [17.5801, 196.5078], [17.6843, 192.7119],
        [17.7782, 87.1088], [17.8907, 87.1230], [17.8905, 87.3119], [85.4774, 95.8499], [85.4774, 95.6609],
        [85.5899, 95.6752], [85.5893, 193.0290], [85.6305, 197.2001], [85.7005, 198.4575], [85.8110, 199.4170],
        [85.9947, 200.3119], [86.1950, 200.9224], [86.3619, 201.2930], [86.5576, 201.6320], [86.9131, 202.0846],
        [87.3392, 202.4614], [87.7001, 202.6820], [87.7007, 202.8142], [87.5127, 202.6993], [87.8226, 271.1001],
        [88.0101, 271.0999], [88.0106, 271.2124], [86.8213, 271.2134], [86.3060, 273.1983], [86.0118, 274.8791],
        [85.8515, 276.6241], [85.7737, 279.2026], [85.7366, 337.0812], [85.6241, 337.0949], [85.6242, 336.9060],
        [17.9156, 345.1427], [17.9159, 345.3316], [17.8034, 345.3452], [17.7165, 282.6809], [17.6805, 280.6203],
        [17.6087, 278.6267], [17.5023, 276.7304], [17.3888, 275.3670], [17.2472, 274.2586], [17.0924, 273.3837],
        [16.8456, 272.2997]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]
    ], convexity = 30);
}

module frame_mask_4() {
    polygon(points = [
        [202.1138, 271.1190], [87.7106, 271.2127], [87.7101, 271.1002], [87.8976, 271.1000], [87.5879, 202.7452],
        [87.3998, 202.6303], [87.3992, 202.4981], [87.8371, 202.7657], [88.4037, 203.0015], [89.0301, 203.1764],
        [89.7063, 203.2987], [90.6668, 203.4012], [91.6693, 203.4563], [93.2170, 203.4900], [194.5958, 203.6452],
        [199.0533, 203.5995], [202.8527, 203.4276], [203.1354, 201.3423], [203.2961, 199.5931], [203.3798, 197.8034],
        [203.4173, 195.1984], [203.4190, 110.5601], [203.5315, 110.5743], [203.5315, 110.7633], [271.1352, 119.3034],
        [271.1351, 119.1144], [271.2476, 119.1286], [271.3260, 195.3800], [271.4083, 197.9570], [271.4902, 198.9569],
        [271.6175, 199.9345], [271.7467, 200.6486], [271.9647, 201.5815], [272.2290, 202.4929], [272.5694, 203.5149],
        [277.6967, 203.4870], [279.4970, 203.4286], [281.0158, 203.3367], [285.7535, 202.8997], [291.2100, 202.3427],
        [293.1680, 202.1084], [294.8198, 201.8494], [294.8075, 201.9652], [294.6157, 201.9953], [287.2540, 270.9721],
        [287.4438, 270.9605], [287.4317, 271.0740], [287.2366, 271.0859], [283.8484, 271.1542], [272.9202, 271.2130],
        [272.3381, 272.6355], [271.9636, 273.7427], [271.6771, 274.8916], [271.4839, 276.0907], [271.3715, 277.3344],
        [271.3080, 278.8701], [271.2600, 285.4106], [271.1901, 288.0022], [271.0631, 290.0360], [270.6579, 294.7931],
        [270.4850, 296.5283], [270.2924, 297.9870], [269.6405, 302.0357], [268.9437, 306.8453], [268.6220, 308.7408],
        [268.2501, 310.6004], [267.2925, 314.9951], [267.1742, 315.0095], [267.2165, 314.8154], [192.6989, 323.8804],
        [192.6021, 324.0811], [192.4694, 324.0972], [192.9674, 323.0649], [194.3421, 320.0399], [195.4591, 317.3865],
        [196.4014, 314.8784], [197.6256, 311.2447], [198.3778, 308.8594], [199.6121, 304.6872], [200.0341, 303.1227],
        [200.4174, 301.5284], [201.4929, 296.7044], [201.8595, 294.8477], [202.1181, 293.1832], [202.3494, 291.2319],
        [202.9492, 285.2837], [203.3194, 281.0467], [203.4008, 279.5290], [203.4435, 277.7296], [203.4198, 272.3011]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89]
    ], convexity = 30);
}

module frame_mask_5() {
    polygon(points = [
        [-405.5834, 17.9235], [-337.5230, 17.8636], [-337.3996, 17.9760], [-337.6777, 17.9762], [-203.5704, 140.1451],
        [-203.5705, 139.8914], [-203.4580, 139.9939], [-203.4368, 195.2111], [-203.3986, 197.8124], [-203.3141, 199.5991],
        [-203.1527, 201.3460], [-202.8700, 203.4275], [-200.2486, 203.5452], [-200.4326, 203.6495], [-200.7847, 203.6337],
        [-313.2294, 267.4228], [-312.9529, 267.4815], [-313.1004, 267.5652], [-316.1769, 266.9125], [-318.2343, 266.4376],
        [-324.7156, 264.6964], [-328.6800, 263.5315], [-331.7258, 262.5788], [-337.9208, 260.4668], [-342.3068, 258.7844],
        [-346.0064, 257.2562], [-349.6752, 255.6695], [-352.3314, 254.4454], [-358.7464, 251.2765], [-361.4910, 249.8430],
        [-366.6511, 246.9696], [-369.1340, 245.5193], [-373.8786, 242.5409], [-377.1528, 240.3531], [-384.2324, 235.3337],
        [-386.5507, 233.6357], [-388.9357, 231.7585], [-393.2276, 228.1722], [-399.3945, 222.7076], [-400.7154, 221.4942],
        [-406.6363, 215.6146], [-408.6965, 213.4589], [-411.6732, 210.0476], [-416.4861, 204.3838], [-420.4433, 199.3654],
        [-422.6679, 196.4434], [-424.8041, 193.4339], [-428.1067, 188.5449], [-430.5102, 184.8165], [-433.0994, 180.5349],
        [-434.4044, 178.5714], [-435.5697, 176.0790], [-438.4570, 170.4470], [-439.9415, 167.3368], [-442.0449, 162.6175],
        [-443.2968, 159.7159], [-444.6681, 156.3736], [-445.7562, 153.5724], [-448.2205, 146.5240], [-449.2842, 143.2970],
        [-449.9521, 141.1174], [-451.5840, 135.1049], [-453.3879, 127.3573], [-453.6855, 125.9742], [-453.9952, 124.3343],
        [-454.6313, 120.5408], [-455.3890, 116.2938], [-455.7491, 113.8901], [-456.0377, 111.1767], [-456.4127, 105.8835],
        [-457.0373, 100.2031], [-457.2245, 97.9418], [-457.3237, 95.3666], [-457.3500, 91.4367], [-457.3462, 70.4144],
        [-457.3177, 67.8016], [-457.2485, 66.0012], [-457.1341, 64.4914], [-456.9294, 62.7770], [-456.5920, 60.6255],
        [-456.1315, 58.0365], [-455.8409, 56.6505], [-455.4997, 55.2976], [-455.1089, 53.9762], [-454.6065, 52.4562],
        [-453.9831, 50.7333], [-453.3810, 49.2447], [-452.6319, 47.5713], [-451.7269, 45.7093], [-450.9656, 44.2634],
        [-450.1417, 42.8174], [-449.2539, 41.3818], [-448.3098, 39.9713], [-447.4589, 38.7864], [-446.5750, 37.6212],
        [-444.5721, 35.1502], [-442.7643, 33.0981], [-441.8949, 32.1880], [-440.9969, 31.3111], [-439.3352, 29.8527],
        [-437.2792, 28.2608], [-434.7935, 26.5095], [-432.3930, 24.9683], [-430.1461, 23.6742], [-429.1151, 23.1368],
        [-427.8672, 22.5377], [-426.5992, 21.9801], [-425.3049, 21.4549], [-422.2356, 20.3225], [-420.4601, 19.7614],
        [-418.6428, 19.3055], [-415.1413, 18.6270], [-412.7523, 18.2480], [-411.2707, 18.0890], [-409.7491, 17.9934],
        [-407.9382, 17.9423], [-275.3866, 85.8334], [-277.1685, 85.7392], [-279.7655, 85.6958], [-378.1916, 85.6995],
        [-382.3777, 85.7212], [-384.6927, 85.8035], [-386.6960, 85.9820], [-389.0170, 86.3219], [-389.0340, 95.6244],
        [-388.9943, 97.6919], [-388.9144, 99.2097], [-388.8016, 100.4446], [-388.6463, 101.6539], [-388.0787, 105.2240],
        [-387.2975, 110.5021], [-387.0368, 111.9052], [-386.6800, 113.5065], [-385.3309, 118.9054], [-384.8474, 120.6804],
        [-383.9718, 123.5141], [-383.0451, 126.3534], [-382.2656, 128.5279], [-381.2774, 131.1157], [-380.1608, 133.8801],
        [-379.1871, 136.1931], [-378.4314, 137.8533], [-377.5250, 139.6947], [-375.5195, 143.5378], [-374.3056, 145.7528],
        [-372.9910, 147.9808], [-371.4324, 150.4479], [-369.5156, 153.3291], [-367.7256, 155.9193], [-366.2256, 157.9869],
        [-364.8296, 159.7954], [-362.7380, 162.3522], [-360.8142, 164.5981], [-357.8883, 167.8537], [-356.1648, 169.6550],
        [-354.8901, 170.8781], [-350.2138, 175.2141], [-349.0948, 176.2052], [-347.7626, 177.3130], [-344.0996, 180.1749],
        [-341.9780, 181.7662], [-340.2324, 182.9856], [-336.4908, 185.4808], [-334.6714, 186.6517], [-332.8284, 187.7517],
        [-329.7575, 189.4531], [-326.9044, 190.9666], [-324.4665, 192.1799], [-321.8445, 193.4108], [-319.2191, 194.5748],
        [-316.9652, 195.5022], [-314.6587, 196.3549], [-310.1791, 197.8866], [-308.0064, 198.5582], [-304.9150, 199.4355],
        [-303.1201, 199.9048], [-301.5207, 200.2753], [-295.9978, 201.4537], [-293.9011, 201.8456], [-291.7358, 202.1411],
        [-287.2920, 202.6080], [-282.3236, 203.0855], [-279.8103, 203.2621], [-277.7653, 203.3137], [-275.7114, 203.2681],
        [-273.6835, 203.1068], [-271.7994, 202.8527], [-271.4895, 200.5123], [-271.3266, 198.5060], [-271.2525, 196.1890],
        [-271.2353, 192.2637], [-271.2952, 93.8156], [-271.3290, 91.4677], [-271.4104, 89.6653], [-271.5741, 87.8931],
        [-271.7989, 86.2586], [-273.6453, 86.0045]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115],
        [116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196]
    ], convexity = 30);
}

module frame_mask_6() {
    polygon(points = [
        [-86.8378, 271.2134], [-96.8540, 271.2052], [-96.8479, 271.0927], [-96.6602, 271.0929], [-93.0072, 203.5482],
        [-93.1950, 203.5485], [-93.1889, 203.4360], [-86.2678, 203.4220], [-85.9858, 201.3438], [-85.8252, 199.5954],
        [-85.7414, 197.8064], [-85.7040, 195.2029], [-85.7018, 86.7771], [-86.8247, 85.7613], [-86.8169, 85.6167],
        [-86.6379, 85.7786], [-82.9680, 17.9215], [-83.1558, 17.9214], [-83.1497, 17.8089], [-71.6198, 17.8170],
        [-67.6960, 17.8523], [-65.3932, 17.9614], [-63.6602, 18.1414], [-61.9806, 18.4019], [-59.1700, 18.9429],
        [-56.8682, 19.4555], [-55.2975, 19.8780], [-53.5446, 20.4287], [-51.5995, 21.1129], [-49.8864, 21.7832],
        [-48.2016, 22.5244], [-46.3463, 23.4306], [-44.5279, 24.3977], [-42.9378, 25.3264], [-41.5608, 26.2125],
        [-40.0005, 27.3086], [-38.2593, 28.6288], [-36.7346, 29.8721], [-34.7155, 31.6575], [-32.9864, 33.3249],
        [-31.3282, 35.0756], [-29.5539, 37.1146], [-28.0280, 39.0360], [-26.4742, 41.1779], [-25.2030, 43.1446],
        [-24.0645, 45.1410], [-22.8140, 47.5915], [-21.8666, 49.6910], [-20.9519, 52.0476], [-20.0744, 54.6525],
        [-19.5105, 56.6587], [-18.9421, 59.1872], [-18.3598, 62.2350], [-18.0123, 64.6492], [-17.8416, 66.3869],
        [-17.4003, 71.6515], [-17.2928, 73.6977], [-17.2470, 75.7783], [-17.1510, 190.5792], [-17.2050, 198.7922],
        [-17.1573, 200.1854], [-17.0377, 201.2916], [-16.8365, 202.3633], [-16.5425, 203.5155], [-1.6260, 203.5155],
        [-1.6270, 203.6280], [-1.8145, 203.6280], [-2.4025, 271.0065], [-2.2150, 271.0065], [-2.2160, 271.1190],
        [-16.5443, 271.1190], [-16.5715, 271.2194], [-16.8849, 272.5024], [-17.0804, 273.5880], [-17.1955, 274.7028],
        [-17.2395, 276.0959], [-17.1818, 280.3615], [-17.1720, 284.0256], [-17.1819, 293.8998], [-17.2944, 293.9492],
        [-17.2942, 293.7443], [-85.6382, 323.7801], [-85.6381, 323.9849], [-85.7505, 324.0343], [-85.7812, 280.2450],
        [-85.8412, 277.1309], [-85.9016, 276.1182], [-85.9977, 275.1232], [-86.1377, 274.1500], [-86.3221, 273.1997]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89]
    ], convexity = 30);
}

module frame_mask_7() {
    polygon(points = [
        [290.0396, 270.9146], [287.1280, 271.0925], [287.1405, 270.9753], [287.2320, 270.9735], [287.3299, 270.9675],
        [294.6924, 201.9833], [294.5006, 202.0133], [294.5130, 201.8975], [294.8416, 201.8460], [296.7081, 201.4765],
        [301.5403, 200.3971], [303.1345, 200.0117], [304.6990, 199.5874], [308.8728, 198.3493], [311.2585, 197.5935],
        [314.4764, 196.4910], [316.8220, 195.5943], [319.5752, 194.4312], [322.7243, 193.0237], [325.4277, 191.7687],
        [327.6895, 190.6528], [329.9503, 189.4666], [332.2394, 188.1884], [334.1195, 187.0635], [335.9763, 185.8722],
        [340.0502, 183.1513], [341.8627, 181.8891], [343.8282, 180.4201], [347.5048, 177.5490], [348.8416, 176.4457],
        [350.1500, 175.2891], [354.8299, 170.9451], [356.2626, 169.5609], [357.9891, 167.7371], [360.9250, 164.4573],
        [362.8398, 162.2085], [364.7763, 159.8352], [366.0315, 158.2102], [367.5295, 156.1579], [369.8378, 152.8686],
        [371.3633, 150.5980], [372.6762, 148.4880], [374.2009, 145.8586], [375.6573, 143.1736], [377.5638, 139.5082],
        [378.3645, 137.8708], [379.1173, 136.2112], [380.1780, 133.6830], [381.2945, 130.9081], [382.2805, 128.3130],
        [382.9782, 126.3515], [384.1810, 122.6383], [384.9224, 120.2372], [385.5280, 118.0108], [386.4745, 114.1735],
        [386.8823, 112.3424], [387.1880, 110.7045], [388.0098, 105.1765], [388.6283, 101.3577], [388.8121, 99.8924],
        [388.9218, 98.6421], [389.0378, 96.0706], [389.0955, 91.8830], [389.0655, 89.0041], [388.9537, 86.2571],
        [386.8734, 85.9731], [385.1273, 85.8117], [383.3405, 85.7264], [380.7400, 85.6867], [306.9217, 85.6319],
        [306.9337, 85.5195], [307.1223, 85.5196], [314.3338, 17.9505], [314.1452, 17.9503], [314.1572, 17.8378],
        [405.1990, 17.9213], [409.1115, 17.9685], [410.6462, 18.0423], [411.8977, 18.1486], [414.0775, 18.4458],
        [417.1362, 18.9988], [419.2153, 19.4396], [420.7939, 19.8633], [423.0008, 20.5984], [425.8411, 21.6762],
        [427.9643, 22.5918], [429.8285, 23.5149], [432.0785, 24.7885], [434.2924, 26.1872], [436.6048, 27.7930],
        [438.6374, 29.3435], [440.2920, 30.7250], [441.9336, 32.2424], [443.3343, 33.6905], [444.9642, 35.5596],
        [446.0385, 36.8669], [447.0611, 38.1729], [447.8964, 39.3131], [448.5651, 40.2912], [449.3399, 41.4994],
        [450.2047, 42.9386], [451.0191, 44.3878], [451.7750, 45.8347], [452.5793, 47.4892], [453.3379, 49.1613],
        [453.9570, 50.6538], [454.5309, 52.1746], [454.9869, 53.5014], [455.3997, 54.8519], [455.7531, 56.2309],
        [456.0498, 57.6353], [456.6288, 60.9525], [456.9889, 63.3549], [457.1884, 65.3363], [457.2892, 67.3800],
        [457.3313, 71.2972], [457.3305, 93.0971], [457.2862, 96.2239], [457.1674, 98.5179], [456.9863, 100.5105],
        [456.3902, 105.9314], [456.0581, 110.7288], [455.9085, 112.4835], [455.6515, 114.6955], [455.3650, 116.6182],
        [454.5434, 121.0705], [453.8862, 124.8465], [453.4639, 126.9378], [452.6686, 130.3681], [451.6518, 134.9731],
        [451.2359, 136.5426], [450.1726, 140.3007], [449.5238, 142.4897], [448.6850, 145.0780], [446.2578, 152.1294],
        [445.2328, 154.9071], [443.7471, 158.6119], [442.2669, 162.0722], [439.4356, 168.3876], [438.2316, 170.8579],
        [435.6521, 175.8759], [434.3871, 178.5715], [433.0837, 180.5326], [430.5125, 184.7910], [427.9251, 188.7933],
        [424.4044, 193.9889], [423.2694, 195.5955], [422.1079, 197.1739], [417.9110, 202.5842], [415.7323, 205.2682],
        [412.0362, 209.5969], [409.4697, 212.5505], [408.0054, 214.1689], [406.4855, 215.7482], [401.3890, 220.8236],
        [399.5311, 222.5824], [393.4849, 227.9396], [389.5330, 231.2530], [387.9256, 232.5582], [385.4427, 234.4251],
        [381.6249, 237.1041], [378.0639, 239.6923], [376.2538, 240.9617], [374.2050, 242.3203], [371.3245, 244.1546],
        [369.0527, 245.5592], [367.1914, 246.6536], [362.0777, 249.5110], [360.0502, 250.6066], [358.0227, 251.6376],
        [352.9282, 254.1496], [350.8832, 255.1161], [348.8332, 256.0266], [342.2657, 258.7502], [339.4208, 259.8837],
        [337.4799, 260.6110], [331.0485, 262.7944], [325.3568, 264.5117], [319.3361, 266.1433], [317.0658, 266.6882],
        [313.5907, 267.4009], [309.9201, 268.2201], [308.5147, 268.4917], [306.8439, 268.7623], [302.0158, 269.4531],
        [297.9558, 270.0930], [295.7679, 270.3771]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186]
    ], convexity = 30);
}

module frame_mask_8() {
    polygon(points = [
        [-337.9680, 17.8640], [-279.5253, 17.8125], [-276.9499, 17.7272], [-275.9495, 17.6453], [-274.9697, 17.5217],
        [-274.0144, 17.3498], [-273.0825, 17.1313], [-271.1362, 16.5389], [-271.1362, 6.2163], [-271.0238, 6.2153],
        [-271.0238, 6.4028], [-203.6437, 5.8148], [-203.6437, 5.6273], [-203.5312, 5.6263], [-203.5312, 16.5389],
        [-202.3768, 16.8911], [-201.5314, 17.1099], [-200.6760, 17.2875], [-199.5822, 17.4498], [-198.4548, 17.5594],
        [-197.0434, 17.6439], [-193.5228, 17.7315], [-82.8493, 17.8091], [-82.8554, 17.9216], [-83.0431, 17.9215],
        [-86.7095, 85.7139], [-86.5305, 85.8758], [-86.5383, 86.0204], [-87.0075, 85.5960], [-193.7488, 85.5780],
        [-197.3876, 85.6252], [-198.6368, 85.7034], [-199.5848, 85.8249], [-200.4636, 86.0245], [-201.0589, 86.2390],
        [-201.4176, 86.4162], [-201.7445, 86.6236], [-202.1781, 86.9961], [-202.5357, 87.4389], [-202.8217, 87.9542],
        [-203.0406, 88.5357], [-203.2004, 89.1751], [-203.3104, 89.8614], [-203.4010, 90.8306], [-203.4540, 92.0952],
        [-203.4757, 93.6498], [-203.4578, 140.3998], [-203.5703, 140.2973], [-203.5704, 140.0436], [-337.5665, 17.9761],
        [-337.8446, 17.9764]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    ], convexity = 30);
}

module frame_mask_9() {
    polygon(points = [
        [271.2210, 93.2995], [271.2479, 119.4310], [271.1354, 119.4168], [271.1352, 119.2278], [203.5315, 110.6877],
        [203.5315, 110.8767], [203.4190, 110.8624], [203.4195, 86.2565], [201.3415, 85.9746], [199.5931, 85.8139],
        [197.8042, 85.7302], [195.2007, 85.6927], [86.7718, 85.6905], [85.5900, 86.9963], [85.5899, 95.9775],
        [85.4774, 95.9633], [85.4774, 95.7743], [17.8906, 87.2364], [17.8904, 87.4253], [17.7779, 87.4111],
        [17.7923, 71.3355], [17.8275, 67.6751], [17.8742, 66.3861], [17.9578, 65.1197], [18.1506, 63.3952],
        [18.4208, 61.7218], [19.0173, 58.6840], [19.4903, 56.6205], [19.9225, 55.0552], [20.4814, 53.3070],
        [21.1731, 51.3634], [21.8517, 49.6532], [22.6027, 47.9722], [23.5164, 46.1215], [24.4926, 44.3075],
        [25.4319, 42.7201], [26.4615, 41.1517], [27.5700, 39.6002], [28.8733, 37.8858], [30.2090, 36.2410],
        [31.7318, 34.5316], [33.3330, 32.9116], [35.4234, 30.9806], [37.4787, 29.2274], [39.6124, 27.5682],
        [41.6061, 26.1468], [43.4455, 24.9629], [45.3049, 23.9030], [47.3757, 22.8645], [49.6827, 21.8438],
        [52.0366, 20.9376], [54.6413, 20.0609], [56.6458, 19.4986], [58.7105, 19.0277], [61.9863, 18.3921],
        [64.1558, 18.0730], [65.4016, 17.9554], [66.9308, 17.8711], [70.8424, 17.8148], [193.5506, 17.7225],
        [197.0672, 17.6341], [199.3799, 17.4675], [200.2547, 17.3530], [201.1113, 17.1983], [201.9530, 17.0014],
        [203.5140, 16.5381], [203.5140, -2.3741], [203.6265, -2.3731], [203.6265, -2.1856], [271.0072, -1.5976],
        [271.0072, -1.7851], [271.1197, -1.7841], [271.1197, 16.5408], [272.1378, 16.8690], [273.7427, 17.2951],
        [274.4457, 17.4352], [275.4084, 17.5811], [276.3948, 17.6817], [277.4022, 17.7451], [279.9873, 17.8065],
        [314.4589, 17.8381], [314.4469, 17.9506], [314.2583, 17.9504], [307.0469, 85.5195], [307.2354, 85.5197],
        [307.2234, 85.6322], [279.7233, 85.6118], [278.1675, 85.6357], [276.8968, 85.6924], [275.9158, 85.7839],
        [274.9857, 85.9384], [274.1288, 86.1794], [273.5523, 86.4284], [273.0396, 86.7433], [272.5975, 87.1279],
        [272.2259, 87.5854], [272.0192, 87.9255], [271.8438, 88.2959], [271.6319, 88.9045], [271.4373, 89.7963],
        [271.3209, 90.7540], [271.2584, 91.7547]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101]
    ], convexity = 30);
}

module frame_mask_10() {
    polygon(points = [
        [-203.5312, -16.5353], [-203.5312, 5.9263], [-203.6437, 5.9273], [-203.6437, 5.7398], [-271.0238, 6.3278],
        [-271.0238, 6.5153], [-271.1362, 6.5163], [-271.1362, -16.5349], [-272.5229, -16.9071], [-273.3836, -17.0999],
        [-274.2519, -17.2547], [-275.3549, -17.3948], [-276.7124, -17.5076], [-278.6034, -17.6124], [-281.6300, -17.6930],
        [-281.6394, -17.8058], [-281.4509, -17.8008], [-287.1049, -85.5257], [-287.2930, -85.5258], [-287.3024, -85.6383],
        [-279.6994, -85.6343], [-278.1427, -85.6582], [-276.8712, -85.7149], [-275.8894, -85.8056], [-274.9579, -85.9594],
        [-274.1002, -86.2005], [-273.5228, -86.4488], [-273.0085, -86.7630], [-272.5649, -87.1470], [-272.1931, -87.6015],
        [-271.8919, -88.1252], [-271.6583, -88.7123], [-271.4853, -89.3561], [-271.3636, -90.0449], [-271.2619, -91.0157],
        [-271.1999, -92.2804], [-271.1745, -93.8359], [-271.1888, -120.0809], [-271.0763, -120.1007], [-271.0762, -119.9103],
        [-203.5814, -131.7572], [-203.5815, -131.9476], [-203.4690, -131.9673], [-203.4368, -86.2565], [-201.3579, -85.9731],
        [-199.6088, -85.8109], [-197.8198, -85.7257], [-195.2156, -85.6867], [-87.0075, -85.5960], [-85.7018, -86.7771],
        [-85.7024, -118.2490], [-85.5899, -118.2618], [-85.5899, -117.5070], [-62.7629, -18.3728], [-62.5767, -18.3995],
        [-62.5513, -18.2894], [-64.1763, -18.0565], [-65.4227, -17.9396], [-66.9518, -17.8561], [-70.8626, -17.7998],
        [-192.4988, -17.7045], [-196.0726, -17.6041], [-197.7656, -17.5024], [-199.3748, -17.3648], [-200.4752, -17.2276],
        [-201.5455, -17.0384], [-202.3864, -16.8464]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]
    ], convexity = 30);
}

module frame_mask_11() {
    polygon(points = [
        [271.1197, -16.5351], [271.1197, -1.4841], [271.0072, -1.4851], [271.0072, -1.6726], [203.6265, -2.2606],
        [203.6265, -2.0731], [203.5140, -2.0741], [203.5140, -16.5350], [202.3581, -16.8456], [201.5104, -17.0384],
        [200.4325, -17.2276], [199.3260, -17.3655], [197.7123, -17.5046], [196.0187, -17.6064], [192.4441, -17.7060],
        [71.3512, -17.7998], [67.6906, -17.8335], [65.1361, -17.9614], [63.4100, -18.1498], [61.7328, -18.4116],
        [58.6831, -18.9765], [56.6183, -19.4355], [55.0631, -19.8740], [53.5435, -20.3768], [51.3807, -21.1644],
        [49.4057, -21.9545], [47.6242, -22.7441], [46.0608, -23.5010], [44.5186, -24.3222], [43.0179, -25.2092],
        [41.3625, -26.2950], [39.7620, -27.4382], [38.0081, -28.7838], [36.4875, -30.0367], [34.4884, -31.8074],
        [32.6425, -33.5743], [31.2350, -35.0540], [29.7266, -36.8040], [27.9652, -39.0532], [26.2945, -41.3796],
        [25.0406, -43.3478], [23.9142, -45.3477], [22.7734, -47.5977], [21.8276, -49.6971], [20.9144, -52.0545],
        [20.0376, -54.6593], [19.4745, -56.6655], [18.9076, -59.1940], [18.3260, -62.2425], [17.9800, -64.6576],
        [17.8101, -66.3952], [17.3523, -71.9131], [17.2470, -74.2238], [17.2095, -76.8334], [17.1784, -123.1121],
        [17.2909, -123.1118], [17.2911, -122.9243], [85.5075, -122.7832], [85.5077, -122.9707], [85.6202, -122.9704],
        [85.5901, -87.0006], [86.9946, -85.5961], [195.1983, -85.6867], [197.8026, -85.7257], [199.5915, -85.8109],
        [201.3407, -85.9731], [203.4195, -86.2564], [203.4187, -122.7267], [203.5312, -122.7264], [203.5312, -122.5389],
        [271.0578, -122.3992], [271.0580, -122.5867], [271.1705, -122.5865], [271.1199, -87.0465], [272.1417, -86.7052],
        [273.0531, -86.4401], [273.9853, -86.2214], [274.6994, -86.0923], [275.6762, -85.9642], [276.6761, -85.8816],
        [279.2515, -85.7985], [294.8161, -85.7756], [294.8125, -85.6631], [294.6249, -85.6634], [292.4604, -17.8508],
        [292.6480, -17.8510], [292.6445, -17.7385], [282.6809, -17.7248], [280.6203, -17.6880], [278.6266, -17.6162],
        [276.7304, -17.5106], [275.3670, -17.3963], [274.2585, -17.2554], [273.3845, -17.1007], [272.3005, -16.8532]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94]
    ], convexity = 30);
}

module frame_mask_12() {
    polygon(points = [
        [-306.3858, -268.8763], [-302.3472, -269.4552], [-302.3379, -269.3429], [-302.5238, -269.3162], [-296.8526, -201.3846],
        [-296.6677, -201.4240], [-296.6583, -201.3110], [-301.0674, -200.3712], [-302.6700, -200.0097], [-304.2435, -199.6043],
        [-307.9834, -198.5111], [-310.5951, -197.7072], [-313.8156, -196.6285], [-316.1645, -195.7654], [-318.2844, -194.8985],
        [-321.0238, -193.7064], [-324.3661, -192.1896], [-326.6372, -191.0934], [-329.0907, -189.8135], [-332.3635, -188.0160],
        [-334.2097, -186.9339], [-335.8434, -185.9019], [-340.1104, -183.0635], [-341.9213, -181.8050], [-343.8853, -180.3397],
        [-347.3664, -177.6298], [-348.8951, -176.3765], [-350.2025, -175.2238], [-354.3798, -171.3351], [-355.6467, -170.1132],
        [-357.0334, -168.6748], [-360.8011, -164.5938], [-362.2669, -162.9124], [-364.2514, -160.5152], [-365.6761, -158.7123],
        [-367.1818, -156.6810], [-368.9656, -154.1368], [-370.8960, -151.2668], [-372.5072, -148.7657], [-373.8982, -146.4530],
        [-375.1832, -144.1519], [-377.1257, -140.4700], [-378.1530, -138.4303], [-379.0202, -136.5686], [-379.9165, -134.4683],
        [-381.1268, -131.4948], [-382.1225, -128.9108], [-382.9875, -126.5210], [-383.7799, -124.1182], [-384.7988, -120.8488],
        [-385.2867, -119.0769], [-386.6366, -113.6779], [-386.9994, -112.0809], [-387.2653, -110.6809], [-388.0870, -105.1655],
        [-388.6507, -101.5950], [-388.8023, -100.3844], [-388.9106, -99.1481], [-388.9838, -97.6288], [-389.0145, -95.5598],
        [-388.9664, -86.2565], [-386.8892, -85.9731], [-385.1423, -85.8124], [-383.3556, -85.7272], [-380.7536, -85.6882],
        [-287.0013, -85.6382], [-286.9920, -85.5256], [-287.1801, -85.5257], [-281.5263, -17.8028], [-281.3377, -17.7978],
        [-281.3283, -17.6850], [-282.6523, -17.7203], [-405.0106, -17.8613], [-408.6687, -17.8980], [-409.9570, -17.9447],
        [-411.2225, -18.0290], [-412.9461, -18.2196], [-414.8575, -18.5250], [-417.9013, -19.0989], [-419.7368, -19.5175],
        [-421.3035, -19.9696], [-423.0671, -20.5715], [-425.2578, -21.3944], [-427.1884, -22.1932], [-428.8603, -22.9730],
        [-430.5087, -23.8364], [-432.3558, -24.9066], [-434.4092, -26.1971], [-436.0426, -27.3010], [-437.4430, -28.3252],
        [-438.9964, -29.5619], [-440.5129, -30.8678], [-442.1814, -32.4250], [-443.7660, -34.0660], [-445.3731, -35.9403],
        [-446.9801, -38.0015], [-448.3403, -39.9198], [-449.6243, -41.9357], [-450.9357, -44.2104], [-452.1073, -46.4850],
        [-453.1697, -48.7731], [-453.9539, -50.6823], [-454.7992, -53.0550], [-455.4727, -55.2463], [-455.9164, -57.0574],
        [-456.4043, -59.6275], [-456.9046, -62.7246], [-457.1553, -64.9374], [-457.2817, -67.2293], [-457.3237, -70.0976],
        [-457.3335, -91.9072], [-457.2975, -95.8282], [-457.2260, -97.6260], [-457.1192, -99.1400], [-456.3797, -106.0514],
        [-455.9401, -112.0911], [-455.7115, -114.0535], [-455.4243, -115.9772], [-454.6298, -120.4627], [-453.9936, -124.2603],
        [-453.5885, -126.3700], [-451.5833, -135.0461], [-450.2660, -139.9551], [-449.5620, -142.3750], [-447.7833, -147.7682],
        [-446.0701, -152.6842], [-445.1891, -155.0373], [-443.8649, -158.3319], [-442.5379, -161.4731], [-440.4217, -166.2376],
        [-439.2577, -168.7180], [-435.7634, -175.6728], [-434.4043, -178.5715], [-433.1003, -180.5325], [-430.7806, -184.3838],
        [-429.3675, -186.6139], [-427.1529, -189.9805], [-424.4169, -193.9936], [-423.1387, -195.7999], [-421.6772, -197.7645],
        [-418.2219, -202.2103], [-416.6865, -204.1376], [-415.0902, -206.0469], [-410.8057, -211.0419], [-408.8928, -213.2168],
        [-407.4128, -214.8126], [-401.3925, -220.8366], [-400.2839, -221.9024], [-399.1537, -222.9372], [-394.4202, -227.1394],
        [-392.7422, -228.5848], [-388.4698, -232.1374], [-387.1804, -233.1501], [-385.8325, -234.1552], [-381.6188, -237.1199],
        [-376.8544, -240.5617], [-375.0166, -241.8030], [-372.5468, -243.3929], [-369.4537, -245.3257], [-367.1784, -246.6702],
        [-363.4857, -248.7103], [-359.6226, -250.7784], [-355.7592, -252.7558], [-351.8614, -254.6706], [-349.3462, -255.8159],
        [-345.1383, -257.6223], [-342.2430, -258.8121], [-338.4911, -260.2587], [-336.5854, -260.9362], [-331.6680, -262.5991],
        [-329.2796, -263.3500], [-325.1075, -264.5883], [-319.0926, -266.2183], [-316.8291, -266.7697], [-310.3818, -268.1594],
        [-308.5196, -268.5254]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175]
    ], convexity = 30);
}

module frame_mask_13() {
    polygon(points = [
        [-62.0038, -18.3679], [-62.8493, -18.2467], [-62.8747, -18.3567], [-62.6884, -18.3834], [-85.5572, -117.6994],
        [-85.5899, -117.6957], [-85.5899, -117.0056], [-85.7024, -117.4942], [-85.7040, -195.2029], [-85.7414, -197.8064],
        [-85.8252, -199.5946], [-85.9858, -201.3430], [-86.2678, -203.4213], [-105.4988, -203.4669], [-105.5247, -203.5795],
        [-105.3322, -203.5790], [-120.8736, -271.0730], [-121.0659, -271.0729], [-121.0918, -271.1854], [-86.8378, -271.2134],
        [-86.3221, -273.1989], [-86.1377, -274.1500], [-85.9977, -275.1232], [-85.9016, -276.1174], [-85.8412, -277.1309],
        [-85.7812, -280.2450], [-85.7709, -294.9537], [-85.6584, -294.9487], [-85.6586, -294.7610], [-17.2974, -291.7048],
        [-17.2976, -291.8925], [-17.1851, -291.8874], [-17.1757, -284.0699], [-17.1848, -280.4036], [-17.2387, -276.1289],
        [-17.1940, -274.7290], [-17.0796, -273.6073], [-16.8849, -272.5144], [-16.5414, -271.1190], [2.5160, -271.1190],
        [2.5150, -271.0065], [2.3275, -271.0065], [1.7395, -203.6280], [1.9270, -203.6280], [1.9261, -203.5155],
        [-16.5422, -203.5155], [-16.8356, -202.3532], [-17.0362, -201.2738], [-17.1558, -200.1599], [-17.2035, -198.7607],
        [-17.1510, -190.8042], [-17.2223, -78.3516], [-17.2740, -73.9098], [-17.3425, -72.3678], [-17.4687, -70.5970],
        [-17.8544, -66.0909], [-18.0333, -64.3588], [-18.2734, -62.6656], [-18.6582, -60.5423], [-19.1834, -57.9856],
        [-19.6838, -55.9389], [-20.3511, -53.7359], [-21.1857, -51.3593], [-21.9455, -49.4366], [-22.8818, -47.3397],
        [-23.8127, -45.4742], [-24.8597, -43.6150], [-25.8970, -41.9762], [-27.1515, -40.1743], [-28.7500, -38.0482],
        [-30.2352, -36.2141], [-31.7588, -34.5046], [-33.3600, -32.8846], [-35.4512, -30.9543], [-37.5073, -29.2019],
        [-39.6402, -27.5434], [-41.6346, -26.1228], [-43.4740, -24.9404], [-45.3343, -23.8819], [-47.4087, -22.8420],
        [-49.7216, -21.8184], [-52.2882, -20.8283], [-55.0942, -19.8689], [-56.8762, -19.3746], [-58.7157, -18.9727]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84]
    ], convexity = 30);
}

module frame_mask_14() {
    polygon(points = [
        [404.3279, -17.8928], [292.3443, -17.7381], [292.3479, -17.8506], [292.5355, -17.8509], [294.7000, -85.6633],
        [294.5124, -85.6636], [294.5160, -85.7760], [387.7566, -85.6389], [388.1742, -86.7913], [388.4847, -87.8742],
        [388.6699, -88.7824], [388.8208, -89.9773], [388.8983, -91.2240], [388.9267, -92.7638], [388.9095, -95.1087],
        [388.8466, -97.4445], [388.7195, -99.4741], [388.4909, -101.4371], [387.8387, -105.4902], [387.1361, -110.2966],
        [386.8872, -111.7095], [386.5965, -113.0921], [385.0924, -119.1789], [384.4780, -121.3911], [382.8760, -126.4105],
        [382.2615, -128.1530], [381.4497, -130.3166], [379.4747, -135.2131], [378.8469, -136.6777], [378.1833, -138.1245],
        [377.1747, -140.1649], [375.7058, -142.9940], [374.6263, -145.0099], [373.7149, -146.6218], [371.9774, -149.4790],
        [369.9538, -152.5753], [367.6130, -155.9914], [365.6997, -158.6145], [363.8405, -160.9694], [361.3549, -163.9458],
        [358.2417, -167.4411], [356.4844, -169.3031], [355.5027, -170.2558], [353.0633, -172.5054], [350.5148, -174.9451],
        [349.3985, -175.9725], [347.6863, -177.4207], [344.7906, -179.6892], [342.0924, -181.7403], [339.7646, -183.3672],
        [335.0028, -186.5178], [333.5742, -187.3966], [331.9344, -188.3434], [328.0508, -190.4579], [325.1793, -191.9060],
        [320.5996, -194.0010], [316.8061, -195.6206], [314.2510, -196.5936], [310.6056, -197.8279], [305.8036, -199.2862],
        [303.1384, -200.0281], [301.0828, -200.5056], [298.1975, -201.1154], [298.2011, -201.2296], [298.3875, -201.1902],
        [300.5681, -269.5099], [300.3815, -269.5392], [300.3851, -269.6525], [301.4776, -269.4809], [306.5769, -268.7819],
        [308.4898, -268.4797], [310.1235, -268.1608], [313.5541, -267.3919], [317.2533, -266.6280], [319.9615, -265.9549],
        [325.0888, -264.5620], [329.2609, -263.3214], [331.6494, -262.5691], [336.3595, -260.9690], [338.9424, -260.0309],
        [342.2486, -258.7126], [346.7097, -256.8524], [350.7714, -255.0753], [353.4767, -253.8213], [357.8239, -251.6774],
        [360.1431, -250.4986], [362.2375, -249.3677], [366.5595, -246.9546], [368.6248, -245.7552], [371.5166, -243.9707],
        [375.0131, -241.7271], [377.4504, -240.0611], [381.6099, -237.0433], [385.4257, -234.3624], [386.9739, -233.2171],
        [388.2672, -232.2035], [389.8559, -230.8852], [394.1940, -227.1751], [398.9131, -223.0285], [400.2476, -221.8217],
        [401.6948, -220.4294], [406.8320, -215.2959], [408.0457, -214.0363], [409.1900, -212.7793], [412.1549, -209.3453],
        [416.3320, -204.4247], [418.0283, -202.3064], [421.7810, -197.4701], [423.6653, -194.8994], [426.1790, -191.2501],
        [428.4919, -187.7747], [430.6128, -184.4571], [431.9568, -182.1823], [435.3731, -176.0768], [437.2967, -172.4870],
        [438.7422, -169.6530], [440.0159, -166.9449], [442.4208, -161.5393], [443.7538, -158.4004], [445.0863, -155.1013],
        [446.0513, -152.5367], [447.9167, -147.1984], [449.2061, -143.3205], [449.9473, -140.9196], [451.2682, -136.2725],
        [451.6803, -134.7024], [453.7284, -125.5420], [454.5658, -120.8332], [455.3086, -116.8561], [455.5364, -115.4242],
        [455.7635, -113.7227], [456.0130, -111.2404], [456.2628, -107.4441], [456.4066, -105.6915], [457.1275, -99.0334],
        [457.2899, -96.2408], [457.3410, -92.3305], [457.3500, -73.4271], [457.3417, -69.2316], [457.2959, -66.8941],
        [457.1770, -64.8631], [456.9579, -62.8959], [456.3863, -59.3181], [455.8999, -56.7245], [455.4471, -54.8787],
        [454.8913, -53.0826], [454.1861, -51.1090], [452.6905, -47.2279], [451.9488, -44.9953], [450.4770, -43.0438],
        [448.1686, -39.7179], [446.9397, -38.0246], [445.3473, -35.9991], [443.7460, -34.1443], [441.9983, -32.3048],
        [440.3426, -30.7500], [438.6561, -29.3511], [436.3984, -27.6648], [434.0653, -26.0638], [431.8449, -24.6710],
        [430.6180, -23.9620], [429.3839, -23.2990], [428.3476, -22.7846], [427.0884, -22.2088], [425.5894, -21.5823],
        [424.0613, -20.9923], [422.3005, -20.3542], [420.9703, -19.9176], [419.8448, -19.5949], [418.4688, -19.2634],
        [414.9566, -18.5836], [413.5283, -18.3444], [412.3141, -18.1779], [410.0616, -17.9860], [407.9955, -17.9175]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174]
    ], convexity = 30);
}

module frame_mask_15() {
    polygon(points = [
        [-203.5140, -195.8347], [-203.4688, -131.6628], [-203.5813, -131.6430], [-203.5814, -131.8334], [-271.0762, -119.9864],
        [-271.0761, -119.7961], [-271.1886, -119.7764], [-271.2292, -194.6246], [-271.2674, -197.2258], [-271.3527, -199.0125],
        [-271.5141, -200.7602], [-271.7990, -202.8526], [-273.6837, -203.1068], [-275.4564, -203.2539], [-277.5090, -203.3130],
        [-279.5576, -203.2733], [-282.0757, -203.1072], [-286.5504, -202.6815], [-291.4940, -202.1695], [-293.6685, -201.8838],
        [-295.7746, -201.4993], [-296.9540, -201.2480], [-296.9635, -201.3610], [-296.7786, -201.4004], [-302.4494, -269.3269],
        [-302.6354, -269.3002], [-302.6447, -269.4125], [-301.5825, -269.5648], [-298.0110, -270.1387], [-296.5538, -270.3320],
        [-294.8201, -270.5056], [-289.8102, -270.9356], [-287.5165, -271.0746], [-284.1314, -271.1512], [-272.9374, -271.2129],
        [-272.3553, -272.6340], [-271.9808, -273.7405], [-271.6943, -274.8886], [-271.5012, -276.0870], [-271.3887, -277.3299],
        [-271.3252, -278.8642], [-271.2772, -285.4008], [-271.2081, -287.9917], [-271.0811, -290.0240], [-270.6759, -294.7781],
        [-270.5030, -296.5133], [-270.3096, -297.9732], [-269.5535, -302.5042], [-269.4568, -303.1658], [-269.3438, -303.1608],
        [-269.3711, -302.9743], [-200.8665, -299.9117], [-200.8266, -300.0976], [-200.7126, -300.0925], [-201.5529, -296.1851],
        [-201.8753, -294.5637], [-202.1414, -292.9036], [-202.3787, -290.9547], [-202.9147, -285.7519], [-203.3517, -281.0151],
        [-203.4436, -279.4963], [-203.5020, -277.6952], [-203.5309, -272.5233], [-202.1267, -271.1191], [-120.7840, -271.1856],
        [-120.7581, -271.0731], [-120.9505, -271.0730], [-105.4092, -203.5792], [-105.2167, -203.5788], [-105.1907, -203.4662],
        [-195.8498, -203.6812], [-197.3971, -203.6476], [-198.4015, -203.5910], [-199.3638, -203.4840], [-200.0424, -203.3566],
        [-200.6728, -203.1779], [-201.2434, -202.9376], [-201.7463, -202.6307], [-202.1764, -202.2529], [-202.5353, -201.8014],
        [-202.8241, -201.2794], [-203.0476, -200.6927], [-203.2134, -200.0491], [-203.3308, -199.3613], [-203.4296, -198.3913],
        [-203.4818, -197.3841]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85]
    ], convexity = 30);
}

module frame_mask_16() {
    polygon(points = [
        [87.0406, -271.1190], [100.8908, -271.1242], [100.8872, -271.0117], [100.6996, -271.0116], [98.5567, -203.5587],
        [98.7443, -203.5591], [98.7407, -203.4466], [86.2505, -203.4213], [85.9671, -201.3422], [85.8057, -199.5938],
        [85.7204, -197.8048], [85.6807, -195.1998], [85.6200, -122.6704], [85.5075, -122.6707], [85.5076, -122.8582],
        [17.2910, -122.9993], [17.2911, -122.8118], [17.1786, -122.8121], [17.1330, -190.8432], [17.1855, -199.0303],
        [17.1401, -200.1850], [17.0205, -201.2916], [16.8192, -202.3634], [16.5259, -203.5155], [1.6260, -203.5155],
        [1.6270, -203.6280], [1.8145, -203.6280], [2.4025, -271.0065], [2.2150, -271.0065], [2.2160, -271.1190],
        [16.5277, -271.1190], [16.8449, -272.2894], [17.0910, -273.3651], [17.2457, -274.2331], [17.3850, -275.3353],
        [17.4971, -276.6920], [17.6011, -278.5824], [17.7053, -282.3696], [17.7637, -359.1877], [17.8762, -359.1768],
        [17.8761, -358.9885], [85.6183, -352.4550], [85.6182, -352.6434], [85.7307, -352.6325], [85.7917, -280.0361],
        [85.8651, -276.9305], [85.9381, -275.9249], [86.0528, -274.9415], [86.2186, -273.9847], [86.4364, -273.0529],
        [86.7000, -272.1416]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    ], convexity = 30);
}

module frame_mask_17() {
    polygon(points = [
        [271.2742, -195.3688], [271.1701, -122.2865], [271.0576, -122.2867], [271.0579, -122.4742], [203.5312, -122.6139],
        [203.5313, -122.4264], [203.4188, -122.4267], [203.4173, -195.1984], [203.3798, -197.8034], [203.2961, -199.5924],
        [203.1354, -201.3423], [202.8527, -203.4268], [199.0542, -203.5980], [194.5959, -203.6407], [98.4405, -203.4460],
        [98.4441, -203.5585], [98.6317, -203.5588], [100.7746, -271.0116], [100.5870, -271.0116], [100.5906, -271.1241],
        [202.2661, -271.1617], [203.5137, -272.5196], [203.4900, -277.4324], [203.4489, -278.9799], [203.3703, -280.5060],
        [203.2326, -282.2607], [202.9230, -285.4921], [202.2333, -292.1716], [201.9686, -294.1061], [201.6254, -295.9878],
        [200.4077, -301.4869], [199.8539, -303.7380], [198.4438, -308.5580], [197.4122, -311.8048], [196.2162, -315.2309],
        [195.1083, -317.9962], [194.0903, -320.3401], [192.5322, -323.8057], [190.9079, -327.2063], [189.8559, -329.2458],
        [188.8728, -331.0525], [187.8336, -332.8607], [186.8516, -334.4812], [184.1412, -338.6812], [182.2594, -341.4100],
        [180.9614, -343.1481], [180.7099, -343.4721], [180.8638, -343.4573], [181.0219, -343.2537], [261.1855, -335.5222],
        [261.1190, -335.7170], [261.2419, -335.7051], [262.8115, -331.1095], [264.5372, -325.4238], [266.2986, -318.9643],
        [266.8987, -316.4667], [268.1954, -310.4826], [268.5666, -308.6243], [268.9227, -306.4925], [269.5430, -302.1668],
        [270.1566, -298.3602], [270.3912, -296.6670], [270.5693, -294.9366], [270.9551, -290.4353], [271.1211, -287.9004],
        [271.1887, -285.3092], [271.2270, -279.0292], [271.3040, -276.7129], [271.4692, -274.7066], [271.7906, -272.3079],
        [273.1051, -271.1189], [285.3822, -271.1010], [287.7168, -271.0424], [289.7534, -270.9214], [294.2438, -270.5175],
        [296.4530, -270.2702], [300.6838, -269.6056], [300.6801, -269.4923], [300.4935, -269.5216], [298.3129, -201.2060],
        [298.4993, -201.1666], [298.4956, -201.0524], [295.0833, -201.7736], [293.1933, -202.0966], [291.2530, -202.3450],
        [283.8464, -203.0894], [280.3488, -203.3770], [278.8219, -203.4451], [277.2728, -203.4765], [272.4145, -203.4728],
        [271.8721, -201.5532], [271.6721, -200.6274], [271.5517, -199.9164], [271.4325, -198.9420], [271.3543, -197.9438]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94]
    ], convexity = 30);
}

module frame_mask_18() {
    polygon(points = [
        [-17.3108, -396.5382], [-17.1848, -291.5871], [-17.2973, -291.5922], [-17.2975, -291.7799], [-85.6585, -294.8361],
        [-85.6586, -294.6484], [-85.7711, -294.6534], [-85.7108, -380.7358], [-85.7460, -383.3363], [-85.8289, -385.1230],
        [-85.9881, -386.8692], [-86.2680, -388.9446], [-95.5852, -388.9905], [-97.6564, -388.9583], [-99.1780, -388.8843],
        [-100.4166, -388.7753], [-101.6287, -388.6237], [-105.2045, -388.0585], [-110.7281, -387.2346], [-112.1296, -386.9671],
        [-113.7297, -386.6036], [-119.1368, -385.2499], [-120.9102, -384.7598], [-124.1850, -383.7394], [-126.5925, -382.9476],
        [-129.4231, -381.9347], [-132.0134, -380.9601], [-134.3571, -380.0009], [-136.6731, -378.9818], [-138.5376, -378.0971],
        [-140.7821, -376.9550], [-143.4207, -375.5413], [-145.8639, -374.1613], [-149.6708, -371.9243], [-151.7907, -370.5919],
        [-154.1130, -369.0147], [-156.8150, -367.1033], [-158.6645, -365.7315], [-160.2927, -364.4521], [-162.6886, -362.4795],
        [-164.7514, -360.7029], [-167.2955, -358.3933], [-169.2767, -356.4974], [-171.0951, -354.6363], [-174.7786, -350.7414],
        [-176.1151, -349.2620], [-177.2306, -347.9327], [-178.8857, -345.8080], [-182.2292, -341.3665], [-183.4516, -339.6253],
        [-185.6738, -336.3208], [-186.9349, -334.3776], [-188.1151, -332.4235], [-189.3347, -330.2508], [-190.5000, -328.0409],
        [-191.6159, -325.7934], [-192.7801, -323.3030], [-194.3795, -319.7370], [-195.5472, -316.9860], [-196.4498, -314.6419],
        [-197.5553, -311.4242], [-198.3808, -308.8217], [-199.6189, -304.6482], [-200.0393, -303.0817], [-200.3639, -301.7137],
        [-200.7765, -299.7950], [-200.8905, -299.8001], [-200.8505, -299.9860], [-269.3602, -303.0489], [-269.3874, -302.8624],
        [-269.5004, -302.8675], [-268.8837, -307.0873], [-268.6086, -308.7516], [-268.3318, -310.1493], [-267.5613, -313.5784],
        [-266.6399, -317.9602], [-266.2429, -319.5386], [-265.0363, -323.9981], [-264.3457, -326.4325], [-263.0831, -330.5881],
        [-260.9840, -336.8051], [-260.1141, -339.1715], [-258.7172, -342.6693], [-256.4278, -348.1830], [-255.0634, -351.2566],
        [-253.5812, -354.3215], [-251.4162, -358.5960], [-249.5903, -362.0429], [-247.3541, -366.1280], [-246.1742, -368.1904],
        [-244.9192, -370.2580], [-242.8358, -373.5498], [-241.2162, -376.0112], [-239.9497, -377.8260], [-237.0725, -381.7833],
        [-234.3909, -385.5953], [-233.3873, -386.9492], [-232.2311, -388.4249], [-227.7265, -393.8024], [-221.9847, -400.2293],
        [-220.4338, -401.8381], [-215.4631, -406.8073], [-214.2028, -408.0232], [-212.7664, -409.3289], [-209.1404, -412.4506],
        [-204.3998, -416.4671], [-202.2784, -418.1582], [-197.4392, -421.9064], [-194.8639, -423.7862], [-191.0084, -426.4326],
        [-187.5262, -428.7396], [-184.4134, -430.7201], [-182.5504, -431.8211], [-180.2915, -433.0778], [-172.8292, -437.1597],
        [-169.7923, -438.7307], [-167.2975, -439.9086], [-161.1748, -442.6338], [-158.3492, -443.8312], [-154.8649, -445.2288],
        [-152.5125, -446.1163], [-147.9597, -447.7427], [-143.7985, -449.0968], [-141.1748, -449.9033], [-136.7263, -451.1311],
        [-134.7051, -451.6562], [-127.4157, -453.3497], [-125.5721, -453.7442], [-120.8668, -454.5786], [-116.8890, -455.3198],
        [-115.4571, -455.5469], [-113.7556, -455.7733], [-111.2719, -456.0220], [-107.4740, -456.2711], [-105.7207, -456.4141],
        [-99.0611, -457.1335], [-96.2670, -457.2952], [-92.3552, -457.3455], [-73.4466, -457.3500], [-69.2496, -457.3402],
        [-66.9114, -457.2944], [-64.8803, -457.1748], [-62.9123, -456.9549], [-59.3338, -456.3825], [-56.7387, -455.8954],
        [-54.8929, -455.4419], [-53.0961, -454.8861], [-51.1218, -454.1809], [-47.2391, -452.6845], [-45.0058, -451.9421],
        [-43.0532, -450.4700], [-38.9629, -447.5914], [-36.7374, -445.8418], [-34.1506, -443.6344], [-32.3080, -441.9309],
        [-30.8935, -440.4743], [-29.4102, -438.7531], [-27.8895, -436.7635], [-26.3473, -434.5137], [-24.8022, -432.0466],
        [-23.9708, -430.6088], [-23.2033, -429.1670], [-22.5978, -427.9192], [-21.9454, -426.4382], [-21.2565, -424.7033],
        [-20.6160, -422.9373], [-20.1021, -421.3799], [-19.6512, -419.8042], [-19.2659, -418.2006], [-18.8774, -416.3431],
        [-18.4755, -414.2306], [-18.2070, -412.5565], [-18.0227, -411.0910], [-17.8012, -408.8624], [-17.5332, -405.8749],
        [-17.4159, -404.1042], [-17.3318, -401.2608]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176]
    ], convexity = 30);
}

module frame_mask_19() {
    polygon(points = [
        [260.5435, -337.7502], [261.3484, -335.3935], [261.2254, -335.4053], [261.1589, -335.6001], [180.9587, -343.3351],
        [181.0509, -343.2163], [181.1140, -343.1317], [180.9628, -343.1463], [178.5772, -346.2196], [176.4529, -348.8681],
        [174.7930, -350.7142], [169.6922, -356.0384], [168.1947, -357.4850], [164.6034, -360.8065], [163.2937, -361.9523],
        [161.6143, -363.3590], [159.9709, -364.6931], [158.5235, -365.8217], [155.3299, -368.1470], [151.6479, -370.6738],
        [148.7355, -372.5026], [145.2592, -374.5520], [141.1506, -376.7569], [137.8817, -378.3999], [135.3783, -379.5158],
        [131.5585, -381.0803], [128.3220, -382.3202], [125.7063, -383.2405], [121.9959, -384.4251], [120.0219, -385.0088],
        [114.1772, -386.4829], [112.3544, -386.8995], [110.4806, -387.2382], [105.9322, -387.9138], [101.8996, -388.5819],
        [100.6953, -388.7463], [99.4650, -388.8702], [97.9521, -388.9599], [95.8874, -389.0070], [86.3157, -388.9959],
        [86.0089, -386.9216], [85.8356, -385.1783], [85.7452, -383.3936], [85.7070, -380.7942], [85.7309, -352.3311],
        [85.6184, -352.3419], [85.6183, -352.5303], [17.8761, -359.0638], [17.8760, -358.8754], [17.7635, -358.8863],
        [17.7907, -394.6980], [17.7465, -398.6006], [17.5688, -402.6108], [17.5380, -404.0757], [17.5591, -405.2953],
        [17.6463, -407.0166], [17.8490, -410.0167], [18.0092, -411.7576], [18.3170, -413.9315], [18.8948, -416.9784],
        [19.4016, -419.2785], [19.9512, -421.2850], [20.7472, -423.6473], [21.7171, -426.1571], [22.6254, -428.2175],
        [23.6680, -430.2680], [24.9732, -432.5098], [26.5242, -434.9037], [28.1512, -437.1795], [29.7410, -439.2025],
        [31.1741, -440.8568], [32.7415, -442.4784], [34.4032, -444.0062], [36.4618, -445.7341], [37.9537, -446.9109],
        [39.2843, -447.8856], [40.6647, -448.8121], [42.2967, -449.8221], [43.9511, -450.7712], [45.6050, -451.6443],
        [47.4665, -452.5473], [49.3504, -453.3843], [50.8429, -453.9759], [52.5665, -454.5918], [54.3069, -455.1529],
        [55.6379, -455.5280], [57.0020, -455.8496], [58.3961, -456.1257], [60.9922, -456.5756], [62.9096, -456.8672],
        [64.3820, -457.0381], [65.6367, -457.1367], [67.1726, -457.2067], [68.7322, -457.2375], [90.7879, -457.2525],
        [95.2379, -457.2255], [97.0437, -457.1676], [98.8155, -457.0532], [105.9741, -456.2919], [112.0271, -455.8569],
        [114.4905, -455.5780], [116.6520, -455.2547], [120.8688, -454.4744], [124.8844, -453.7713], [127.2053, -453.2897],
        [134.2604, -451.6387], [140.7055, -449.8991], [143.1169, -449.1885], [147.2027, -447.8418], [152.9656, -445.8260],
        [156.6198, -444.4137], [160.7700, -442.6903], [167.3207, -439.7796], [169.6074, -438.7009], [172.0459, -437.4531],
        [182.1574, -431.9168], [184.2157, -430.7122], [186.6505, -429.1741], [190.0194, -426.9617], [194.0393, -424.2265],
        [195.8426, -422.9482], [197.6100, -421.6367], [203.0176, -417.4364], [204.5552, -416.1955], [206.2705, -414.7519],
        [210.5475, -411.0931], [213.4115, -408.5819], [215.6351, -406.4793], [220.5309, -401.5782], [222.6459, -399.3551],
        [227.6830, -393.6884], [231.6053, -389.0215], [233.4872, -386.6378], [234.6311, -385.0729], [237.3162, -381.2568],
        [240.0511, -377.4995], [241.4476, -375.4751], [242.9230, -373.2158], [244.8728, -370.1298], [246.0038, -368.2687],
        [247.1917, -366.2068], [249.5859, -361.9225], [250.5735, -360.0983], [251.6083, -358.0724], [254.0256, -353.1866],
        [255.0010, -351.1465], [255.9231, -349.1093], [257.4240, -345.6467], [258.4698, -343.1423], [259.5703, -340.3363]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149]
    ], convexity = 30);
}

module frame_joint_domain_0() {
    polygon(points = [
        [16.5659, 271.0690], [-3.9656, 271.0690], [-3.3766, 203.5655], [16.5664, 203.5655], [16.8996, 202.3626],
        [17.1019, 201.5065], [17.2645, 200.6406], [17.4138, 199.5377], [17.5335, 198.1727], [17.6301, 196.5100],
        [17.7343, 192.7126], [17.7440, 181.7350], [18.5147, 181.7417], [17.6878, 276.4980], [17.5336, 276.5038],
        [17.4385, 275.3617], [17.2966, 274.2511], [17.1415, 273.3738], [16.8942, 272.2876]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    ], convexity = 30);
}

module frame_joint_domain_1() {
    polygon(points = [
        [17.7553, -282.3689], [17.7633, -292.9355], [22.6568, -292.8928], [21.6837, -181.3909], [17.1893, -181.4302],
        [17.1830, -190.8430], [17.2355, -199.0311], [17.1900, -200.1887], [17.0700, -201.2989], [16.8681, -202.3742],
        [16.5648, -203.5655], [0.1764, -203.5655], [0.7655, -271.0690], [16.5660, -271.0690], [16.8935, -272.2772],
        [17.1400, -273.3552], [17.2951, -274.2256], [17.4348, -275.3301], [17.5470, -276.6886], [17.6511, -278.5804]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    ], convexity = 30);
}

module frame_joint_domain_2() {
    polygon(points = [
        [-292.9867, 17.8744], [-279.5244, 17.8625], [-276.9470, 17.7771], [-275.9443, 17.6950], [-274.9621, 17.5711],
        [-274.0043, 17.3988], [-273.0695, 17.1796], [-271.0863, 16.5759], [-271.0863, 4.7658], [-203.5812, 4.1767],
        [-203.5812, 16.5760], [-202.3904, 16.9392], [-201.5428, 17.1586], [-200.6847, 17.3368], [-199.5883, 17.4995],
        [-198.4587, 17.6093], [-197.0455, 17.6938], [-193.5235, 17.7815], [-181.4756, 17.7900], [-181.4067, 25.6840],
        [-292.9100, 26.6571]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    ], convexity = 30);
}

module frame_joint_domain_3() {
    polygon(points = [
        [279.9867, 17.8565], [292.9004, 17.8683], [292.8935, 18.6567], [197.3637, 17.8230], [197.3587, 17.6633],
        [199.3849, 17.5172], [200.2624, 17.4024], [201.1215, 17.2473], [201.9659, 17.0498], [203.5640, 16.5754],
        [203.5640, -3.8237], [271.0697, -3.2346], [271.0697, 16.5772], [272.1237, 16.9170], [273.7314, 17.3438],
        [274.4370, 17.4845], [275.4021, 17.6308], [276.3907, 17.7316], [277.4001, 17.7951]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    ], convexity = 30);
}

module frame_joint_domain_4() {
    polygon(points = [
        [-241.4580, 375.5939], [-244.0930, 371.5032], [-180.6182, 343.6074], [-177.5142, 347.6602], [-176.4103, 348.9970],
        [-175.2491, 350.3064], [-170.0046, 355.9009], [-168.1791, 357.6756], [-165.0805, 360.4820], [-231.2365, 389.5562],
        [-232.4842, 388.0594], [-233.9254, 386.1992], [-235.3359, 384.2745], [-240.2035, 377.4183]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    ], convexity = 30);
}

module frame_joint_domain_5() {
    polygon(points = [
        [-17.2220, 284.0257], [-17.2335, 295.5063], [-85.6994, 325.5957], [-85.7161, 301.8998], [-16.7093, 271.5728],
        [-16.9339, 272.4920], [-17.1299, 273.5810], [-17.2454, 274.6995], [-17.2895, 276.0954], [-17.2318, 280.3619]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    ], convexity = 30);
}

module frame_joint_domain_6() {
    polygon(points = [
        [-86.7991, 271.1634], [-98.3034, 271.1540], [-94.6439, 203.4890], [-86.2241, 203.4719], [-85.9361, 201.3494],
        [-85.7753, 199.5988], [-85.6915, 197.8079], [-85.6540, 195.2033], [-85.6537, 181.8533], [-71.7826, 182.6035],
        [-77.8185, 294.2086], [-85.7218, 293.7811], [-85.7312, 280.2445], [-85.7912, 277.1289], [-85.8517, 276.1143],
        [-85.9481, 275.1172], [-86.0884, 274.1417], [-86.2733, 273.1886]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    ], convexity = 30);
}

module frame_joint_domain_7() {
    polygon(points = [
        [-63.6667, 18.1910], [-62.8972, 18.3104], [-67.7939, 108.8513], [-85.6522, 107.8854], [-85.6518, 86.7549],
        [-86.9883, 85.5460], [-88.2652, 85.5458], [-84.6045, 17.8579], [-71.6200, 17.8670], [-67.6974, 17.9023],
        [-65.3970, 18.0112]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ], convexity = 30);
}

module frame_joint_domain_8() {
    polygon(points = [
        [-337.9038, 260.4198], [-340.0758, 259.5866], [-203.4918, 182.1035], [-203.4868, 195.2115], [-203.4485, 197.8139],
        [-203.3640, 199.6025], [-203.2024, 201.3517], [-202.9139, 203.4756], [-199.0720, 203.6480], [-197.5180, 203.6632],
        [-310.8961, 267.9818], [-316.1661, 266.8636], [-318.2222, 266.3890], [-324.7021, 264.6483], [-328.6655, 263.4837],
        [-331.7103, 262.5313]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    ], convexity = 30);
}

module frame_joint_domain_9() {
    polygon(points = [
        [-367.5088, 17.9400], [-335.3171, 17.9116], [-203.5087, 137.9862], [-203.4974, 167.3507], [-271.2380, 105.6405],
        [-271.2452, 93.8152], [-271.2790, 91.4662], [-271.3605, 89.6619], [-271.5244, 87.8874], [-271.7545, 86.2142],
        [-273.6395, 85.9548], [-275.3828, 85.7835], [-277.1667, 85.6892], [-279.7651, 85.6458], [-293.1861, 85.6463]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    ], convexity = 30);
}

module frame_joint_domain_10() {
    polygon(points = [
        [-269.5041, -302.4965], [-269.1958, -304.6056], [-200.4541, -301.5324], [-201.6018, -296.1952], [-201.9246, -294.5726],
        [-202.1910, -292.9105], [-202.4284, -290.9603], [-202.9645, -285.7568], [-203.4015, -281.0189], [-203.4665, -279.9454],
        [-271.2450, -282.9756], [-271.2272, -285.4000], [-271.1582, -287.9895], [-271.0312, -290.0204], [-270.6261, -294.7735],
        [-270.4533, -296.5075], [-270.2602, -297.9658]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    ], convexity = 30);
}

module frame_joint_domain_11() {
    polygon(points = [
        [-16.9339, -272.5040], [-16.7104, -271.5960], [-86.0089, -274.6941], [-85.9481, -275.1172], [-85.8517, -276.1135],
        [-85.7912, -277.1289], [-85.7312, -280.2445], [-85.7199, -296.4029], [-17.2369, -293.3412], [-17.2257, -284.0699],
        [-17.2348, -280.4040], [-17.2887, -276.1285], [-17.2439, -274.7257], [-17.1291, -273.6004]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    ], convexity = 30);
}

module frame_joint_domain_12() {
    polygon(points = [
        [-301.5750, -269.5154], [-300.9062, -269.6228], [-295.2315, -201.6493], [-295.7843, -201.5484], [-301.0781, -200.4201],
        [-302.6818, -200.0583], [-304.2567, -199.6526], [-307.9978, -198.5590], [-310.6104, -197.7548], [-313.8321, -196.6756],
        [-316.1826, -195.8120], [-316.5085, -195.6787], [-322.3201, -265.2919], [-319.0802, -266.1699], [-316.8179, -266.7210],
        [-310.3717, -268.1104], [-308.5108, -268.4762], [-306.3782, -268.8268]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    ], convexity = 30);
}

module frame_joint_domain_13() {
    polygon(points = [
        [-282.6516, -17.7703], [-301.6577, -17.7922], [-307.3185, -85.5990], [-285.5421, -85.5874], [-279.8742, -17.6962]
    ], paths = [
        [0, 1, 2, 3, 4]
    ], convexity = 30);
}

module frame_joint_domain_14() {
    polygon(points = [
        [-141.5485, -271.1186], [-119.2849, -271.1368], [-103.7135, -203.5127], [-125.9935, -203.5655]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_15() {
    polygon(points = [
        [-70.8630, -17.8498], [-83.2278, -17.8401], [-98.8202, -85.5559], [-86.9882, -85.5460], [-85.6518, -86.7549],
        [-85.6525, -124.6884], [-85.5654, -124.6983], [-61.1302, -18.5795], [-62.0119, -18.4173], [-64.1822, -18.1062],
        [-65.4264, -17.9895], [-66.9536, -17.9060]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    ], convexity = 30);
}

module frame_joint_domain_16() {
    polygon(points = [
        [-203.5333, -152.2110], [-203.5178, -130.1820], [-271.1378, -118.3131], [-271.1498, -140.3427]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_17() {
    polygon(points = [
        [271.0132, 290.0324], [270.8961, 291.4072], [264.9641, 290.7741], [274.2727, 203.5556], [277.6976, 203.5370],
        [279.4994, 203.4786], [281.0196, 203.3865], [285.7583, 202.9495], [291.2155, 202.3924], [293.1748, 202.1579],
        [294.8503, 201.8953], [296.3039, 201.6075], [288.9049, 270.9338], [287.2346, 271.0359], [283.8478, 271.1042],
        [272.8865, 271.1631], [272.2912, 272.6180], [271.9155, 273.7287], [271.6281, 274.8816], [271.4343, 276.0845],
        [271.3216, 277.3311], [271.2580, 278.8689], [271.2100, 285.4097], [271.1402, 288.0000]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    ], convexity = 30);
}

module frame_joint_domain_18() {
    polygon(points = [
        [294.0905, 17.8694], [315.9116, 17.8894], [308.6869, 85.5833], [286.8653, 85.5671]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_19() {
    polygon(points = [
        [17.8101, 107.5237], [17.8295, 85.6537], [85.5399, 94.2073], [85.5398, 116.0798]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_20() {
    polygon(points = [
        [271.1961, 117.6606], [271.2186, 139.5359], [203.4686, 130.9773], [203.4690, 109.1049]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_21() {
    polygon(points = [
        [17.8554, 346.7996], [17.8251, 324.9433], [85.6997, 316.6864], [85.6857, 338.5481]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_22() {
    polygon(points = [
        [268.2011, 310.5902], [266.9129, 316.5019], [191.7799, 325.6418], [193.0127, 323.0861], [194.3879, 320.0599],
        [195.5056, 317.4050], [196.4485, 314.8952], [197.6732, 311.2602], [198.4256, 308.8740], [199.6603, 304.7008],
        [200.0826, 303.1350], [200.1725, 302.7609], [270.6594, 294.1862], [270.6081, 294.7885], [270.4353, 296.5225],
        [270.2430, 297.9797], [269.5911, 302.0281], [268.8943, 306.8375], [268.5728, 308.7317]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    ], convexity = 30);
}

module frame_joint_domain_23() {
    polygon(points = [
        [85.7237, 279.2018], [85.7148, 293.1725], [67.8602, 293.2534], [67.3505, 180.7576], [85.5393, 180.6752],
        [85.5393, 193.0293], [85.5805, 197.2017], [85.6507, 198.4617], [85.7616, 199.4249], [85.9463, 200.3248],
        [86.1484, 200.9405], [86.3174, 201.3159], [86.5160, 201.6601], [86.8765, 202.1191], [87.3094, 202.5018],
        [87.8143, 202.8104], [88.3873, 203.0488], [89.0189, 203.2252], [89.1527, 203.2494], [89.4603, 271.1612],
        [86.7826, 271.1634], [86.2571, 273.1877], [85.9622, 274.8725], [85.8016, 276.6211]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    ], convexity = 30);
}

module frame_joint_domain_24() {
    polygon(points = [
        [273.3746, -17.1497], [272.3579, -16.9176], [274.5651, -86.0657], [274.6917, -86.0428], [275.6709, -85.9145],
        [276.6732, -85.8316], [279.2507, -85.7485], [296.2652, -85.7235], [294.0969, -17.7905], [282.6805, -17.7748],
        [280.6189, -17.7380], [278.6243, -17.6661], [276.7270, -17.5605], [275.3617, -17.4460], [274.2510, -17.3049]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    ], convexity = 30);
}

module frame_joint_domain_25() {
    polygon(points = [
        [301.4703, -269.4314], [302.1261, -269.3415], [299.9383, -200.7986], [295.0927, -201.8228], [293.2007, -202.1461],
        [291.2587, -202.3946], [283.8509, -203.1392], [280.3519, -203.4269], [278.8235, -203.4950], [278.3136, -203.5054],
        [280.4698, -271.0582], [285.3816, -271.0510], [287.7147, -270.9924], [289.7497, -270.8715], [294.2388, -270.4678],
        [296.4463, -270.2206]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    ], convexity = 30);
}

module frame_joint_domain_26() {
    polygon(points = [
        [17.2420, -102.8619], [17.2275, -124.5620], [85.5714, -124.4205], [85.5532, -102.7205]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_27() {
    polygon(points = [
        [271.1226, -124.0366], [271.0917, -102.3366], [203.4692, -102.4765], [203.4687, -124.1766]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_28() {
    polygon(points = [
        [17.7982, -338.8404], [17.8148, -360.6395], [85.6795, -354.0942], [85.6978, -332.2917]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module frame_joint_domain_29() {
    polygon(points = [
        [266.8500, -316.4555], [267.2119, -314.7854], [193.4438, -321.9000], [192.5775, -323.8267], [190.9527, -327.2285],
        [189.9001, -329.2692], [188.9165, -331.0769], [187.8766, -332.8862], [186.8940, -334.5077], [184.1828, -338.7090],
        [182.3000, -341.4392], [181.0012, -343.1784], [179.5561, -345.0401], [260.6728, -337.2167], [262.7639, -331.0942],
        [264.4891, -325.4099], [266.2501, -318.9518]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    ], convexity = 30);
}

module frame_joint_domain_30() {
    polygon(points = [
        [87.0046, -271.0690], [102.3399, -271.0747], [100.1931, -203.4995], [86.2068, -203.4712], [85.9174, -201.3479],
        [85.7558, -199.5973], [85.6705, -197.8064], [85.6307, -195.2002], [85.6196, -181.8974], [77.8038, -182.1456],
        [81.3478, -293.7012], [85.7304, -293.5620], [85.7417, -280.0355], [85.8152, -276.9281], [85.8883, -275.9202],
        [86.0033, -274.9343], [86.1695, -273.9747], [86.3880, -273.0403], [86.6523, -272.1267]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    ], convexity = 30);
}

M_joints = [[1,2,[32.336138117987566,136.58266699147163],57.06125907870988,38.67716598571674,[-12.83858299285837,7.16141700714163]],[5,2,[256.2170492115984,-8.467216860370549],57.06125907870988,93.27915851028523,[-31.139579255142614,30.860420744857386]],[0,3,[-251.1940238396848,61.411599507632864],277.3456590993838,79.87740560872571,[-26.438702804362855,26.561297195637145]],[0,1,[-32.448878861423665,126.7092511819895],293.02451173245254,49.72808919633396,[-16.36404459816698,16.63595540183302]],[1,4,[-5.511882018869134,-4.5879340820127075],-83.91147184580483,69.62648500042326,[-23.31324250021163,23.18675749978837]]];
M_placements = [[28.525000000000002,[-165.7840189844955,11.824223965563675],[-227.3546845977615,118.33087499999999],0],[65.95,[-50.08464207297149,31.742236435169588],[-5.516379858842416,69.17325],0],[76.92500000000001,[-25.600289569670437,174.313544373803],[251.13864337163096,73.890375],0],[18.075000000000003,[-174.60638575341875,-121.73927500681813],[-251.29880412612113,-57.376125],0],[47.0,[64.85625534916488,-65.50074490111496],[-5.5143516383764695,-93.824075],0],[82.0,[95.13845061190125,190.08651546963745],[241.7403108414382,-80.418],0]];
M_assembly_order = [1,6,2,4,3,5];
M_print_footprints = [[240.00722092826766,240.04719803736816,10.5],[158.58801677274232,158.27835705082305,10.5],[250.73700756131055,250.6950149157516,10.5],[238.63407906043255,238.6570628238971,10.5],[172.336191699271,172.3521526016711,10.5],[207.0295747859717,207.01127723859906,10.5]];
module M_mask_0() {
    polygon(points = [
        [-55.6277, 117.3076], [-55.4131, 116.7869], [-55.3096, 116.8309], [-55.3810, 117.0043], [-9.5577, 136.4783],
        [-9.4087, 136.3379], [-9.2956, 136.3859], [-9.6872, 136.7549], [-11.8561, 138.7211], [-14.0588, 140.6408],
        [-16.2938, 142.5139], [-18.5610, 144.3412], [-20.8598, 146.1219], [-23.1885, 147.8569], [-25.5466, 149.5445],
        [-27.9339, 151.1871], [-30.3490, 152.7832], [-32.7918, 154.3327], [-35.2602, 155.8356], [-37.7548, 157.2927],
        [-40.2734, 158.7033], [-42.8168, 160.0681], [-45.3826, 161.3863], [-47.9718, 162.6587], [-50.5819, 163.8838],
        [-53.2131, 165.0639], [-55.8637, 166.1967], [-58.5339, 167.2837], [-61.2221, 168.3249], [-63.9282, 169.3187],
        [-66.6516, 170.2676], [-69.3900, 171.1691], [-72.1442, 172.0249], [-74.8999, 172.8303], [-77.6945, 173.5975],
        [-80.4892, 174.3144], [-83.2958, 174.9847], [-86.1137, 175.6092], [-88.9422, 176.1880], [-91.7803, 176.7194],
        [-94.6267, 177.2051], [-97.4821, 177.6449], [-100.3435, 178.0383], [-103.2117, 178.3851], [-106.0859, 178.6853],
        [-108.9637, 178.9398], [-111.8461, 179.1477], [-114.7330, 179.3098], [-117.6207, 179.4254], [-120.5106, 179.4945],
        [-123.4012, 179.5178], [-126.2926, 179.4952], [-129.1818, 179.4254], [-132.0702, 179.3098], [-134.9556, 179.1477],
        [-137.8387, 178.9398], [-140.7174, 178.6853], [-143.5908, 178.3843], [-146.4597, 178.0375], [-149.3211, 177.6442],
        [-152.1765, 177.2051], [-155.0229, 176.7194], [-157.8603, 176.1880], [-160.6888, 175.6100], [-163.5074, 174.9847],
        [-166.3141, 174.3144], [-169.1080, 173.5975], [-171.8906, 172.8341], [-174.6591, 172.0249], [-177.4125, 171.1691],
        [-180.1516, 170.2668], [-182.8743, 169.3187], [-185.5804, 168.3249], [-188.2694, 167.2837], [-190.9395, 166.1967],
        [-193.5902, 165.0632], [-196.2213, 163.8846], [-198.8315, 162.6587], [-201.4206, 161.3863], [-203.9865, 160.0681],
        [-206.5291, 158.7040], [-209.0485, 157.2927], [-211.5431, 155.8356], [-214.0114, 154.3326], [-216.4535, 152.7832],
        [-218.8694, 151.1871], [-221.2559, 149.5453], [-223.6147, 147.8561], [-225.9435, 146.1220], [-228.2423, 144.3412],
        [-230.5095, 142.5139], [-232.7445, 140.6400], [-234.9464, 138.7211], [-237.1161, 136.7549], [-239.2512, 134.7429],
        [-241.3475, 132.6870], [-244.3103, 130.1148], [-247.1946, 127.4797], [-249.9971, 124.7853], [-252.7177, 122.0339],
        [-255.3581, 119.2269], [-257.9188, 116.3636], [-260.3992, 113.4478], [-262.8008, 110.4794], [-265.1228, 107.4608],
        [-267.3659, 104.3933], [-269.5311, 101.2769], [-271.9293, 97.6192], [-273.6283, 94.9066], [-275.5613, 91.6547],
        [-277.4178, 88.3606], [-279.1976, 85.0254], [-280.9017, 81.6504], [-282.5306, 78.2371], [-284.0844, 74.7871],
        [-285.5632, 71.3011], [-286.9684, 67.7806], [-288.2993, 64.2279], [-289.5566, 60.6437], [-290.7410, 57.0287],
        [-291.0162, 56.1268], [-290.8938, 56.1425], [-290.8337, 56.3393], [-211.5405, 66.5613], [-211.5621, 66.3694],
        [-211.4472, 66.3842], [-211.3518, 67.2316], [-210.6666, 72.5745], [-210.2890, 75.1858], [-209.4659, 80.2919],
        [-208.5522, 85.2420], [-208.0614, 87.6585], [-207.5497, 90.0361], [-206.4591, 94.6764], [-205.7263, 97.5212],
        [-204.6621, 101.3495], [-204.0216, 103.4966], [-203.3592, 105.6073], [-202.6775, 107.6785], [-201.2499, 111.7111],
        [-200.5062, 113.6704], [-199.7420, 115.5928], [-198.9585, 117.4776], [-198.1554, 119.3256], [-197.3322, 121.1361],
        [-196.4903, 122.9105], [-195.6297, 124.6475], [-194.7496, 126.3476], [-193.8509, 128.0118], [-192.9328, 129.6399],
        [-191.9967, 131.2312], [-191.0419, 132.7858], [-190.0699, 134.3044], [-189.0801, 135.7877], [-188.0715, 137.2350],
        [-187.0458, 138.6471], [-186.0022, 140.0224], [-184.9421, 141.3625], [-183.8648, 142.6680], [-182.7704, 143.9368],
        [-181.6588, 145.1727], [-180.5316, 146.3711], [-179.3879, 147.5364], [-178.2271, 148.6658], [-177.0513, 149.7608],
        [-175.8583, 150.8213], [-174.6512, 151.8481], [-173.4269, 152.8396], [-172.1884, 153.7968], [-170.9342, 154.7209],
        [-169.6659, 155.6099], [-168.3818, 156.4652], [-167.0835, 157.2876], [-165.7696, 158.0755], [-164.4421, 158.8305],
        [-163.1005, 159.5518], [-161.7454, 160.2402], [-160.3754, 160.8949], [-158.9926, 161.5167], [-157.5956, 162.1056],
        [-156.1858, 162.6623], [-154.7627, 163.1854], [-153.3259, 163.6755], [-151.8771, 164.1342], [-150.4157, 164.5600],
        [-148.9414, 164.9536], [-147.4544, 165.3151], [-145.9554, 165.6444], [-144.4451, 165.9415], [-142.9220, 166.2080],
        [-141.3885, 166.4422], [-139.8421, 166.6443], [-138.2852, 166.8157], [-136.7170, 166.9550], [-135.1375, 167.0635],
        [-133.5474, 167.1406], [-131.9468, 167.1870], [-130.3357, 167.2027], [-128.2699, 167.1848], [-126.2296, 167.1301],
        [-124.2148, 167.0410], [-122.2257, 166.9151], [-120.2621, 166.7519], [-118.3240, 166.5542], [-116.4116, 166.3198],
        [-114.5239, 166.0480], [-112.6617, 165.7410], [-110.8245, 165.3974], [-109.0127, 165.0163], [-107.2257, 164.6001],
        [-105.4643, 164.1464], [-103.7277, 163.6569], [-102.0158, 163.1299], [-100.3287, 162.5663], [-98.6664, 161.9660],
        [-97.0289, 161.3291], [-95.4161, 160.6548], [-93.8280, 159.9439], [-92.2640, 159.1955], [-90.7246, 158.4105],
        [-89.2100, 157.5874], [-87.7193, 156.7283], [-86.2526, 155.8318], [-84.8107, 154.8979], [-83.3934, 153.9259],
        [-82.0000, 152.9171], [-80.6299, 151.8702], [-79.2843, 150.7859], [-77.9628, 149.6649], [-76.6653, 148.5051],
        [-75.0444, 146.9703], [-74.1401, 146.0727], [-72.9133, 144.8002], [-71.7105, 143.4889], [-70.5308, 142.1401],
        [-69.3743, 140.7538], [-68.2418, 139.3285], [-67.1331, 137.8657], [-66.0475, 136.3639], [-64.9844, 134.8239],
        [-63.9451, 133.2463], [-62.9291, 131.6297], [-61.9362, 129.9749], [-60.9664, 128.2810], [-60.0191, 126.5488],
        [-59.0956, 124.7784], [-58.1946, 122.9689], [-57.3161, 121.1203], [-56.4607, 119.2335]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248]
    ], convexity = 30);
}

module M_mask_1() {
    polygon(points = [
        [47.1614, 122.9689], [48.0624, 124.7784], [48.7623, 126.1191], [48.6674, 126.1805], [48.5803, 126.0136],
        [16.0354, 147.0990], [16.2141, 147.2067], [16.1091, 147.2747], [14.2040, 146.1267], [11.3387, 144.3466],
        [8.4863, 142.5200], [5.6466, 140.6469], [2.8211, 138.7280], [0.0092, 136.7619], [-2.7884, 134.7507],
        [-5.5086, 132.7389], [-7.5520, 134.7429], [-9.5340, 136.6106], [-9.6471, 136.5625], [-9.4981, 136.4221],
        [-55.3524, 116.9350], [-55.4239, 117.1083], [-55.5274, 117.0643], [-54.8179, 115.3427], [-54.0306, 113.3388],
        [-53.2656, 111.2958], [-52.5232, 109.2130], [-51.8031, 107.0918], [-51.1056, 104.9317], [-50.4305, 102.7318],
        [-49.7779, 100.4925], [-48.5390, 95.8949], [-47.9523, 93.5377], [-47.3880, 91.1410], [-46.8461, 88.7038],
        [-46.6496, 87.7681], [-46.3261, 86.2279], [-45.3508, 81.1544], [-44.8960, 78.5595], [-44.0511, 73.2469],
        [-43.2933, 67.7756], [-42.6216, 62.1428], [-42.0354, 56.3494], [-41.5338, 50.3946], [-41.1177, 44.2777],
        [-40.7848, 37.9986], [-40.5367, 31.5557], [-40.4437, 28.2745], [-40.3200, 21.5867], [-40.2885, 18.1823],
        [-40.2788, -3.7800], [-40.2788, -8.4473], [-40.1663, -8.4353], [-40.1663, -8.2467], [29.1425, -0.8538],
        [29.1425, -1.0423], [29.2550, -1.0303], [29.2560, 18.1823], [29.2867, 21.5867], [29.4105, 28.2742],
        [29.6174, 34.7982], [29.7523, 37.9987], [29.9075, 41.1578], [30.2824, 47.3568], [30.7412, 53.3927],
        [31.2847, 59.2664], [31.9137, 64.9795], [32.6289, 70.5315], [33.0186, 73.2466], [33.8626, 78.5591],
        [34.7943, 83.7107], [35.8129, 88.7038], [36.9192, 93.5382], [37.5057, 95.8949], [38.2528, 98.6674],
        [38.7447, 100.4925], [39.3980, 102.7317], [40.0731, 104.9317], [40.7707, 107.0919], [41.4899, 109.2130],
        [42.2324, 111.2958], [42.9973, 113.3388], [43.7846, 115.3427], [44.5952, 117.3076], [45.4274, 119.2335],
        [46.2828, 121.1203]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85]
    ], convexity = 30);
}

module M_mask_2() {
    polygon(points = [
        [216.6955, 22.1583], [216.9282, 16.8089], [217.0440, 16.7338], [217.0340, 16.9637], [295.4013, -33.8096],
        [295.3607, -34.0067], [295.4621, -34.0724], [295.9952, -31.4825], [296.6887, -27.7967], [297.3176, -24.1057],
        [297.8827, -20.4102], [298.3841, -16.7116], [298.8201, -13.0123], [299.1924, -9.3122], [299.5008, -5.6137],
        [299.6277, -3.6998], [299.7448, -1.9181], [299.9241, 1.7730], [300.0397, 5.4589], [300.0900, 9.1380],
        [300.0757, 12.8097], [299.9969, 16.4708], [299.8536, 20.1207], [299.6457, 23.7594], [299.3725, 27.3839],
        [299.0347, 30.9926], [298.6324, 34.5856], [298.1648, 38.1613], [297.6319, 41.7169], [297.0337, 45.2522],
        [296.3709, 48.7657], [295.6428, 52.2561], [294.8494, 55.7217], [293.9907, 59.1610], [293.0659, 62.5734],
        [292.0765, 65.9573], [291.0211, 69.3105], [289.9004, 72.6322], [288.7143, 75.9209], [287.4622, 79.1758],
        [286.1447, 82.3948], [284.7612, 85.5771], [283.3115, 88.7211], [281.7958, 91.8253], [280.2148, 94.8883],
        [278.7177, 97.6332], [276.8537, 100.8852], [275.0751, 103.8164], [273.2281, 106.7016], [271.3166, 109.5388],
        [269.3383, 112.3258], [267.2938, 115.0633], [265.1825, 117.7482], [263.0044, 120.3798], [260.7609, 122.9559],
        [258.4498, 125.4773], [256.0726, 127.9393], [253.6285, 130.3443], [251.1169, 132.6870], [248.7917, 134.7456],
        [246.4408, 136.7573], [244.0659, 138.7231], [241.6655, 140.6424], [239.2417, 142.5159], [236.7948, 144.3429],
        [234.3252, 146.1242], [231.8331, 147.8581], [229.3186, 149.5462], [226.7815, 151.1886], [224.2248, 152.7844],
        [221.6464, 154.3337], [219.0485, 155.8365], [216.4311, 157.2934], [213.7941, 158.7046], [211.1377, 160.0685],
        [208.4632, 161.3873], [205.7715, 162.6589], [203.0617, 163.8847], [200.3347, 165.0639], [197.5911, 166.1974],
        [194.8318, 167.2843], [192.0568, 168.3246], [189.2667, 169.3192], [186.4616, 170.2680], [183.6423, 171.1695],
        [180.8087, 172.0252], [177.9624, 172.8344], [175.1025, 173.5977], [172.2314, 174.3146], [169.3468, 174.9856],
        [166.4517, 175.6094], [163.5453, 176.1881], [160.6285, 176.7195], [157.7011, 177.2052], [154.7640, 177.6450],
        [151.8179, 178.0376], [148.8636, 178.3844], [145.9002, 178.6854], [142.9286, 178.9398], [139.9503, 179.1485],
        [136.9644, 179.3098], [133.9726, 179.4254], [130.9741, 179.4945], [127.9710, 179.5178], [124.9620, 179.4952],
        [121.9484, 179.4254], [118.9304, 179.3098], [115.9101, 179.1477], [112.8846, 178.9398], [109.8568, 178.6854],
        [106.8276, 178.3844], [103.7946, 178.0377], [100.7616, 177.6451], [97.7271, 177.2053], [94.6927, 176.7197],
        [91.6575, 176.1883], [88.6231, 175.6096], [85.5887, 174.9852], [82.5558, 174.3142], [79.5252, 173.5975],
        [76.4961, 172.8349], [73.4699, 172.0251], [70.4469, 171.1695], [67.4276, 170.2682], [64.4120, 169.3203],
        [61.4009, 168.3258], [58.3952, 167.2849], [55.3947, 166.1982], [52.3994, 165.0649], [49.4110, 163.8859],
        [46.4292, 162.6603], [43.4543, 161.3883], [40.4876, 160.0704], [37.5285, 158.7060], [34.5784, 157.2959],
        [31.6365, 155.8385], [28.7051, 154.3360], [25.7828, 152.7863], [22.8718, 151.1908], [19.9712, 149.5495],
        [17.0819, 147.8610], [15.8232, 147.1025], [15.9282, 147.0344], [16.1069, 147.1421], [48.6151, 126.0804],
        [48.5280, 125.9134], [48.6228, 125.8520], [48.9866, 126.5488], [49.9332, 128.2810], [50.9029, 129.9749],
        [51.8958, 131.6297], [52.9126, 133.2463], [53.9519, 134.8239], [55.0143, 136.3640], [56.0998, 137.8657],
        [57.2092, 139.3285], [58.3418, 140.7538], [59.4976, 142.1401], [60.6772, 143.4889], [61.8800, 144.8002],
        [63.1067, 146.0726], [64.3573, 147.3082], [65.6311, 148.5049], [66.9295, 149.6641], [68.2511, 150.7859],
        [69.5966, 151.8702], [70.9668, 152.9171], [72.3601, 153.9259], [73.7783, 154.8973], [75.0202, 155.7060],
        [76.6862, 156.7283], [78.1775, 157.5881], [79.6914, 158.4105], [81.2314, 159.1955], [82.7948, 159.9431],
        [84.3829, 160.6548], [85.9964, 161.3291], [87.6339, 161.9660], [89.2955, 162.5663], [90.9826, 163.1299],
        [92.6944, 163.6569], [94.4318, 164.1464], [96.1925, 164.6001], [97.9802, 165.0170], [99.7920, 165.3974],
        [101.6285, 165.7410], [103.4906, 166.0480], [105.3783, 166.3198], [107.2907, 166.5542], [109.2296, 166.7519],
        [111.1932, 166.9151], [113.1823, 167.0410], [115.1971, 167.1301], [117.2367, 167.1848], [119.3025, 167.2027],
        [121.3714, 167.1848], [123.4192, 167.1308], [125.4468, 167.0410], [127.4525, 166.9159], [129.4387, 166.7549],
        [131.4031, 166.5579], [133.3472, 166.3257], [135.2704, 166.0576], [137.1717, 165.7551], [139.0527, 165.4159],
        [140.9119, 165.0422], [142.7501, 164.6327], [144.5673, 164.1879], [146.3635, 163.7080], [148.1379, 163.1936],
        [149.8913, 162.6434], [151.6230, 162.0587], [153.3328, 161.4395], [155.0217, 160.7845], [156.6881, 160.0950],
        [158.3343, 159.3704], [159.9572, 158.6113], [161.5591, 157.8179], [163.1393, 156.9892], [164.6971, 156.1269],
        [166.2331, 155.2294], [167.7474, 154.2974], [169.2393, 153.3318], [170.7087, 152.3317], [172.1564, 151.2965],
        [173.5824, 150.2275], [174.9860, 149.1249], [176.3663, 147.9871], [177.7243, 146.8162], [179.0606, 145.6110],
        [180.3744, 144.3728], [181.6650, 143.0986], [182.9332, 141.7929], [184.1790, 140.4513], [185.4024, 139.0775],
        [186.6026, 137.6692], [187.7796, 136.2278], [188.9334, 134.7528], [190.0648, 133.2440], [191.1738, 131.7022],
        [192.2589, 130.1259], [193.3208, 128.5180], [194.3602, 126.8757], [195.3765, 125.2004], [196.3689, 123.4921],
        [197.3380, 121.7507], [198.2840, 119.9756], [199.2060, 118.1682], [200.1049, 116.3279], [200.9790, 114.4544],
        [201.8308, 112.5479], [202.6593, 110.6085], [203.4631, 108.6367], [204.2430, 106.6327], [204.9997, 104.5949],
        [205.7317, 102.5255], [206.4404, 100.4242], [207.3980, 97.3962], [208.4210, 93.9227], [209.0323, 91.6916],
        [209.6198, 89.4278], [210.1833, 87.1317], [210.7221, 84.8041], [211.2361, 82.4447], [212.1911, 77.6279],
        [212.6316, 75.1728], [213.4381, 70.1658], [214.1457, 65.0316], [214.7536, 59.7717], [215.0204, 57.0950],
        [215.4777, 51.6456], [215.6688, 48.8750], [215.9746, 43.2383], [216.1793, 37.4780], [216.2820, 31.5929],
        [216.2948, 28.6015]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275]
    ], convexity = 30);
}

module M_mask_3() {
    polygon(points = [
        [-211.6591, 64.5023], [-211.4127, 66.6912], [-211.5275, 66.6764], [-211.5491, 66.4845], [-290.8578, 56.2606],
        [-290.7977, 56.4574], [-290.9202, 56.4416], [-291.8527, 53.3853], [-292.8922, 49.7149], [-293.8605, 46.0176],
        [-294.7567, 42.2962], [-295.5815, 38.5516], [-296.3366, 34.7853], [-297.0204, 30.9980], [-297.6351, 27.1921],
        [-298.1807, 23.3681], [-298.6565, 19.5276], [-299.0641, 15.6714], [-299.4033, 11.8025], [-299.6742, 7.9209],
        [-299.8784, 4.0288], [-300.0157, 0.1262], [-300.0862, -3.8026], [-300.0900, -7.7006], [-300.0285, -11.6234],
        [-299.9009, -15.5498], [-299.7088, -19.4793], [-299.4521, -23.4102], [-299.1309, -27.3412], [-298.7459, -31.2698],
        [-298.2979, -35.1970], [-297.7861, -39.1196], [-297.2120, -43.0362], [-296.5756, -46.9460], [-295.8777, -50.8483],
        [-295.1183, -54.7409], [-294.2980, -58.6222], [-293.4170, -62.4907], [-292.4752, -66.3465], [-291.4741, -70.1865],
        [-290.4130, -74.0100], [-289.2933, -77.8162], [-288.1151, -81.6029], [-286.8784, -85.3694], [-285.5846, -89.1134],
        [-284.2323, -92.8348], [-282.8237, -96.5308], [-281.3581, -100.2012], [-279.8362, -103.8439], [-278.2587, -107.4581],
        [-276.6257, -111.0423], [-274.9372, -114.5950], [-273.1946, -118.1146], [-271.3980, -121.5998], [-269.5466, -125.0498],
        [-267.6426, -128.4622], [-265.6854, -131.8371], [-263.6756, -135.1715], [-261.6132, -138.4654], [-259.4990, -141.7166],
        [-257.3331, -144.9235], [-255.1168, -148.0862], [-252.8495, -151.2016], [-250.5319, -154.2690], [-248.1647, -157.2876],
        [-245.7479, -160.2553], [-243.2816, -163.1704], [-240.7673, -166.0331], [-238.2048, -168.8402], [-235.5935, -171.5911],
        [-232.9357, -174.2849], [-230.2306, -176.9195], [-227.4532, -179.5178], [-116.1195, -179.5178], [-118.9476, -177.9493],
        [-121.4351, -176.5253], [-123.8872, -175.0752], [-126.3034, -173.6003], [-128.6844, -172.0999], [-131.0301, -170.5756],
        [-133.3406, -169.0258], [-135.6158, -167.4520], [-137.8557, -165.8535], [-140.0605, -164.2311], [-142.2307, -162.5847],
        [-144.3665, -160.9150], [-146.4677, -159.2214], [-148.5345, -157.5038], [-150.5661, -155.7638], [-152.5646, -153.9998],
        [-154.5280, -152.2133], [-156.4584, -150.4043], [-158.3542, -148.5729], [-160.2164, -146.7183], [-162.0448, -144.8419],
        [-163.8402, -142.9438], [-165.6012, -141.0232], [-167.3300, -139.0809], [-169.0250, -137.1176], [-170.6870, -135.1326],
        [-172.3161, -133.1258], [-173.9122, -131.0989], [-175.4753, -129.0501], [-177.0063, -126.9812], [-178.5042, -124.8920],
        [-179.9707, -122.7818], [-181.4042, -120.6522], [-182.8055, -118.5023], [-184.1746, -116.3321], [-185.5122, -114.1425],
        [-186.8176, -111.9334], [-188.0915, -109.7047], [-189.3340, -107.4574], [-190.5449, -105.1905], [-191.7245, -102.9049],
        [-192.8725, -100.6013], [-193.9891, -98.2782], [-195.0750, -95.9371], [-196.1302, -93.5779], [-197.1546, -91.2008],
        [-198.1483, -88.8064], [-199.1113, -86.3941], [-200.0436, -83.9637], [-200.9459, -81.5160], [-201.8183, -79.0519],
        [-202.6599, -76.5705], [-203.4716, -74.0725], [-204.2540, -71.5574], [-205.0057, -69.0264], [-205.7289, -66.4790],
        [-206.4215, -63.9150], [-207.0855, -61.3360], [-207.7196, -58.7405], [-208.3244, -56.1293], [-208.9000, -53.5030],
        [-209.4472, -50.8617], [-209.9651, -48.2054], [-210.4546, -45.5333], [-210.9155, -42.8470], [-211.3479, -40.1468],
        [-212.1268, -34.7012], [-212.4745, -31.9586], [-213.0848, -26.4297], [-213.3486, -23.6458], [-213.7923, -18.0362],
        [-214.1259, -12.3744], [-214.3508, -6.6627], [-214.4250, -3.6873], [-214.4850, 1.9978], [-214.4760, 4.9073],
        [-214.3793, 10.7639], [-214.1769, 16.6653], [-213.8695, 22.6102], [-213.4590, 28.6008], [-213.4073, 34.9933],
        [-213.2551, 41.2184], [-213.1411, 44.2697], [-212.8390, 50.2516], [-212.4394, 56.0722], [-212.2034, 58.9215]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159]
    ], convexity = 30);
}

module M_mask_4() {
    polygon(points = [
        [29.2455, -179.5178], [29.2550, -0.7286], [29.1425, -0.7406], [29.1425, -0.9292], [-40.1663, -8.3221],
        [-40.1663, -8.1335], [-40.2788, -8.1455], [-40.2788, -179.5178]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7]
    ], convexity = 30);
}

module M_mask_5() {
    polygon(points = [
        [295.2379, -35.1615], [295.5270, -33.7570], [295.4257, -33.6913], [295.3851, -33.8884], [217.0380, 16.8717],
        [217.0280, 17.1016], [216.9122, 17.1767], [216.9728, 15.7821], [217.0650, 12.6181], [217.1265, 9.4703],
        [217.1573, 6.3390], [217.1573, 3.2242], [217.1265, 0.1264], [216.9728, -6.0191], [216.8492, -9.0652],
        [216.6955, -12.0944], [216.5111, -15.1055], [216.2952, -18.0994], [216.0478, -21.0745], [215.7705, -24.0332],
        [215.4632, -26.9723], [215.1243, -29.8926], [214.7548, -32.7949], [214.3538, -35.6777], [213.9220, -38.5418],
        [213.4611, -41.3864], [212.9679, -44.2128], [212.4432, -47.0191], [211.8893, -49.8051], [211.3039, -52.5716],
        [210.6878, -55.3185], [210.0410, -58.0445], [209.3635, -60.7494], [208.6545, -63.4355], [207.9147, -66.1000],
        [207.1450, -68.7441], [206.3438, -71.3657], [205.5119, -73.9679], [204.6493, -76.5475], [203.7560, -79.1061],
        [202.8319, -81.6422], [201.8771, -84.1573], [200.8916, -86.6499], [199.8747, -89.1207], [198.8278, -91.5683],
        [197.7494, -93.9941], [196.6403, -96.3967], [195.5004, -98.7760], [194.3299, -101.1320], [193.1286, -103.4656],
        [191.8967, -105.7759], [190.6332, -108.0615], [189.3398, -110.3238], [188.0150, -112.5621], [186.6594, -114.7765],
        [185.2739, -116.9661], [183.8569, -119.1317], [182.4084, -121.2725], [180.9299, -123.3887], [179.4208, -125.4800],
        [177.8802, -127.5459], [176.3096, -129.5856], [174.7083, -131.6013], [173.0755, -133.5907], [171.4121, -135.5539],
        [169.7186, -137.4909], [167.9929, -139.4024], [166.2373, -141.2869], [164.4509, -143.1460], [162.6331, -144.9780],
        [160.7860, -146.7824], [158.9060, -148.5605], [156.9968, -150.3101], [155.0560, -152.0336], [153.0846, -153.7300],
        [151.0824, -155.3972], [149.0495, -157.0375], [146.9858, -158.6501], [144.8907, -160.2334], [142.7656, -161.7890],
        [140.6090, -163.3154], [138.4224, -164.8133], [136.2044, -166.2828], [133.9556, -167.7223], [131.6768, -169.1334],
        [129.3665, -170.5152], [127.0255, -171.8663], [124.6530, -173.1889], [122.2505, -174.4808], [119.8165, -175.7421],
        [117.3524, -176.9741], [114.8569, -178.1754], [111.9577, -179.5187], [123.2991, -179.5035], [128.6415, -179.4690],
        [133.9030, -179.4007], [137.7944, -179.3220], [141.6402, -179.2139], [145.4389, -179.0721], [149.1927, -178.8913],
        [151.6695, -178.7472], [156.5613, -178.3960], [161.3701, -177.9517], [163.7453, -177.6913], [166.0985, -177.4030],
        [168.4315, -177.0855], [170.7443, -176.7394], [173.0371, -176.3611], [175.3090, -175.9489], [177.5599, -175.5029],
        [179.7907, -175.0223], [182.0014, -174.5035], [184.1911, -173.9470], [186.3607, -173.3507], [188.5094, -172.7131],
        [190.6372, -172.0326], [192.7455, -171.3086], [194.8330, -170.5394], [196.8995, -169.7229], [198.9465, -168.8590],
        [200.9719, -167.9455], [202.9769, -166.9809], [204.9618, -165.9651], [206.9257, -164.8953], [208.8693, -163.7714],
        [210.7927, -162.5903], [212.6950, -161.3514], [214.5771, -160.0546], [219.6433, -156.3542], [222.7891, -153.9515],
        [225.8726, -151.4887], [228.8930, -148.9682], [231.8527, -146.3929], [234.7507, -143.7620], [237.5858, -141.0771],
        [240.3599, -138.3405], [243.0711, -135.5535], [245.7207, -132.7170], [248.3072, -129.8333], [250.8314, -126.9015],
        [253.2940, -123.9255], [255.6936, -120.9052], [258.0309, -117.8428], [260.3058, -114.7385], [262.5177, -111.5959],
        [264.6673, -108.4135], [266.7546, -105.1944], [268.7781, -101.9408], [270.7400, -98.6519], [272.6389, -95.3307],
        [274.4740, -91.9781], [276.2468, -88.5939], [277.9557, -85.1827], [279.6024, -81.7431], [281.1860, -78.2779],
        [282.7058, -74.7872], [284.1626, -71.2740], [285.5555, -67.7390], [286.8862, -64.1831], [288.1523, -60.6084],
        [289.3554, -57.0157], [290.4954, -53.4064], [291.5709, -49.7822], [292.5833, -46.1437], [293.5327, -42.4940],
        [294.4176, -38.8330]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165]
    ], convexity = 30);
}

module M_joint_domain_0() {
    polygon(points = [
        [59.4596, 142.1726], [59.8989, 142.6749], [36.2121, 158.0214], [34.6002, 157.2509], [31.6590, 155.7938],
        [28.7283, 154.2917], [25.8065, 152.7423], [22.8961, 151.1471], [19.9961, 149.5062], [17.1075, 147.8180],
        [14.4883, 146.2396], [47.9106, 124.5857], [48.0178, 124.8011], [48.9425, 126.5724], [49.8895, 128.3054],
        [50.8598, 130.0002], [51.8532, 131.6559], [52.8706, 133.2734], [53.9104, 134.8518], [54.9734, 136.3928],
        [56.0596, 137.8955], [57.1697, 139.3592], [58.3031, 140.7854]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    ], convexity = 30);
}

module M_joint_domain_1() {
    polygon(points = [
        [217.0228, 15.7839], [217.0455, 15.0051], [295.0969, -35.5635], [295.1890, -35.1510], [295.9461, -31.4728],
        [296.6394, -27.7879], [297.2682, -24.0977], [297.8332, -20.4030], [298.3345, -16.7053], [298.7704, -13.0069],
        [298.8573, -12.1434], [216.0871, 41.4824], [216.2293, 37.4794], [216.3320, 31.5934], [216.3448, 28.6032],
        [216.7454, 22.1610]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    ], convexity = 30);
}

module M_joint_domain_2() {
    polygon(points = [
        [-211.4015, 67.2375], [-211.2819, 68.1700], [-290.3789, 57.9734], [-290.6933, 57.0137], [-291.8047, 53.3712],
        [-292.8440, 49.7018], [-293.8120, 46.0054], [-294.7079, 42.2850], [-295.5326, 38.5413], [-296.1730, 35.3469],
        [-213.1010, 46.0560], [-212.8889, 50.2546], [-212.4893, 56.0759], [-212.2532, 58.9260], [-211.7088, 64.5076]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    ], convexity = 30);
}

module M_joint_domain_3() {
    polygon(points = [
        [-49.7298, 100.5060], [-49.0091, 97.8317], [18.6355, 126.5793], [11.1589, 144.1721], [8.5135, 142.4781],
        [5.6744, 140.6054], [2.8495, 138.6868], [0.0382, 136.7211], [-2.7589, 134.7103], [-5.5131, 132.6734],
        [-7.5867, 134.7068], [-9.7211, 136.7182], [-10.7638, 137.6635], [-56.0528, 118.4165], [-55.5816, 117.3271],
        [-54.7715, 115.3614], [-53.9839, 113.3567], [-53.2187, 111.3129], [-52.4759, 109.2294], [-51.7557, 107.1076],
        [-51.0579, 104.9467], [-50.3826, 102.7461]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
    ], convexity = 30);
}

module M_joint_domain_4() {
    polygon(points = [
        [29.2039, -21.0989], [29.2051, 0.7243], [-40.2287, -6.6820], [-40.2287, -28.5051]
    ], paths = [
        [0, 1, 2, 3]
    ], convexity = 30);
}

module part_mask(kind,i) {
    if(kind=="frame" && i==0) frame_mask_0();
    if(kind=="frame" && i==1) frame_mask_1();
    if(kind=="frame" && i==2) frame_mask_2();
    if(kind=="frame" && i==3) frame_mask_3();
    if(kind=="frame" && i==4) frame_mask_4();
    if(kind=="frame" && i==5) frame_mask_5();
    if(kind=="frame" && i==6) frame_mask_6();
    if(kind=="frame" && i==7) frame_mask_7();
    if(kind=="frame" && i==8) frame_mask_8();
    if(kind=="frame" && i==9) frame_mask_9();
    if(kind=="frame" && i==10) frame_mask_10();
    if(kind=="frame" && i==11) frame_mask_11();
    if(kind=="frame" && i==12) frame_mask_12();
    if(kind=="frame" && i==13) frame_mask_13();
    if(kind=="frame" && i==14) frame_mask_14();
    if(kind=="frame" && i==15) frame_mask_15();
    if(kind=="frame" && i==16) frame_mask_16();
    if(kind=="frame" && i==17) frame_mask_17();
    if(kind=="frame" && i==18) frame_mask_18();
    if(kind=="frame" && i==19) frame_mask_19();
    if(kind=="M" && i==0) M_mask_0();
    if(kind=="M" && i==1) M_mask_1();
    if(kind=="M" && i==2) M_mask_2();
    if(kind=="M" && i==3) M_mask_3();
    if(kind=="M" && i==4) M_mask_4();
    if(kind=="M" && i==5) M_mask_5();
}
module joint_domain(kind,i) {
    if(kind=="frame" && i==0) frame_joint_domain_0();
    if(kind=="frame" && i==1) frame_joint_domain_1();
    if(kind=="frame" && i==2) frame_joint_domain_2();
    if(kind=="frame" && i==3) frame_joint_domain_3();
    if(kind=="frame" && i==4) frame_joint_domain_4();
    if(kind=="frame" && i==5) frame_joint_domain_5();
    if(kind=="frame" && i==6) frame_joint_domain_6();
    if(kind=="frame" && i==7) frame_joint_domain_7();
    if(kind=="frame" && i==8) frame_joint_domain_8();
    if(kind=="frame" && i==9) frame_joint_domain_9();
    if(kind=="frame" && i==10) frame_joint_domain_10();
    if(kind=="frame" && i==11) frame_joint_domain_11();
    if(kind=="frame" && i==12) frame_joint_domain_12();
    if(kind=="frame" && i==13) frame_joint_domain_13();
    if(kind=="frame" && i==14) frame_joint_domain_14();
    if(kind=="frame" && i==15) frame_joint_domain_15();
    if(kind=="frame" && i==16) frame_joint_domain_16();
    if(kind=="frame" && i==17) frame_joint_domain_17();
    if(kind=="frame" && i==18) frame_joint_domain_18();
    if(kind=="frame" && i==19) frame_joint_domain_19();
    if(kind=="frame" && i==20) frame_joint_domain_20();
    if(kind=="frame" && i==21) frame_joint_domain_21();
    if(kind=="frame" && i==22) frame_joint_domain_22();
    if(kind=="frame" && i==23) frame_joint_domain_23();
    if(kind=="frame" && i==24) frame_joint_domain_24();
    if(kind=="frame" && i==25) frame_joint_domain_25();
    if(kind=="frame" && i==26) frame_joint_domain_26();
    if(kind=="frame" && i==27) frame_joint_domain_27();
    if(kind=="frame" && i==28) frame_joint_domain_28();
    if(kind=="frame" && i==29) frame_joint_domain_29();
    if(kind=="frame" && i==30) frame_joint_domain_30();
    if(kind=="M" && i==0) M_joint_domain_0();
    if(kind=="M" && i==1) M_joint_domain_1();
    if(kind=="M" && i==2) M_joint_domain_2();
    if(kind=="M" && i==3) M_joint_domain_3();
    if(kind=="M" && i==4) M_joint_domain_4();
}
module tested_tongue_xz() {
    polygon(points = [
        [18.0000, 0.0000], [18.0000, 4.1963], [17.9969, 4.2588], [17.9883, 4.3170], [17.9740, 4.3741],
        [17.9542, 4.4295], [17.9290, 4.4828], [17.8987, 4.5332], [17.8637, 4.5805], [17.8241, 4.6241],
        [17.7805, 4.6637], [17.7332, 4.6987], [17.6828, 4.7290], [17.6295, 4.7542], [17.5741, 4.7740],
        [17.5170, 4.7883], [17.4588, 4.7969], [17.3963, 4.8000], [0.7125, 4.8000], [0.6390, 4.8036],
        [0.5662, 4.8144], [0.4948, 4.8323], [0.4255, 4.8571], [0.3590, 4.8886], [0.2958, 4.9264],
        [0.2367, 4.9702], [0.1822, 5.0197], [0.1327, 5.0742], [0.0889, 5.1333], [0.0511, 5.1965],
        [0.0196, 5.2630], [-0.0052, 5.3323], [-0.0231, 5.4037], [-0.0339, 5.4765], [-0.0375, 5.5500],
        [-0.0375, 6.6000], [-1.0000, 6.6000], [-1.0000, 0.0000]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]
    ], convexity = 30);
}
module tested_socket_void_xz() {
    polygon(points = [
        [20.0000, -0.1000], [20.0000, 0.0000], [18.1500, 0.0000], [18.1500, 4.2000], [18.1464, 4.2735],
        [18.1356, 4.3463], [18.1177, 4.4177], [18.0929, 4.4870], [18.0614, 4.5535], [18.0236, 4.6167],
        [17.9798, 4.6758], [17.9303, 4.7303], [17.8758, 4.7798], [17.8167, 4.8236], [17.7535, 4.8614],
        [17.6870, 4.8929], [17.6177, 4.9177], [17.5463, 4.9356], [17.4735, 4.9464], [17.4000, 4.9500],
        [0.7162, 4.9500], [0.6537, 4.9531], [0.5955, 4.9617], [0.5384, 4.9760], [0.4830, 4.9958],
        [0.4297, 5.0210], [0.3793, 5.0513], [0.3320, 5.0863], [0.2884, 5.1259], [0.2488, 5.1695],
        [0.2138, 5.2168], [0.1835, 5.2672], [0.1583, 5.3205], [0.1385, 5.3759], [0.1242, 5.4330],
        [0.1156, 5.4912], [0.1123, 5.5574], [0.0375, 5.6252], [0.0375, 6.6000], [-1.0000, 6.6000],
        [-1.0000, -0.1000]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
    ], convexity = 30);
}
module tested_key() {
    polygon(points = [
        [15.1500, -1.5000], [15.5743, -1.3243], [15.7500, -0.9000], [15.7500, 0.9000], [15.5743, 1.3243],
        [15.1500, 1.5000], [2.8500, 1.5000], [2.4257, 1.3243], [2.2500, 0.9000], [2.2500, -0.9000],
        [2.4257, -1.3243], [2.8500, -1.5000]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    ], convexity = 30);
}
module tested_key_pocket() {
    polygon(points = [
        [2.8500, -1.6500], [15.1500, -1.6500], [15.2074, -1.6386], [15.6317, -1.4628], [15.7128, -1.3817],
        [15.8886, -0.9574], [15.9000, -0.9000], [15.9000, 0.9000], [15.8886, 0.9574], [15.7128, 1.3817],
        [15.6317, 1.4628], [15.2074, 1.6386], [15.1500, 1.6500], [2.8500, 1.6500], [2.7926, 1.6386],
        [2.3683, 1.4628], [2.2872, 1.3817], [2.1114, 0.9574], [2.1000, 0.9000], [2.1000, -0.9000],
        [2.1114, -0.9574], [2.2872, -1.3817], [2.3683, -1.4628], [2.7926, -1.6386]
    ], paths = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    ], convexity = 30);
}

// DEFAULT-GEOMETRY PREVIEW CACHE. No external mesh files are required.
// Preview tessellations are regenerated after native geometry validation.
module preview_section(kind,i) { section_csg(kind,i); }

original_body_mm("M");
