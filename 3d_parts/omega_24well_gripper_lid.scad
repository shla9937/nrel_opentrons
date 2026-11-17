// Omega PS24N-25SWV-16 — ESTIMATED-FIT PETG prototype, not robot-ready.
// One body, two lift-release clips, fixed 88 mm jaw faces; no squeeze action.
// Upper body 112.2 x 74.8, raised features 2.2 out / 17 below rim: estimates.
// Film plane is Z=0, rim Z=-2.4; EVERY default exported surface is at/below Z=0.
// Breathe-Easier overall sheet 152.4 x 82.55; centred trimmed patch 114 x 76.
// Adhesive extent, PETG adhesion and sterile performance remain unverified.
// 24 open splash collars on separate film lands: NOT a liquid-tight seal.
// Grip the FIXED pads and lift; the ledges cam the clips outwards. Push down
// to replace. Retention and extraction are force-dependent and unqualified.
// Nominal unpreloaded clips have 1.15 mm upward play; collars then retain
// 1.85 mm engagement, not a seal. Measure the actual ledges before use.
// Export is upright for inspection. For slicing, rotate 180 degrees about X
// (or select seal_down) so flat film lands face the bed. PETG, 0.4 mm nozzle.
// Check first-layer flatness and root layer bonding; use accessible EXTERNAL
// supports if needed. No enclosed mechanism pockets; keep clip gaps clear.
// Neither unsupported printing nor durability is qualified. Check film,
// fit, grip, extraction and retention physically before robot use.
// 15 mL/well, 37 C, 900 rpm, 48 h performance, 15 N bridge stiffness and
// PETG fatigue/creep are UNVERIFIED. Paddles and global deck clearance unknown.

output = "print"; // print, preview, plate
print_orientation = "upright"; // upright, seal_down
clip_deflection = [0,0]; // preview only: negative-Y / positive-Y tip travel, mm
plate_drop = 0;          // preview: plate moves DOWN as the lid lifts
show_plate = false;
show_film = false;       // virtual film only; never included in the STL
$fn = 32;

body_x = 112.2;
body_y = 74.8;
plate_height = 88.3;
rim_z = -2.4;
pitch = 18.7;
well_opening = 17.2;
well_corner = 0.8; // estimate; check the real corner radii
feature_width = 55.4;
feature_projection = 2.2;
feature_top_depth = 7;
feature_bottom_depth = 17;
feature_centre_width = 22.4;
feature_notch_width = 7.8;
feature_notch_depth = 3; // conservative photo estimate
socket_clearance = 0.5;
socket_wall = 1.6;
socket_depth = 2.6;
collar_outer = 16;
passage = 14.4;
collar_depth = 3;
collar_tip_chamfer = 0.6;
collar_tip_reduction = 0.6;
film_x = 114;
film_y = 76;
clip_width = 10;
clip_thickness = 1.2;
clip_inner_y = 40.2;
root_end_z = -5.8;
root_radius = 1;
hook_vertical_gap = 1.15; // actual upward play at the feature's OUTER edge
hook_overlap = 1;
hook_nose_height = 0.6;
hook_root_height = 3.2;
max_deflection = 1.4;    // geometric preview envelope, NOT a force prediction
jaw_y = 44;
pad_width = 40;
pad_depth = 5.8;
bridge_depth = 4.8;
pad_inner_y = 42.4;

frame_x = body_x + 2 * (socket_clearance + socket_wall);
frame_y = body_y + 2 * (socket_clearance + socket_wall);
feature_y = body_y/2 + feature_projection;
ledge_z = rim_z - feature_bottom_depth;
hook_root_z = ledge_z - hook_vertical_gap + clip_inner_y - feature_y;
hook_tip_y = feature_y - hook_overlap;
hook_nose_z = hook_root_z - (clip_inner_y-hook_tip_y);
clip_centre_y = clip_inner_y + clip_thickness/2;
free_length = root_end_z - hook_root_z;

// End-loaded cantilever shape with second-order axial shortening; NOT FEA.
function bend_y(t,d) = d*t*t*(3-t)/2;
function bend_slope(t,d) = d/free_length*(3*t-1.5*t*t);
function bend_z(t,d) = root_end_z-free_length*t
    + d*d/(2*free_length)*(3*t*t*t-2.25*pow(t,4)+0.45*pow(t,5));
function bend_angle(t,d) = atan(bend_slope(t,d)/(1-pow(bend_slope(t,d),2)/2));
function leaf_edge(t,d,edge) =
    [clip_centre_y+bend_y(t,d)+edge*clip_thickness/2*cos(bend_angle(t,d)),
     bend_z(t,d)+edge*clip_thickness/2*sin(bend_angle(t,d))];
function hook_point(p,d) =
    let(a=bend_angle(1,d), y=p[0]-clip_centre_y, z=p[1]-hook_root_z)
    [clip_centre_y+d+y*cos(a)-z*sin(a),
     bend_z(1,d)+y*sin(a)+z*cos(a)];
function hook_profile() = [
    [clip_inner_y,hook_root_z],
    [hook_tip_y,hook_nose_z],
    [hook_tip_y,hook_nose_z-hook_nose_height],
    [clip_inner_y,hook_root_z-hook_root_height],
    [clip_inner_y+clip_thickness,hook_root_z-hook_root_height],
    [clip_inner_y+clip_thickness,hook_root_z]];

