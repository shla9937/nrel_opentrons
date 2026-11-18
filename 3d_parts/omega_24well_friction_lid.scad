// Omega 24-well friction lid — provisional fit prototype, NOT robot-qualified.
// Assembly: centred XY grid; plate rim/seating plane Z=0, film face Z=2.4.
// Print: rotate 180 degrees about X, then raise film face to bed Z=0.
// No clips, tabs, grip pads or film membrane are modelled.
print_orientation = true; // false: assembly coordinates for inspection
$fn = 96;

body_x = 111.2;
body_y = 74.8;
pitch = 18.0; // provisional: 89.8 / 5 = 17.96; centred grid is unmeasured
well_opening = 17;
roof_thickness = 2.4;
collar_clearance = 0.6;
collar_depth = 5;
collar_lead = 0.8;
collar_tip_inset = 0.4;
passage = 13.8;
passage_radius = 2.4; // retains >1.2 mm wall at relieved collar corners
post_radius = 1.75;
post_clearance = 0.3;
skirt_clearance = 1;
skirt_wall = 1.6;
skirt_depth = 4;
skirt_lead = 0.6;
retention_interference = 0.05; // per side, geometric only; no force prediction
retention_depth = 2.3; // centre below rim; ribs have 2.6 mm total axial length
retaining_wells = [[1,1],[4,1],[1,2],[4,2]]; // zero-based column,row

collar_outer = well_opening - 2*collar_clearance;
frame_x = body_x + 2*(skirt_clearance+skirt_wall);
frame_y = body_y + 2*(skirt_clearance+skirt_wall);
epsilon = 0.01;

function well_x(c) = (c-2.5)*pitch;
function well_y(r) = (r-1.5)*pitch;
function retaining(c,r) = len([for(w=retaining_wells)
    if(w==[c,r]) 1]) > 0;

module rounded_rectangle(x,y,r) {
    offset(r=r) square([x-2*r,y-2*r],center=true);
}
module well_positions() {
    for(c=[0:5],r=[0:3]) translate([well_x(c),well_y(r),0]) children();
}
module post_reliefs(height) {
    for(x=[-1,1],y=[-1,1])
        translate([x*well_opening/2,y*well_opening/2,-collar_depth-epsilon])
            // Circumscribed polygon never cuts inside the specified clearance.
            cylinder(h=height,r=(post_radius+post_clearance)/cos(180/$fn));
}
module collar_blank() {
    difference() {
        union() {
            translate([0,0,-collar_depth+collar_lead])
                linear_extrude(collar_depth-collar_lead+epsilon)
                    square([collar_outer,collar_outer],center=true);
            hull() {
                translate([0,0,-collar_depth])
                    linear_extrude(epsilon)
                        square([collar_outer-2*collar_tip_inset,
                                collar_outer-2*collar_tip_inset],center=true);
                translate([0,0,-collar_depth+collar_lead])
                    linear_extrude(epsilon)
                        square([collar_outer,collar_outer],center=true);
            }
        }
        post_reliefs(collar_depth+2*epsilon);
    }
}
module retention_rib() {
    // Both axial ends ramp gently into the wall; only the outer flat is proud.
    hull() for(level=[-1.3,-0.5,0.5,1.3]) {
        extent = abs(level)>1 ? collar_outer/2
            : well_opening/2+retention_interference;
        translate([extent-0.5,0,-retention_depth+level])
            linear_extrude(epsilon) rounded_rectangle(1,2,0.4);
    }
}
module skirt() {
    difference() {
        translate([-frame_x/2,-frame_y/2,-skirt_depth])
            cube([frame_x,frame_y,skirt_depth+epsilon]);
        translate([0,0,-skirt_depth-epsilon])
            linear_extrude(skirt_depth+3*epsilon)
                square([body_x+2*skirt_clearance,
                        body_y+2*skirt_clearance],center=true);
        hull() {
            translate([0,0,-skirt_depth-epsilon])
                linear_extrude(epsilon)
                    square([body_x+2*(skirt_clearance+skirt_lead),
                            body_y+2*(skirt_clearance+skirt_lead)],center=true);
            translate([0,0,-skirt_depth+skirt_lead])
                linear_extrude(epsilon)
                    square([body_x+2*skirt_clearance,
                            body_y+2*skirt_clearance],center=true);
        }
    }
}
module lid() {
    difference() {
        union() {
            translate([-frame_x/2,-frame_y/2,0])
                cube([frame_x,frame_y,roof_thickness]);
            skirt();
            for(c=[0:5],r=[0:3]) translate([well_x(c),well_y(r),0]) {
                collar_blank();
                if(retaining(c,r))
                    for(side=[-1,1]) scale([side,1,1])
                        retention_rib();
            }
        }
        well_positions() translate([0,0,-collar_depth-epsilon])
            linear_extrude(collar_depth+roof_thickness+2*epsilon)
                rounded_rectangle(passage,passage,passage_radius);
    }
}
assert(collar_depth>collar_lead && skirt_depth>skirt_lead);
assert(passage<collar_outer-2*collar_tip_inset);
assert(passage_radius>0 && 2*passage_radius<passage);
assert(skirt_wall>skirt_lead && skirt_clearance>0);
assert(retention_interference>=0 && retention_interference<=0.2,
       "Prototype rib adjustment limited to 0..0.2 mm per side");
assert(retention_depth>1.3+epsilon &&
       retention_depth+1.3<collar_depth-collar_lead);
assert(5*pitch+well_opening<body_x && 3*pitch+well_opening<body_y);

if(print_orientation)
    translate([0,0,roof_thickness]) rotate([180,0,0]) lid();
else lid();
