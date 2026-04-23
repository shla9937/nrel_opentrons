/* ================================================================
   Cytiva / GE Healthcare ÄKTA avant F9-C Fraction Collector
   Combined Ice Bath Cassette  —  6-position (2 × 3)

   Inner tray sits directly on the outer box floor (no gap ribs).
   Inner tray height fills the full interior to be flush with the top.
   Print as a single piece.
   ================================================================ */

// ── Render quality ──────────────────────────────────────────────
$fn = 64;

// ================================================================
//  PARAMETERS  (edit here)
// ================================================================

// — Tube geometry ────────────────────────────────────────────────
tube_od        = 29.0;   // Nominal OD of a 50 mL conical tube (mm)
tube_clearance = 0.6;    // Extra radial clearance per side (mm)

// — Cassette layout ──────────────────────────────────────────────
n_cols         = 2;      // Number of columns  (left ↔ right)
n_rows         = 3;      // Number of rows     (front ↔ back)
tube_edge      = 25.4;   // Tube centre to outer box edge  (1.00 in)

// — Outside dimensions (fixed) ───────────────────────────────────
ob_w           = 95.25;   // 3.75 in
ob_d           = 133.35;  // 5.25 in (full length, notches cut into end wall)
ob_h           = 101.6;   // 4.00 in

// — Wall thicknesses ─────────────────────────────────────────────
outer_wall     = 3.0;    // Outer box wall & floor thickness (mm)
gap            = 3.5;    // Gap between inner tray and outer box walls (mm)
tray_wall      = 3.0;    // Inner tray wall thickness (mm)
rib_t          = 2.5;    // Connecting rib thickness (mm)
wall           = 3.0;    // Tube cylinder wall thickness (mm)
base_t         = 2.5;    // Floor thickness inside each tube cylinder (mm)
chamfer        = 1.2;    // Top-edge chamfer on tube bore (mm)

// — Barcode notches (cut into short end wall) ───────────────────
bc_notch_w     = 3.175;  // Notch width  (1/8 in)
bc_notch_h     = 25.4;   // Notch height (1.00 in) — runs along the 4 in tall axis
bc_notch_depth = 3.175 + 0.2;  // Notch depth into wall face (1/8 in + overshoot)
// Left edge of each notch from the right edge of the outer box (mm):
// 5/8", 1.25", 1.5", 1-15/16", 2.5", 2-7/8"
bc_notch_offsets = [15.875, 31.75, 38.1, 49.2125, 63.5, 73.025];

// ================================================================
//  DERIVED DIMENSIONS  (do not edit)
// ================================================================

pocket_d = tube_od + tube_clearance * 2;
cyl_od   = pocket_d + 2 * wall;

col_pitch = ob_w - 2 * tube_edge;       // 44.45 mm
row_pitch = ob_d / 2 - tube_edge;       // 37.275 mm

ob_inner_w = ob_w - 2 * outer_wall;
ob_inner_d = ob_d - 2 * outer_wall;

// Inner tray outer dims: 5mm gap to outer box walls on all sides
tray_outer_w = ob_inner_w - 2 * gap;
tray_outer_d = ob_inner_d - 2 * gap;
body_h       = ob_h - outer_wall;       // flush with box top
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

// ── Support ribs (connect inner tray to outer box across gap) ─
//   1 rib along X at Y=0, 1 rib along Y at X=0.
//   Both span the full inner box width/depth, inner tray interior subtracted.
module support_ribs() {
    difference() {
        union() {
            // Along X — bisects long (Y) dimension
            translate([-ob_inner_w / 2, -rib_t / 2, 0])
                cube([ob_inner_w, rib_t, body_h]);
            // Along Y — bisects short (X) dimension
            translate([-rib_t / 2, -ob_inner_d / 2, 0])
                cube([rib_t, ob_inner_d, body_h]);
        }
        // Remove rib material from inside the inner tray (above tray floor)
        translate([-tray_inner_w / 2, -tray_inner_d / 2, tray_wall])
            cube([tray_inner_w, tray_inner_d, body_h]);
    }
}

// ── Outer box (5-sided open-top) ──────────────────────────────
module outer_box() {
    difference() {
        translate([-ob_w / 2, -ob_d / 2, 0])
            cube([ob_w, ob_d, ob_h]);
        translate([-ob_inner_w / 2, -ob_inner_d / 2, outer_wall])
            cube([ob_inner_w, ob_inner_d, ob_h]);
    }
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

// ── Gap fill on +Y side (barcode wall), top 1in+3mm ─────────────
//   Fills the gap between inner tray and +Y outer wall for the top section.
//   Bottom transitions via a 45° triangle ramp for printability.
//   Called inside translate([0,0,outer_wall]) block.
module gap_fill_y_plus() {
    rect_h = 25.4 + 3.0;          // 1 in + 3 mm tall in Z (solid rectangular fill)
    ramp_h = gap;                  // ramp height below the rectangle = gap width
    y0     = tray_outer_d / 2;    // inner edge of +Y gap (inner tray outer wall)
    y1     = ob_inner_d / 2;      // outer edge of +Y gap (outer box inner face)
    z_rect = body_h - rect_h;     // z of bottom of rectangular fill (local coords)
    z_ramp = z_rect - ramp_h;     // z of bottom of ramp

    // 45° ramp below the rectangle
    hull() {
        translate([-ob_inner_w / 2, y1 - 0.001, z_ramp])
            cube([ob_inner_w, 0.001, 0.001]);
        translate([-ob_inner_w / 2, y0, z_rect - 0.001])
            cube([ob_inner_w, gap, 0.001]);
    }
    // Rectangular fill: 1 in + 3 mm tall
    translate([-ob_inner_w / 2, y0, z_rect])
        cube([ob_inner_w, gap, rect_h]);
}

// ── Barcode notches (cut into short +Y end wall) ──────────────
//   Rectangular slots cut from the outside face through the wall,
//   positioned at the top of the wall.
module barcode_notches() {
    end_y = ob_d / 2;   // outer face of +Y wall
    nz    = ob_h - bc_notch_h;  // notch sits at the top of the wall

    for (offset = bc_notch_offsets) {
        nx = ob_w / 2 - offset - bc_notch_w;
        translate([nx, end_y - bc_notch_depth + 0.1, nz])
            cube([bc_notch_w, bc_notch_depth, bc_notch_h]);
    }
}

// ================================================================
//  ASSEMBLY
// ================================================================

// Notches are subtracted at the top level so they cut both the outer
// wall and the gap fill behind it.
difference() {
    union() {
        outer_box();
        translate([0, 0, outer_wall]) {
            ice_tray();
            cassette_body();
            support_ribs();
            gap_fill_y_plus();
        }
    }
    barcode_notches();
}
