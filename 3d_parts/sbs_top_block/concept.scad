$fn = 40;

view = "underside";
block_length = 145;
block_width = 100;
block_thickness = 40;
edge_radius = 3;
edge_press_angle = 25;
sticky_length = 120;
slit_inset_from_sticky = 0.25;
slit_width = 0.65;
tab_thickness = 0.2;
closed_gap = 0.15;
button_travel = 0.4;
jaw_opening = 0.3;
bar_width = 6;
bar_length = block_width;
bar_height = edge_radius + button_travel + 1;
flexure_thickness = 0.5;
beam_positions = [-30, 0, 30];
plate_length = 127.76;
plate_width = 85.48;
seal_width = 78;
seal_tab_length = 8.5;
seal_recess_depth = 0.2;

slit_inner = sticky_length / 2 + slit_inset_from_sticky;
slit_outer = slit_inner + slit_width;
tab_approach = slit_outer - tab_thickness - sticky_length / 2;
slit_depth = seal_tab_length - tab_approach - button_travel - tab_thickness;
bar_center = slit_inner - bar_width / 2 - 0.25;
stem_inner = slit_inner - 1.1;
stem_outer = slit_inner - 0.3;
relief_inner = stem_inner - 1.4;
flexure_root = slit_outer + 1.65;
flexure_top = slit_depth + 7;

body_tint = [0.12, 0.53, 0.48];
bar_tint = [0.94, 0.64, 0.18];
ink = [0.15, 0.19, 0.22];

assert(block_length / 2 > flexure_root + 2, "Keep solid material outside the flexure root");
assert(sticky_length == 120, "Measure seal and reposition the mechanism before changing the assumed sticky length");
assert(slit_depth > 6 && flexure_top + 2 < block_thickness);
assert(stem_outer < slit_inner);
assert(closed_gap > 0 && closed_gap < tab_thickness);
assert(bar_center + bar_width / 2 < slit_inner, "Release bars must stay inboard of their slits");
assert(bar_center - bar_width / 2 - jaw_opening > 0);
assert(bar_length == block_width, "Release bars must span the full block width");
assert(stem_inner - jaw_opening > relief_inner);
assert(edge_radius > 0 && 2 * edge_radius < min(block_length, block_width, block_thickness));
assert(block_length / 2 - edge_radius > flexure_root + flexure_thickness / 2);
assert(block_width / 2 - edge_radius > max(beam_positions) + 3.5);
assert(seal_recess_depth > 0 && seal_recess_depth <= tab_thickness);
assert(tab_approach > 0 && slit_depth < seal_tab_length);

module solid(size, position = [0, 0, 0]) {
    translate(position) translate([-size[0] / 2, -size[1] / 2, 0]) cube(size);
}

module label(caption, position, size = 4) {
    color(ink) translate(position) linear_extrude(0.25)
        text(caption, size = size, halign = "center", font = "Liberation Sans:style=Bold");
}

module pocket() {
    solid([slit_width, block_width + 2, slit_depth + 1], [(slit_inner + slit_outer) / 2, 0, -1]);
    solid([slit_inner - relief_inner, block_width + 2, slit_depth + 6.9], [(relief_inner + slit_inner) / 2, 0, -1]);
    solid([slit_outer - relief_inner, block_width + 2, 3], [(relief_inner + slit_outer) / 2, 0, -1]);
    solid([bar_width + jaw_opening + 0.6, bar_length + 0.6, bar_height + 1.3], [bar_center - jaw_opening / 2, 0, -1]);
    for (beam_y = beam_positions)
        solid([flexure_root - 0.2 - relief_inner, 7, 6], [(flexure_root - 0.2 + relief_inner) / 2, beam_y, slit_depth + 2]);
}

module rounded_body_blank() {
    hull()
        for (corner_x = [-1, 1], corner_y = [-1, 1], corner_z = [edge_radius, block_thickness - edge_radius])
            translate([corner_x * (block_length / 2 - edge_radius), corner_y * (block_width / 2 - edge_radius), corner_z])
                sphere(r = edge_radius, $fn = 64);
}

module block_body() {
    difference() {
        rounded_body_blank();
        solid([sticky_length, seal_width, seal_recess_depth + 1], [0, 0, -1]);
        pocket();
        mirror([1, 0, 0]) pocket();
    }
}

