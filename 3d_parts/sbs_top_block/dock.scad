use <concept.scad>

$fn = 40;
view = "dock";
base_length = 127.76;
base_width = 85.48;
deck_clearance_height = 26;
flare_height = 8;
platform_thickness = 4;
top_length = 145;
top_width = 100;
cradle_clearance = 0.5;
guide_wall = 1.6;
guide_height = 7;
guide_leg = 6;
guide_lead_in = 1;
top_reference_clearance = 2.5;
platform_length = 155;
platform_width = 110;
platform_top = deck_clearance_height + flare_height + platform_thickness;
seat_height = platform_top + top_reference_clearance;
seal_length = 120;
prepeel_length = 5;
peel_start = seal_length / 2 - prepeel_length;
clamp_slot = 0.6;
clamp_length = 80;
clamp_depth = 6;
liner_thickness = 0.0508;
clamp_gap = liner_thickness * 0.7;
clamp_travel = 0.35;
clamp_opening = 0.25;
button_diameter = 10;
button_thickness = 1.7;
button_pocket_depth = button_thickness + clamp_travel + 0.3;
button_center = -5.5;
button_y = clamp_length / 2 + 5;
button_arm_y = clamp_length / 2 - 2;
clamp_flexure = 0.5;
clamp_root_height = 9.5;
clamp_beams = [-28, 0, 28];
liner_width = 78;
top_bar_drop = 0.4;
film_thickness = 0.2;
liner_drop_to_slot = top_reference_clearance - film_thickness - top_bar_drop;
liner_insertion_depth = 2.2;
liner_approach_length = prepeel_length - liner_insertion_depth;
clamp_wall_offset = sqrt(pow(liner_approach_length, 2) - pow(liner_drop_to_slot, 2));
clamp_fixed_wall = peel_start + clamp_wall_offset;
clamp_center = clamp_fixed_wall - clamp_slot;
top_slot_reference = 60.9;
clamp_offset_from_top = top_slot_reference - clamp_fixed_wall;
adhesive_recess_depth = 3;
fixed_jaw_wall = 1.2;
adhesive_recess_start = clamp_fixed_wall + fixed_jaw_wall;
adhesive_recess_length = platform_length / 2 - adhesive_recess_start + 0.1;
adhesive_recess_width = liner_width + 6;
minimum_adhesive_clearance = 1.5;
seal_recess_depth = 0.2;

assert(deck_clearance_height > 0);
assert(top_length / 2 + cradle_clearance + guide_wall < platform_length / 2);
assert(top_width / 2 + cradle_clearance + guide_wall < platform_width / 2);
assert(top_reference_clearance > clamp_travel + 0.4);
assert(guide_height - guide_lead_in >= top_reference_clearance + 3 + 0.5);
assert(guide_leg > 3 + cradle_clearance);
assert(clamp_length / 2 + 0.3 < top_width / 2 - 3);
assert(liner_width < clamp_length);
assert(seal_recess_depth > 0 && seal_recess_depth < 0.5);
assert(seal_length == 120 && peel_start > 54 && peel_start < seal_length / 2);
assert(clamp_gap > 0 && clamp_gap < liner_thickness * 0.9);
assert(liner_insertion_depth > 1.5 && liner_insertion_depth < clamp_depth);
assert(liner_approach_length > liner_drop_to_slot);
assert(clamp_offset_from_top > liner_insertion_depth);
assert(adhesive_recess_start > clamp_fixed_wall && adhesive_recess_start < seal_length / 2);
assert(button_center + button_diameter / 2 < 0);
assert(button_y - button_diameter / 2 > liner_width / 2);
assert(button_y + button_diameter / 2 + 0.3 < top_width / 2 + cradle_clearance);
assert(liner_drop_to_slot - clamp_travel >= minimum_adhesive_clearance);
assert(adhesive_recess_depth > 0 && adhesive_recess_depth < platform_thickness);
assert(platform_top - clamp_root_height - clamp_flexure / 2 > deck_clearance_height);
assert(clamp_center + 1.6 + clamp_flexure / 2 < base_length / 2
    + (platform_length - base_length) / 2
    * (platform_top - clamp_root_height - clamp_flexure / 2 - deck_clearance_height) / flare_height);

module dock_solid(size, position = [0, 0, 0]) {
    translate(position) translate([-size[0] / 2, -size[1] / 2, 0]) cube(size);
}

