/*
 * NLR / Robotic Biology — alpine manipulator, v3
 * Self-contained volumetric adaptation, NOT brand-approved artwork.
 * Front = -Y; millimetres; underside Z=0. See README.md for build limitations.
 * Material regions share boundaries, never positive-volume overlaps.
 * Registered exports retain the same origin. Colours are NOT AMS assignments.
 */

/* [Output] */
view_mode = "assembly"; // [assembly, solid]
part = "all"; // [all, navy, blue, gold, white]
inspection = "none"; // [none, centre_section]

/* [Mountain depth] */
mountain_half_taper = 0.13; // Y change per mm of X, either side of vertical ridge.

/* [Resolution] */
$fn = 64;

/* [Hidden] */
base_x = 127.4;
base_y = 85;
base_h = 22;
corner_r = 5;
chamfer = 1;
snow_depth = 0.8; // Along Y; follows both shared front planes.
text_depth = 1;
arm_y = -12;
arm_depth = 12;
sun_r = 9;
sun_z = 77;
sun_depth = 8;
materials = ["navy", "blue", "gold", "white"];
palette = ["#003a69", "#0079C2", "#db9728", "#f2f4f5"];

// Official source artwork coordinates: screen Y is down.
// Tiny original curves are simplified; both coloured outlines stay unchanged.
// A full-depth WHITE valley fills the entire separation down to the base.
navy_outline = [[1,68.5],[40.7,68.5],[41.6,64.3],[53,47.1],
    [57.2,44.3],[63.6,42.6],[72.8,32.5],[76,29.6],[79,29.3],
    [59,1],[53,12.4],[47.4,14.3],[41.9,23.4],[40,24],[33.1,19.8]];
snow_upper = [[45.7,28],[50.5,19.9],[54.5,18.1],[56.9,16.8],
    [58.6,14.4],[59.4,12.5],[60.9,12.3],[68.3,22.6],[67.9,23.9],
    [65.6,24],[51.2,28.9],[48.7,29.3],[46.5,29.2]];
snow_lower = [[18.8,51.1],[33.9,28.4],[35.1,28.1],[42.1,32.5],
    [44.1,32.4],[44.8,33.9],[41.2,37.8],[35.9,38.6],[20.5,52.1]];
mesa_outline = [[48.7,68.5],[114.7,68.5],[102.4,35.1],
    [78.9,35.1],[67.4,47.2],[58.5,49.9],[48.7,64.4]];

valley_left = [for (i=[1:8]) navy_outline[i]];
// Continue the summit-to-tip diagonal down to the unchanged mesa top.
valley_cap_x = 79 + (35.1-29.3)*(79-59)/(29.3-1);
valley_right = [[48.7,68.5],[48.7,64.4],[58.5,49.9],
    [67.4,47.2],[78.9,35.1],[valley_cap_x,35.1],[79,29.3]];
valley_outline = concat(valley_left,
    [for (i=[len(valley_right)-2:-1:0]) valley_right[i]]);

function logo_xz(p) = [-56 + 0.90*p[0], base_h + 0.90*(68.5-p[1])];
// Vertical YZ plane through the angled white cap's junction with the mesa.
ridge_x = logo_xz([valley_cap_x,35.1])[0];
function signed_area2(points, i=0) = i==len(points) ? 0 :
    points[i][0]*points[(i+1)%len(points)][1] -
    points[(i+1)%len(points)][0]*points[i][1] + signed_area2(points,i+1);

module rounded_rectangle(w, d, r) {
    hull()
        for (x = [-w/2+r, w/2-r], y = [-d/2+r, d/2-r])
            translate([x,y]) circle(r=r);
}

// Exact XZ profile with a constant Y depth, front at yc-depth/2.
module upright(depth, yc=0) {
    translate([0,yc+depth/2,0]) rotate([90,0,0])
        linear_extrude(height=depth, convexity=12) children();
}

// Short bevels on front/back edges; no spheres or hidden spherical joints.
module bevelled_upright(depth, yc, bevel=0.65) {
    hull() {
        upright(depth-2*bevel, yc) children();
        upright(depth, yc) offset(delta=-bevel) children();
    }
}

module base_blank() {
    // Same outer radius/size at Z=1 and 21; one millimetre 45-degree chamfers.
    hull() {
        linear_extrude(height=base_h)
            rounded_rectangle(base_x-2*chamfer, base_y-2*chamfer, corner_r-chamfer);
        translate([0,0,chamfer]) linear_extrude(height=base_h-2*chamfer)
            rounded_rectangle(base_x, base_y, corner_r);
    }
}

module label_inlays() {
    // Start INSIDE the face and extrude towards -Y: front exactly Y=-42.5.
    // Letter counters stay navy and connect to the full base behind the inlay.
    translate([0,-base_y/2+text_depth,15.3]) rotate([90,0,0])
        linear_extrude(height=text_depth)
            text("NLR", size=10.5, font="Liberation Sans:style=Bold",
                 halign="center", valign="center", spacing=1.08);
    translate([0,-base_y/2+text_depth,6.4]) rotate([90,0,0])
        linear_extrude(height=text_depth)
            text("Robotic Biology", size=5, font="Liberation Sans:style=Bold",
                 halign="center", valign="center");
}

// Finite halfspaces, generously enclosing the actual model. Shear leaves XZ
// unchanged, preserving the true front logo silhouette instead of making cones.
module front_halfspace() {
    // Y >= -3+mountain_half_taper*abs(X-ridge_x); no Z slope.
    intersection() {
        intersection_for (slope=[-mountain_half_taper,mountain_half_taper])
            multmatrix([[1,0,0,0],[slope,1,0,-3-slope*ridge_x],
                        [0,0,1,0],[0,0,0,1]])
                translate([-150,0,-10]) cube([300,200,150]);
    }
}