module moving_jaw(pressed = false) {
    rise = pressed ? button_travel : 0;
    shift = pressed ? -jaw_opening : 0;
    translate([shift, 0, rise]) intersection() {
        union() {
            solid([stem_outer - stem_inner, block_width, slit_depth + 4.7], [(stem_inner + stem_outer) / 2, 0, 0.5]);
            solid([slit_outer - closed_gap - stem_inner, block_width, 1.3], [(stem_inner + slit_outer - closed_gap) / 2, 0, 0.5]);
            solid([bar_width, bar_length, bar_height], [bar_center, 0, -button_travel]);
        }
        translate([0, 0, -button_travel]) rounded_body_blank();
    }
    for (beam_y = beam_positions)
        hull() {
            solid([flexure_thickness, 6, flexure_thickness], [flexure_root, beam_y, flexure_top - flexure_thickness / 2]);
            solid([flexure_thickness, 6, flexure_thickness], [stem_outer + shift - 0.25, beam_y, slit_depth + 4.3 + rise]);
        }
}

module top_block(left_pressed = false, right_pressed = false, colored = false) {
    color(body_tint) block_body();
    color(colored ? bar_tint : body_tint) {
        moving_jaw(right_pressed);
        mirror([1, 0, 0]) moving_jaw(left_pressed);
    }
}

module underside_scene(left_pressed = false, right_pressed = false) {
    translate([0, 0, block_thickness]) rotate([180, 0, 0]) top_block(left_pressed, right_pressed);
}

module tab_proxy() {
    color([0.25, 0.65, 0.93, 0.7])
        solid([tab_thickness, 10, slit_depth + button_travel + tab_thickness],
            [slit_outer - tab_thickness / 2, 0, -button_travel - tab_thickness]);
}

module section(pressed = false) {
    intersection() {
        top_block(false, pressed, true);
        solid([10.88, 10, block_thickness + 2], [58.44, 0, -1]);
    }
    tab_proxy();
}

module seal_proxy(tabs_inserted = true, bars_pressed = false) {
    tab_drop = tabs_inserted && !bars_pressed ? button_travel : 0;
    bar_inboard = bar_center - bar_width / 2;
    color([0.22, 0.70, 0.91, 0.8]) {
        if (tabs_inserted)
            rotate([90, 0, 0]) linear_extrude(height = seal_width, center = true)
                polygon([
                    [-sticky_length / 2, -tab_drop], [-bar_inboard, -tab_drop],
                    [-bar_inboard + 2, seal_recess_depth], [bar_inboard - 2, seal_recess_depth],
                    [bar_inboard, -tab_drop], [sticky_length / 2, -tab_drop],
                    [sticky_length / 2, -tab_drop - tab_thickness], [bar_inboard, -tab_drop - tab_thickness],
                    [bar_inboard - 2, seal_recess_depth - tab_thickness], [-bar_inboard + 2, seal_recess_depth - tab_thickness],
                    [-bar_inboard, -tab_drop - tab_thickness], [-sticky_length / 2, -tab_drop - tab_thickness]
                ]);
        else
            solid([sticky_length, seal_width, tab_thickness], [0, 0, -tab_thickness]);
    }
    for (tab_side = [-1, 1])
        scale([tab_side, 1, 1]) color([0.97, 0.69, 0.24]) {
            if (tabs_inserted) {
                solid([slit_outer - sticky_length / 2, seal_width, tab_thickness],
                    [(sticky_length / 2 + slit_outer) / 2, 0, -tab_thickness - tab_drop]);
                solid([tab_thickness, seal_width, slit_depth + tab_thickness + tab_drop],
                    [slit_outer - tab_thickness / 2, 0, -tab_thickness - tab_drop]);
            } else {
                solid([seal_tab_length, seal_width, tab_thickness],
                    [(sticky_length + seal_tab_length) / 2, 0, 0]);
            }
        }
}

module plate_proxy() {
    color([0.85, 0.87, 0.88]) difference() {
        solid([plate_length, plate_width, 12], [0, 0, -12]);
        solid([122, 79, 1], [0, 0, -tab_thickness]);
        for (column = [0:11], row = [0:7])
            translate([column * 9 - 49.5, row * 9 - 31.5, -4.2]) cylinder(r = 2.7, h = 5);
    }
}

module block_cutaway(pressed = false) {
    intersection() {
        top_block(pressed, pressed, true);
        solid([block_length + 2, block_width / 2, block_thickness + 2], [0, block_width / 4, -1]);
    }
}

module seal_stage(stage = 0) {
    block_height = stage == 1 ? 0 : 24;
    plate_proxy();
    translate([0, 0, block_height]) block_cutaway(stage == 1);
    translate([0, 0, stage == 0 ? block_height : 0]) seal_proxy(stage != 2, stage == 1);
}