module box(x0,x1,y0,y1,z0,z1) {
    translate([x0,y0,z0]) cube([x1-x0,y1-y0,z1-z0]);
}
module yz_prism(x0,x1,points) {
    multmatrix([[0,0,1,x0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
        linear_extrude(x1-x0) polygon(points);
}
module round_square(size,r) {
    offset(r=r) square([size-2*r,size-2*r],center=true);
}
module wells() {
    for (x=[-2.5:1:2.5], y=[-1.5:1:1.5])
        translate([x*pitch,y*pitch,0]) children();
}
module sides() {
    for(s=[-1,1]) scale([1,s,1]) children();
}

module platform() {
    difference() {
        union() {
            box(-frame_x/2,frame_x/2,-frame_y/2,frame_y/2,rim_z,0);
            difference() {
                box(-frame_x/2,frame_x/2,-frame_y/2,frame_y/2,
                    rim_z-socket_depth,rim_z+0.01);
                box(-body_x/2-socket_clearance,body_x/2+socket_clearance,
                    -body_y/2-socket_clearance,body_y/2+socket_clearance,
                    rim_z-socket_depth-0.01,rim_z+0.02);
            }
            wells() {
                translate([0,0,rim_z-collar_depth+collar_tip_chamfer])
                    linear_extrude(collar_depth-collar_tip_chamfer+0.01)
                        round_square(collar_outer,0.8);
                hull() {
                    translate([0,0,rim_z-collar_depth])
                        linear_extrude(0.01)
                            round_square(collar_outer-collar_tip_reduction,0.8);
                    translate([0,0,rim_z-collar_depth+collar_tip_chamfer])
                        linear_extrude(0.01) round_square(collar_outer,0.8);
                }
            }
        }
        wells() box(-passage/2,passage/2,-passage/2,passage/2,
                    rim_z-collar_depth-0.1,0.1);
    }
}

module fixed_side() {
    box(-pad_width/2,pad_width/2,film_y/2,jaw_y,-bridge_depth,0);
    box(-pad_width/2,pad_width/2,pad_inner_y,jaw_y,-pad_depth,0);
    // Both 1 mm root fillets end at -5.8: the 14.15 mm leaf starts HERE.
    yz_prism(-clip_width/2,clip_width/2,concat(
        [[clip_inner_y-root_radius,-bridge_depth+0.01]],
        [for(a=[90:-5:0])
            [clip_inner_y-root_radius+root_radius*cos(a),
             root_end_z+root_radius*sin(a)]],
        [for(a=[0:5:90])
            [clip_inner_y+clip_thickness+root_radius-root_radius*cos(a),
             root_end_z+root_radius*sin(a)]],
        [[clip_inner_y+clip_thickness+root_radius,-bridge_depth+0.01]]));
}
module fixed() {
    union() {
        platform();
        sides() fixed_side();
    }
}
module leaf_side(d=0) {
    yz_prism(-clip_width/2,clip_width/2,concat(
        [for(i=[0:32]) leaf_edge(i/32,d,-1)],
        [for(i=[32:-1:0]) leaf_edge(i/32,d,1)]));
}
module hook_side(d=0) {
    yz_prism(-clip_width/2,clip_width/2,
        [for(p=hook_profile()) hook_point(p,d)]);
}
module clip_side(d=0) {
    union() { leaf_side(d); hook_side(d); }
}
module lid(deflections=[0,0]) {
    union() {
        fixed();
        for(i=[0:1]) scale([1,i==0 ? -1 : 1,1])
            clip_side(deflections[i]);
    }
}
module film_patch() {
    box(-film_x/2,film_x/2,-film_y/2,film_y/2,0.01,0.16);
}
module feature_side() {
    // Both end feet and central underside included; notch depths are estimated.
    difference() {
        box(-feature_width/2,feature_width/2,body_y/2,feature_y,
            rim_z-feature_bottom_depth,rim_z-feature_top_depth);
        for(s=[-1,1]) scale([s,1,1])
            box(feature_centre_width/2,
                feature_centre_width/2+feature_notch_width,
                body_y/2-0.01,feature_y+0.01,
                rim_z-feature_bottom_depth-0.01,
                rim_z-feature_bottom_depth+feature_notch_depth);
    }
}
module nominal_plate() {
    difference() {
        union() {
            box(-body_x/2,body_x/2,-body_y/2,body_y/2,
                rim_z-plate_height,rim_z);
            box(-127.4/2,127.4/2,-85/2,85/2,
                rim_z-plate_height,rim_z-plate_height+3);
            sides() feature_side();
        }
        wells() translate([0,0,rim_z-plate_height+3])
            linear_extrude(plate_height)
                round_square(well_opening,well_corner);
    }
}

assert(free_length >= 14, "Free leaf length excludes the root fillets");
assert(clip_width < feature_centre_width && hook_overlap > 0);
assert(hook_root_height > clip_inner_y-hook_tip_y+hook_nose_height);
assert(pad_depth <= -root_end_z && bridge_depth+root_radius == -root_end_z);
assert(jaw_y*2 < 90 && pad_inner_y > clip_inner_y+clip_thickness);
assert(hook_vertical_gap > 0 && film_y/2 < frame_y/2);
assert(min(clip_deflection) >= 0 && max(clip_deflection) <= max_deflection);
assert(output != "print" || clip_deflection == [0,0],
       "Export only the unloaded part");
assert(print_orientation == "upright" || print_orientation == "seal_down");
if(output=="print") {
    if(print_orientation=="seal_down") rotate([180,0,0]) lid();
    else lid();
}
else if(output=="preview") {
    color("LightSteelBlue") fixed();
    color("DarkOrange")
        for(i=[0:1]) scale([1,i==0 ? -1 : 1,1]) clip_side(clip_deflection[i]);
    if(show_plate) color([0.6,0.65,0.7,0.25])
        translate([0,0,-plate_drop]) nominal_plate();
    if(show_film) color([0.5,0.8,1,0.3]) film_patch();
}
else if(output=="plate") nominal_plate();