module rock_envelope() {
    // ONE continuous double wedge shared by navy, valley, blue and snow.
    // Maximum depth 28 on vertical YZ plane X=18.7890459364, centred at Y=11.
    // Tapers LEFT and RIGHT only; constant depth along Z, no horizontal ridge.
    // Front Y=-3+0.13*abs(X-ridge_x); back Y=25-0.13*abs(X-ridge_x).
    intersection() {
        front_halfspace();
        intersection_for (slope=[-mountain_half_taper,mountain_half_taper])
            multmatrix([[1,0,0,0],[slope,1,0,25-slope*ridge_x],
                        [0,0,1,0],[0,0,0,1]])
                translate([-150,-200,-10]) cube([300,200,150]);
    }
}

module logo_prism(points) {
    upright(100) polygon([for (p=points) logo_xz(p)]);
}

module rock_prism(points) {
    // Keep XZ coordinates in the same double-precision representation as the
    // other structural colour regions; do not quantise one through a 2D grid.
    n=len(points);
    // Valley and rock outlines traverse opposite directions in artwork space.
    // Normalise winding so EVERY prism is an outward-oriented positive solid.
    ordered=signed_area2(points)>0 ? [for (i=[n-1:-1:0]) points[i]] : points;
    vertices=[for (y=[-50,50], p=ordered) let(q=logo_xz(p)) [q[0],y,q[1]]];
    polyhedron(points=vertices,faces=concat(
        [[for (i=[n-1:-1:0]) i],[for (i=[0:n-1]) n+i]],
        [for (i=[0:n-1]) [i,(i+1)%n,n+(i+1)%n,n+i]]),convexity=12);
}

module mountain_original() {
    intersection() {
        rock_prism(navy_outline);
        rock_envelope();
    }
}

module mountain_valley_fill() {
    intersection() {
        rock_prism(valley_outline);
        rock_envelope();
    }
}

module snow_pockets() {
    // Cut from well in FRONT of the rock to the inlay back plane. Reusing an
    // already-clipped shell as the cutter leaves numerical coplanar flakes.
    intersection() {
        union() {
            logo_prism(snow_upper);
            logo_prism(snow_lower);
        }
        difference() {
            translate([-100,-60,0]) cube([200,120,100]);
            translate([0,snow_depth,0]) front_halfspace();
        }
    }
}

module snow_inlays() {
    intersection() { mountain_original(); snow_pockets(); }
}

module mesa() {
    intersection() {
        rock_prism(mesa_outline);
        rock_envelope();
    }
}

module link_profile(a, b, ra, rb) {
    hull() {
        translate(a) circle(r=ra);
        translate(b) circle(r=rb);
    }
}

module sun() {
    // Upright circular disk, never a diamond; 0.4 mm perimeter bevel.
    bevelled_upright(sun_depth, arm_y, 0.4)
        translate([30,sun_z]) circle(r=sun_r);
}

module cup_blank() {
    // Full-depth structural cradle supports the gold lower arc before Z=70.64,
    // where the circle's layerwise outward slope falls below 1:1.
    // Subtracting the identical disk gives a matched interface, not overlap.
    upright(sun_depth, arm_y)
        polygon([[26,62.5],[34,62.5],[41,70.5],[41,73.5],[39,75],
                 [37.8,75],[37.8,72],[22.2,72],[22.2,75],[21,75],
                 [19,73.5],[19,70.5]]);
}

module arm_blank() {
    union() {
        translate([43,arm_y,base_h]) cylinder(d=16,h=1.6);
        translate([43,arm_y,23.6]) cylinder(d1=16,d2=13,h=3);
        translate([43,arm_y,26.6]) cylinder(d1=13,d2=11,h=3.4);
        bevelled_upright(arm_depth,arm_y)
            link_profile([43,30],[50,44],6.3,6.1);
        bevelled_upright(arm_depth,arm_y)
            link_profile([50,44],[30,64],5.7,4.8);
        cup_blank();
    }
}

module arm_region() {
    // Entire mechanical volume, including the pedestal foot, is white.
    difference() {
        arm_blank();
        sun();
    }
}

module material_region(material) {
    if (material=="navy") difference() {
        // Preserve the original coloured mountain outline.
        union() { base_blank(); mountain_original(); }
        snow_pockets();
        label_inlays();
    }
    if (material=="blue") mesa();
    if (material=="gold") sun();
    if (material=="white") union() {
        mountain_valley_fill();
        snow_inlays();
        label_inlays();
        arm_region();
    }
}

module complete_solid() {
    // Filling every inlay with the parent solid is exactly the union of all
    // four regions, without the unnecessary internal surfaces/colour booleans.
    union() {
        base_blank(); mountain_original(); mountain_valley_fill();
        mesa(); arm_blank(); sun();
    }
}

module selected_output() {
    if (part!="all") material_region(part);
    else if (view_mode=="solid") complete_solid();
    else for (i=[0:len(materials)-1])
        // Evaluate each partition before OpenCSG preview: nested coincident
        // inlay cutters otherwise display false colours and missing snow.
        color(palette[i]) render(convexity=16) material_region(materials[i]);
}

assert(view_mode=="assembly" || view_mode=="solid", "Unknown view_mode");
assert(part=="all" || len([for (m=materials) if (m==part) m])==1,
       "Unknown material selector");
assert(inspection=="none" || inspection=="centre_section", "Unknown inspection mode");

if (inspection=="centre_section") intersection() {
    selected_output();
    translate([-80,-60,-1]) cube([160,60,100]);
} else selected_output();