if (view == "part") {
    top_block(false, false, false);
} else if (view == "print_part") {
    translate([0, 0, block_thickness]) rotate([180, 0, 0]) top_block(false, false, false);
} else if (view == "underside") {
    underside_scene();
    label("SEAL TOP BLOCK", [0, -65, 0], 7);
    label(str(block_length, " x ", block_width, " x ", block_thickness, " MM / UNDERSIDE SHOWN"), [0, -78, 0], 3.8);
    label(str(sticky_length, " x ", seal_width, " x ", seal_recess_depth, " MM RECESS / ", slit_depth, " MM TAB STOPS"), [0, -90, 0], 3.3);
} else if (view == "states") {
    translate([-85, 0, 0]) underside_scene();
    translate([85, 0, 0]) underside_scene(true, false);
    label("BOTH FREE: GRIP", [-85, -65, 0], 5);
    label("LEFT FLUSH: LEFT RELEASED", [85, -65, 0], 4.2);
    label("BAR TRAVEL 0.4 MM / RIGHT SIDE REMAINS CLOSED", [0, -84, 0], 4);
} else if (view == "section") {
    translate([-17, 0, 0]) section();
    translate([17, 0, 0]) section(true);
    label("FREE", [44, -15, 0], 3);
    label("FLUSH", [78, -15, 0], 3);
    label("INTERNAL FLEXURE / POSED STATES, NOT A FORCE SIMULATION", [61, -27, 0], 2.2);
} else if (view == "print_depressed") {
    translate([0, 0, block_thickness]) rotate([180, 0, 0]) top_block(true, true, false);
} else if (view == "loaded") {
    translate([0, 0, block_thickness]) rotate([180, 0, 0]) {
        top_block();
        seal_proxy();
    }
    label("LOADED / UNDERSIDE", [0, -68, 0], 6);
    label("BLUE: SEAL / GOLD: TABS FOLDED INTO SLITS", [0, -81, 0], 3.6);
} else if (view == "loading") {
    translate([0, 0, block_thickness]) rotate([180, 0, 0]) {
        top_block();
        seal_proxy();
    }
    label("SEAL LOADING / SHALLOW REGISTRATION RECESS", [0, -68, 0], 4);
    label(str(sticky_length, " x ", seal_width, " MM RECESS / ", slit_depth, " MM TAB STOPS"), [0, -81, 0], 3.2);
} else if (view == "tab_stop_check") {
    intersection() {
        top_block(true, true);
        tab_proxy();
    }
} else if (view == "plate_collision") {
    intersection() {
        top_block(true, true);
        plate_proxy();
    }
} else if (view == "unloaded") {
    seal_stage(2);
    label("UNLOADED / CUTAWAY", [0, -68, -12], 6);
    label("SEAL LEFT ON PLATE / EMPTY BLOCK ABOVE", [0, -81, -12], 3.6);
    label("INTENDED END STATE / WITHDRAWAL NOT VALIDATED", [0, -93, -12], 3);
} else if (view == "workflow") {
    for (stage = [0:2]) translate([(stage - 1) * 175, 0, 0]) {
        seal_stage(stage);
        label(["1  LOADED", "2  PRESS / RELEASE", "3  UNLOADED"][stage], [0, -66, -12], 5.2);
        label(["TABS INSERTED / BARS FREE", "BOTH BARS FLUSH / JAWS OPEN", "SEAL ON PLATE / BLOCK LIFTED"][stage], [0, -78, -12], 3.2);
    }
    label("CUTAWAY MOCKUP / SCHEMATIC PLATE AND SEAL / NOT A VALIDATED MOTION SEQUENCE", [0, -96, -12], 4);
} else if (view == "edge_press") {
    plate_proxy();
    seal_proxy(false);
    translate([0, -seal_width / 2 + edge_radius, edge_radius])
        rotate([edge_press_angle, 0, 0])
            translate([0, block_width / 2 - edge_radius, -edge_radius]) top_block(true, true);
    label("LONG EDGE / ANGLED PRESS", [0, -68, -12], 5);
    label(str(edge_radius, " MM RADIUS / ", edge_press_angle, " DEG ILLUSTRATIVE POSE"), [0, -81, -12], 3.5);
    label("BOTH BARS FLUSH / CONTACT FORCE NOT VALIDATED", [0, -93, -12], 2.8);
} else if (view == "envelope_check") {
    difference() {
        top_block();
        solid([block_length, block_width, block_thickness + button_travel], [0, 0, -button_travel]);
    }
} else {
    assert(false, str("Unknown view: ", view));
}