module pedestal() {
    dock_solid([base_length, base_width, deck_clearance_height + 0.1]);
    hull() {
        dock_solid([base_length, base_width, 0.1], [0, 0, deck_clearance_height]);
        dock_solid([platform_length, platform_width, 0.1], [0, 0, deck_clearance_height + flare_height]);
    }
    dock_solid([platform_length, platform_width, platform_thickness], [0, 0, deck_clearance_height + flare_height]);
}

module corner_guides() {
    inner_length = top_length + 2 * cradle_clearance;
    inner_width = top_width + 2 * cradle_clearance;
    difference() {
        dock_solid([inner_length + 2 * guide_wall, inner_width + 2 * guide_wall, guide_height], [0, 0, platform_top]);
        dock_solid([inner_length, inner_width, guide_height + 1], [0, 0, platform_top - 0.1]);
        hull() {
            dock_solid([inner_length, inner_width, 0.1], [0, 0, platform_top + guide_height - guide_lead_in]);
            dock_solid([inner_length + 2, inner_width + 2, 0.1], [0, 0, platform_top + guide_height]);
        }
        dock_solid([inner_length - 2 * guide_leg, platform_width + 2, guide_height + 2], [0, 0, platform_top - 1]);
        dock_solid([platform_length + 2, inner_width - 2 * guide_leg, guide_height + 2], [0, 0, platform_top - 1]);
    }
}

module liner_clamp_space() {
    dock_solid([clamp_slot, clamp_length + 0.6, liner_insertion_depth + 1], [clamp_slot / 2, 0, -1]);
    dock_solid([2.2, clamp_length + 0.6, 9.8], [-1.1, 0, -1]);
    dock_solid([2.2 + clamp_slot, clamp_length + 0.6, 3], [(clamp_slot - 2.2) / 2, 0, -1]);
    hull()
        for (shift = [0, -clamp_opening])
            translate([button_center + shift, button_y, -1]) cylinder(d = button_diameter + 0.6, h = button_pocket_depth + 1);
    for (shift = [0, -clamp_opening])
        hull() {
            dock_solid([1.6, 6.6, 3], [button_center + shift, button_y, -1]);
            dock_solid([1.2, 4.6, 3], [-0.75 + shift, button_arm_y, -1]);
        }
    for (beam_y = clamp_beams)
        dock_solid([3.6, 5, 3.7], [-0.4, beam_y, 6.5]);
}

module liner_moving_member(pressed = false) {
    rise = pressed ? clamp_travel : 0;
    shift = pressed ? -clamp_opening : 0;
    translate([shift, 0, rise]) {
        dock_solid([0.6, clamp_length, 7.7], [-0.75, 0, 0.5]);
        dock_solid([clamp_slot - clamp_gap + 1.05, clamp_length, 1], [(clamp_slot - clamp_gap - 1.05) / 2, 0, 0.5]);
        translate([button_center, button_y, 0]) cylinder(d = button_diameter, h = button_thickness);
        hull() {
            dock_solid([1, 6, 1], [button_center, button_y, 0.5]);
            dock_solid([0.6, 4, 1], [-0.75, button_arm_y, 0.5]);
        }
    }
}

module liner_clamp(pressed = false) {
    rise = pressed ? clamp_travel : 0;
    shift = pressed ? -clamp_opening : 0;
    liner_moving_member(pressed);
    for (beam_y = clamp_beams)
        hull() {
            dock_solid([clamp_flexure, 4, clamp_flexure], [1.6, beam_y, clamp_root_height - clamp_flexure / 2]);
            dock_solid([clamp_flexure, 4, clamp_flexure], [-0.65 + shift, beam_y, 7.4 + rise]);
        }
}

module clamp_location() {
    translate([clamp_center, 0, platform_top]) rotate([180, 0, 0]) children();
}

module dock_body() {
    difference() {
        union() {
            pedestal();
            corner_guides();
        }
        dock_solid([seal_length, liner_width, seal_recess_depth + 1],
            [0, 0, platform_top - seal_recess_depth]);
        clamp_location() liner_clamp_space();
        dock_solid([adhesive_recess_length, adhesive_recess_width, adhesive_recess_depth + 1],
            [adhesive_recess_start + adhesive_recess_length / 2, 0, platform_top - adhesive_recess_depth]);
    }
}

module dock(pressed = false, colored = true) {
    color(colored ? [0.72, 0.76, 0.78] : [1, 1, 1]) dock_body();
    color(colored ? [0.95, 0.63, 0.16] : [1, 1, 1]) clamp_location() liner_clamp(pressed);
}

