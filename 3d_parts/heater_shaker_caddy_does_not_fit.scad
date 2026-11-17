// Experimental, UNPOWERED FIT ONLY. Dimensions in millimetres.
use <../flex_heater_shaker_caddy.scad>

$fn = 96;
part = "printassembly"; // printassembly, coupon, body, lever, hinge_preview, section_preview
travel_limit = 12;
print_angle = travel_limit / 2;
side_gap = 0.6;
radial_gap = 0.6;
lever_width = 6;
ear_width = 4;
axle_radius = 2;
boss_radius = 5;
pivot = [-60, 26, 53.825];
ear_inner = lever_width / 2 + side_gap;
ear_outer = ear_inner + ear_width;
top_z = 59.325;
pip_floor_z = 6;
pip_rail_height = 3;
pip_rail_top_width = 3;
pip_rail_foot_width = 6;
pip_corner_cutback = 5; // Visual estimate, not a measured OEM dimension.
pip_pocket_x = [-30.32, 101.32];
pip_pocket_y = [-44, 44];
pip_rail_overlap = 0.05;

assert(side_gap >= 0.6 && side_gap <= 0.8, "Side gap must be 0.6–0.8 mm");
assert(radial_gap >= 0.6 && radial_gap <= 0.8, "Radial gap must be 0.6–0.8 mm");
assert(travel_limit == 12, "This actuator is verified for 12 degree travel only");
assert(print_angle > travel_limit / 2 - 1 && print_angle < travel_limit / 2 + 1,
       "Print near mid-travel, never on the stops");
assert(part == "printassembly" || part == "coupon" || part == "body" ||
       part == "lever" || part == "hinge_preview" || part == "support_preview" ||
       part == "section_preview");
assert(pip_rail_height > 0 && pip_rail_top_width >= 3 &&
       pip_rail_foot_width >= pip_rail_top_width && pip_rail_foot_width < 6.5,
       "Rails need a supported foot and at least 3 mm top thickness");
assert(pip_corner_cutback > 0 &&
       2 * pip_corner_cutback < min(pip_pocket_x[1] - pip_pocket_x[0],
                                   pip_pocket_y[1] - pip_pocket_y[0]),
       "Corner cutbacks must leave four separate, positive-length rails");
assert(pip_rail_overlap > 0 && pip_rail_overlap < pip_floor_z);

module pivot_pose(angle = 0) {
    translate(pivot) rotate([0, -angle, 0]) children();
}

module local_extrude(half_width) {
    along_y(-half_width, half_width) children();
}

module fixed_axle(extra = 0) {
    translate(pivot)
        local_extrude(ear_inner + extra)
            rotate(22.5) circle(r = axle_radius, $fn = 8);
}

module ears() {
    for (side = [-1, 1])
        block(-80, -54,
              pivot[1] + (side < 0 ? -ear_outer : ear_inner),
              pivot[1] + (side < 0 ? -ear_inner : ear_outer),
              46.5, top_z);
}

module stops() {
    pivot_pose()
        block(-19, -15, -ear_inner - 0.05, ear_inner + 0.05, 1.5, 3);
    intersection() {
        pivot_pose(travel_limit)
            local_extrude(ear_inner + 0.05)
                polygon([[-19, -0.5], [-17, -2.5], [-17, -5], [-19, -3]]);
        block(-85, -70, 18, 34, 46.5, top_z);
    }
}

module fixed_hinge() {
    ears();
    fixed_axle(0.1);
    stops();
}

module reinforced_rail(length) {
    // Keep the taper exact above the floor; the buried foot only joins the floor.
    along_y(0, length)
        polygon([[0, pip_floor_z - pip_rail_overlap],
                 [pip_rail_foot_width, pip_floor_z - pip_rail_overlap],
                 [pip_rail_foot_width, pip_floor_z],
                 [pip_rail_top_width, pip_floor_z + pip_rail_height],
                 [0, pip_floor_z + pip_rail_height]]);
}

