base_length = 127.76;
base_width = 85.48;
base_radius = 3;
floor_thickness = 3;
column_count = 3;
row_count = 2;
chamber_pitch = 41;
body_diameter = 40;
wall_thickness = 2;
belly_height = 13;
sump_height = 5;
sump_tip_diameter = 1.5;
shoulder_height = 37;
neck_outer_diameter = 22;
neck_height = 10;
cross_section = false;
profile_slice = 0.001;
$fn = 128;

inner_diameter = body_diameter - 2 * wall_thickness;
neck_inner_diameter = neck_outer_diameter - 2 * wall_thickness;
shoulder_bottom = floor_thickness + belly_height;
neck_bottom = shoulder_bottom + shoulder_height;
total_height = neck_bottom + neck_height;
shoulder_inset = (inner_diameter - neck_inner_diameter) / 2;
shoulder_angle = atan(shoulder_inset / shoulder_height);
belly_area = PI * inner_diameter * inner_diameter / 4;
mean_sump_area = PI * (sump_tip_diameter * sump_tip_diameter
    + sump_tip_diameter * inner_diameter + inner_diameter * inner_diameter) / 12;
mean_shoulder_area = PI * (inner_diameter * inner_diameter
    + inner_diameter * neck_inner_diameter
    + neck_inner_diameter * neck_inner_diameter) / 12;
cavity_estimate_ml = (belly_area * (belly_height - sump_height)
    + mean_sump_area * sump_height
    + mean_shoulder_area * shoulder_height
    + PI * neck_inner_diameter * neck_inner_diameter * neck_height / 4) / 1000;

assert(base_length > 0 && base_width > 0 && floor_thickness >= 3);
assert(base_radius > 0 && 2 * base_radius <= min(base_length, base_width));
assert(column_count == 3 && row_count == 2, "Plate requires six chambers");
assert(wall_thickness >= 2 && inner_diameter > 0);
assert(neck_inner_diameter > 0 && neck_outer_diameter < body_diameter);
assert(chamber_pitch >= inner_diameter + wall_thickness, "Cavities must remain isolated");
assert(body_diameter / 2 >= base_radius);
assert((column_count - 1) * chamber_pitch + body_diameter <= base_length);
assert((row_count - 1) * chamber_pitch + body_diameter <= base_width);
assert(belly_height > 0 && neck_height > 0 && shoulder_height > 0);
assert(sump_height > 0 && sump_height < belly_height);
assert(sump_tip_diameter > 0 && sump_tip_diameter < inner_diameter);
assert(profile_slice > 0 && profile_slice <= 0.01);
assert(shoulder_inset > 0 && shoulder_angle <= 45, "Shoulder exceeds 45 degrees from vertical");
assert($fn >= 64 && $fn % 4 == 0);

echo(footprint_mm = [base_length, base_width], height_mm = total_height,
    approximate_capacity_ml = cavity_estimate_ml,
    shoulder_degrees_from_vertical = shoulder_angle);

module chamber_void() {
    translate([0, 0, floor_thickness])
        cylinder(h = sump_height, d1 = sump_tip_diameter, d2 = inner_diameter);
    translate([0, 0, floor_thickness + sump_height])
        cylinder(h = belly_height - sump_height, d = inner_diameter);
    translate([0, 0, shoulder_bottom])
        cylinder(h = shoulder_height, d1 = inner_diameter, d2 = neck_inner_diameter);
    translate([0, 0, neck_bottom])
        cylinder(h = neck_height + profile_slice, d = neck_inner_diameter);
}

module chamber_positions() {
    for (column_index = [0 : column_count - 1])
        for (row_index = [0 : row_count - 1])
            translate([(column_index - (column_count - 1) / 2) * chamber_pitch,
                (row_index - (row_count - 1) / 2) * chamber_pitch, 0])
                children();
}

module plate_body() {
    difference() {
        linear_extrude(height = total_height)
            offset(r = base_radius)
                square([base_length - 2 * base_radius,
                    base_width - 2 * base_radius], center = true);
        chamber_positions() chamber_void();
    }
}

if (cross_section) {
    difference() {
        plate_body();
        translate([-base_length, -(row_count - 1) * chamber_pitch / 2, -1])
            cube([2 * base_length, 2 * base_width, total_height + 2]);
    }
} else {
    plate_body();
}