module backing() {
    liner_top = seat_height - film_thickness;
    tab_top = liner_top - top_bar_drop;
    tab_outer = clamp_center + clamp_slot;
    left_end = seal_length / 2;
    right_end = peel_start;
    color([0.94, 0.94, 0.88])
        rotate([90, 0, 0]) linear_extrude(height = liner_width, center = true)
            polygon([
                [-left_end, tab_top], [-54, tab_top], [-52, liner_top], [52, liner_top], [54, tab_top], [right_end, tab_top],
                [right_end, tab_top - liner_thickness], [54, tab_top - liner_thickness],
                [52, liner_top - liner_thickness], [-52, liner_top - liner_thickness],
                [-54, tab_top - liner_thickness], [-left_end, tab_top - liner_thickness]
            ]);
    color([0.85, 0.43, 0.20]) {
            hull() {
                dock_solid([liner_thickness, liner_width, liner_thickness], [peel_start - liner_thickness / 2, 0, tab_top - liner_thickness]);
                dock_solid([liner_thickness, liner_width, liner_thickness], [tab_outer - liner_thickness / 2, 0, platform_top - liner_thickness]);
            }
            dock_solid([liner_thickness, liner_width, liner_insertion_depth],
                [tab_outer - liner_thickness / 2, 0, platform_top - liner_insertion_depth]);
        }
}

module dock_label(caption, position, size = 4) {
    color([0.15, 0.19, 0.22]) translate(position) linear_extrude(0.25)
        text(caption, size = size, halign = "center", font = "Liberation Sans:style=Bold");
}

if (view == "part") {
    dock(false, false);
} else if (view == "dock") {
    dock();
    dock_label("RAISED SBS DOCK", [0, -75, 0], 6);
    dock_label(str(deck_clearance_height, " MM NECK / NO SUPPORT PADS / ONE FINGER-RELEASE CLAMP"), [0, -88, 0], 3);
} else if (view == "assembly" || view == "exploded") {
    dock();
    backing();
    translate([0, 0, seat_height + (view == "exploded" ? 35 : 0)]) {
        top_block();
        seal_proxy();
    }
    dock_label(view == "exploded" ? "EXPLODED / NOT A PEEL TRAJECTORY" : "REFERENCE HEIGHT / TOP NOT SUPPORTED", [0, -78, 0], 4.2);
    dock_label("SBS BASE / RAISED CRADLE / DECK FIT UNVERIFIED", [0, -92, 0], 3.2);
} else if (view == "loading") {
    dock();
    backing();
    dock_label("BACKING LOADING / SHALLOW RECESS AND DEPTH STOP", [0, -78, 0], 4);
    dock_label("CENTER LINER / PRESS BUTTON / INSERT TO STOP / RELEASE", [0, -92, 0], 3.2);
} else if (view == "liner_modes") {
    for (mode_index = [0:1]) translate([(mode_index - 0.5) * 180, 0, 0]) {
        dock(mode_index == 1);
        dock_label(mode_index == 0 ? "FLUSH / CLAMPED" : "PRESS DOWN / RELEASE", [0, -75, 0], 4.4);
    }
    dock_label("ONE SLOT / ROUND FINGER BUTTON / OUTBOARD CLEARANCE RECESS", [0, -92, 0], 3.6);
} else if (view == "clamp_section") {
    intersection() {
        union() {
            dock();
            backing();
            translate([0, 0, seat_height]) {
                top_block();
                seal_proxy();
            }
        }
        dock_solid([20, 8, 24], [clamp_center, 0, platform_top - 12]);
    }
    dock_label("OFFSET SLOT / OUTBOARD AIR GAP", [clamp_center, -14, platform_top - 12], 1.4);
} else if (view == "adhesive_clearance") {
    intersection() {
        dock();
        dock_solid([seal_length, liner_width, minimum_adhesive_clearance + film_thickness + top_bar_drop],
            [0, 0, seat_height - film_thickness - top_bar_drop - minimum_adhesive_clearance]);
    }
} else if (view == "assembly_collision") {
    intersection() {
        dock();
        translate([0, 0, seat_height]) top_block();
    }
} else if (view == "liner_collision") {
    intersection() {
        backing();
        translate([0, 0, seat_height]) {
            top_block();
            seal_proxy();
        }
    }
} else if (view == "clamp_collision") {
    intersection() {
        dock_body();
        clamp_location() liner_moving_member(true);
    }
} else {
    assert(false, str("Unknown dock view: ", view));
}