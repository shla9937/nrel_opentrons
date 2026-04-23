/* ================================================================
   Cytiva / GE Healthcare ÄKTA avant F9-C Fraction Collector
   Inner Ice Tray with Tube Holders  —  6-position (2 × 3)

   Sits inside cytiva_50ml_outer_box.scad with 5 mm clearance.
   ================================================================ */

// ── Render quality ──────────────────────────────────────────────
$fn = 64;

// ================================================================
//  PARAMETERS  (edit here)
// ================================================================

// — Tube geometry ————————————————————————————————————————————————
tube_od        = 29.0;   // Nominal OD of a 50 mL conical tube (mm)
tube_clearance = 0.6;    // Extra radial clearance per side (mm)

// — Cassette layout ──────────────────────────────────────────────
n_cols         = 2;      // Number of columns  (left ↔ right)
n_rows         = 3;      // Number of rows     (front ↔ back)
tube_edge      = 25.4;   // Tube centre to outer box edge  (1.00 in)

// — Ice tray ─────────────────────────────────────────────────────
tray_wall      = 3.0;    // Tray wall & floor thickness (mm)

// — Outer box reference dims (must match cytiva_50ml_outer_box.scad) ─────────
ob_w           = 95.25;  // Outer box width  (3.75 in)
ob_d           = 125.35; // Outer box depth  (5.25 in - 8 mm tab)
ob_h           = 101.6;  // Outer box height (4.00 in)
outer_wall     = 3.0;    // Outer box wall & floor thickness (mm)
outer_gap      = 5.0;    // Gap between outer floor and inner tray floor (mm)

// — Cylinder holders ─────────────────────────────────────────────
wall           = 3.0;    // Cylinder wall thickness (mm)
base_t         = 2.5;    // Floor thickness inside each cylinder (mm)
chamfer        = 1.2;    // Top-edge chamfer (mm)

// ================================================================
//  DERIVED DIMENSIONS  (do not edit)
// ================================================================

pocket_d = tube_od + tube_clearance * 2;
cyl_od   = pocket_d + 2 * wall;

// col_pitch: distance between the 2 column centres
// The two columns are each 1 in from the outer box edge, so pitch = ob_w - 2*tube_edge
col_pitch = ob_w - 2 * tube_edge;       // 44.45 mm

// row_pitch: distance between adjacent row centres
// Corner rows are 1 in from the outer box ends; middle row is at Y=0 (centre)
// So rows are at -row_pitch, 0, +row_pitch where row_pitch = ob_d/2 - tube_edge
row_pitch = ob_d / 2 - tube_edge;       // 37.275 mm

// Inner tray outer dims = outer box interior
tray_outer_w = ob_w - 2 * outer_wall;
tray_outer_d = ob_d - 2 * outer_wall;

// Height: sits on gap ledge, flush with top of outer box
body_h       = ob_h - outer_wall - outer_gap;
pocket_depth = body_h - base_t;

tray_inner_w = tray_outer_w - 2 * tray_wall;
tray_inner_d = tray_outer_d - 2 * tray_wall;

function cx(c) = (c - (n_cols - 1) / 2.0) * col_pitch;
function cy(r) = (r - (n_rows - 1) / 2.0) * row_pitch;

// ================================================================
//  MODULES
// ================================================================

module tube_bore(h, d, ch) {
    cylinder(d = d, h = h);
    translate([0, 0, h - ch])
        cylinder(d1 = d, d2 = d + ch * 2, h = ch + 0.01);
}

// ── Tube holder cylinders ──────────────────────────────────────
module cassette_body() {
    difference() {
        union()
            for (c = [0 : n_cols - 1], r = [0 : n_rows - 1])
                translate([cx(c), cy(r), 0])
                    cylinder(d = cyl_od, h = body_h);
        for (c = [0 : n_cols - 1], r = [0 : n_rows - 1])
            translate([cx(c), cy(r), base_t])
                tube_bore(body_h - base_t + 0.1, pocket_d, chamfer);
    }
}

// ── Ice tray (5-sided open-top box) ───────────────────────────
module ice_tray() {
    difference() {
        translate([-tray_outer_w / 2, -tray_outer_d / 2, 0])
            cube([tray_outer_w, tray_outer_d, body_h]);
        translate([-tray_inner_w / 2, -tray_inner_d / 2, tray_wall])
            cube([tray_inner_w, tray_inner_d, body_h]);
    }
}

// ================================================================
//  ASSEMBLY
// ================================================================

ice_tray();
cassette_body();