module reinforced_rails() {
    x0 = pip_pocket_x[0] + pip_corner_cutback;
    x1 = pip_pocket_x[1] - pip_corner_cutback;
    y0 = pip_pocket_y[0] + pip_corner_cutback;
    y1 = pip_pocket_y[1] - pip_corner_cutback;
    translate([x0, pip_pocket_y[0], 0])
        rotate([0, 0, -90]) reinforced_rail(x1 - x0);
    translate([x1, pip_pocket_y[1], 0])
        rotate([0, 0, 90]) reinforced_rail(x1 - x0);
    translate([pip_pocket_x[0], y0, 0])
        mirror([1, 0, 0]) reinforced_rail(y1 - y0);
    translate([pip_pocket_x[1], y0, 0])
        reinforced_rail(y1 - y0);
}

module body() {
    // Reuse the OEM-style members, not the old screw pockets or slotted ears.
    rounded_plate(-57.5, 114, 101, 4.5, 0, 6);
    posts();
    reinforced_rails();
    handle();
    difference() {
        flange();
        block(-81, -48.45, pivot[1] - ear_inner, pivot[1] + ear_inner, 6, 70);
    }
    fixed_hinge();
}

module contact_tip() {
    translate([-53, 26, 36.31]) rotate([0, 90, 0])
        cylinder(d = 3, h = 5.5);
}

module lever_rest(with_tip = true) {
    difference() {
        union() {
            along_y(pivot[1] - lever_width / 2, pivot[1] + lever_width / 2)
                difference() {
                    lever_profile();
                    translate([pivot[0] - 18.05, pivot[2] + 6.175])
                        square([14.1, 4]);
                    translate([-51.75, 34]) square([5, 9]);
                }
            block(-60, -51.75, pivot[1] - lever_width / 2,
                  pivot[1] + lever_width / 2, 34.81, 35.2);
            cylinder_y(pivot[0], pivot[1] - lever_width / 2,
                       pivot[1] + lever_width / 2, pivot[2], boss_radius * 2);
            pivot_pose() local_extrude(lever_width / 2) {
                // Rising undersides prevent new islands above the supported nose.
                polygon([[-18, 1.5], [-2, 1.5], [-2, -17.5], [-18, -1.5]]);
                polygon([[-18, 10.175], [-4, 10.175], [-4, 9.175],
                         [-8, 5.175], [-12.5, 5.175], [-16.5, 9.175]]);
            }
            if (with_tip) contact_tip();
        }
        cylinder_y(pivot[0], pivot[1] - lever_width, pivot[1] + lever_width,
                   pivot[2], 2 * (axle_radius + radial_gap));
    }
}

module lever_at(angle = print_angle) {
    pivot_pose(angle) translate(-pivot) lever_rest();
}

module assembly(angle = print_angle) {
    color([0.72, 0.75, 0.78]) body();
    color([0.95, 0.42, 0.08]) lever_at(angle);
}

module coupon_body_world() {
    intersection() {
        body();
        block(-84, -45, 15, 37, 34, 70);
    }
    block(-84, -45, 15, 37, 32, 34);
    for (y = [15, 33])
        block(-84, -81, y, y + 4, 33.95, top_z);
}

module coupon_world(angle = print_angle) {
    color([0.72, 0.75, 0.78]) coupon_body_world();
    color([0.95, 0.42, 0.08]) lever_at(angle);
}

module coupon(angle = print_angle) {
    // A rigid translation only: retain the entire lever and its support access.
    translate([64, -26, -32]) coupon_world(angle);
}

module no_support_zones() {
    cylinder_y(-60, 21.9, 30.1, 53.825, 6.4);
    block(-80, -74, 22, 30, 46.4, 57.5);
    for (y = [22.2, 28.8])
        block(-81, -48.45, y, y + 1, 46, 65);
}

if (part == "printassembly") assembly(print_angle);
if (part == "body") body();
if (part == "lever") lever_at(print_angle);
if (part == "coupon") coupon(print_angle);
if (part == "hinge_preview") coupon_world(print_angle);
module section_at(angle = print_angle) {
    color([0.72, 0.75, 0.78])
        intersection() { coupon_body_world(); block(-85, -44, 25.8, 26.2, 31, 70); }
    color([0.95, 0.42, 0.08])
        intersection() { lever_at(angle); block(-85, -44, 25.8, 26.2, 31, 70); }
}
if (part == "section_preview") section_at(print_angle);
if (part == "support_preview") {
    coupon_world(print_angle);
    %color([0.95, 0.05, 0.1, 0.5]) no_support_zones();
}
