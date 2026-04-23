/* ================================================================
   Cytiva / GE Healthcare ÄKTA avant F9-C Fraction Collector
   Outer Cooling Box  —  6-position (2 × 3)

   Inner tray (cytiva_50ml_inner_tray.scad) sits inside with
   5 mm clearance on all sides.
   ================================================================ */

// ── Render quality ──────────────────────────────────────────────
$fn = 64;

// ================================================================
//  PARAMETERS  (edit here)
// ================================================================

// — Tube geometry (must match inner tray) ────────────────────────
tube_od        = 29.0;
tube_clearance = 0.6;

// — Cassette layout (must match inner tray) ──────────────────────
n_cols         = 2;
n_rows         = 3;
col_pitch      = 36.0;
row_pitch      = 36.0;

// — Inner tray dimensions (must match inner tray) ────────────────
tray_wall      = 3.0;
wall           = 3.0;
base_t         = 2.5;
pocket_depth   = 102.5;

// — Outer cooling box ────────────────────────────────────────────
outer_gap      = 5.0;    // Air gap between inner tray and outer box walls (mm)
outer_wall     = 3.0;    // Outer box wall & floor thickness (mm)
rib_t          = 2.5;    // Support rib thickness (mm)
rib_clearance  = 0.25;   // Clearance per side between inner tray and ribs (mm)
// Outside dimensions (fixed)
ob_w           = 95.25;  // 3.75 in
ob_d           = 125.35; // 5.25 in minus barcode tab protrusion (133.35 - 8.0 mm)
ob_h           = 101.6;  // 4.00 in

// — Barcode tab ──────────────────────────────────────────────────
bc_tab_proj    = 8.0;    // Protrusion of triangular brace from short end face (mm)
bc_notch_w     = 3.175;  // Notch width  (1/8 in)
bc_notch_len   = 3.175;  // Notch depth into tab from tip (1/8 in)
// Left edge of each notch measured from the left edge of the outer box (mm):
// 5/8", 1.25", 1.5", 1-15/16", 2.5", 2-7/8"
bc_notch_offsets = [15.875, 31.75, 38.1, 49.2125, 63.5, 73.025];

// ================================================================
//  DERIVED DIMENSIONS  (do not edit)
// ================================================================

pocket_d = tube_od + tube_clearance * 2;
cyl_od   = pocket_d + 2 * wall;
body_h   = base_t + pocket_depth;

tray_inner_w = (n_cols - 1) * col_pitch + cyl_od;
tray_inner_d = (n_rows - 1) * row_pitch + cyl_od;
tray_outer_w = tray_inner_w + 2 * tray_wall;
tray_outer_d = tray_inner_d + 2 * tray_wall;

ob_inner_w = ob_w - 2 * outer_wall;
ob_inner_d = ob_d - 2 * outer_wall;

// ================================================================
//  MODULES
// ================================================================

// ── Outer cooling box (5-sided open-top) ──────────────────────
module outer_box() {
    difference() {
        translate([-ob_w / 2, -ob_d / 2, 0])
            cube([ob_w, ob_d, ob_h]);
        translate([-ob_inner_w / 2, -ob_inner_d / 2, outer_wall])
            cube([ob_inner_w, ob_inner_d, ob_h]);
    }
}

// ── Support ribs ──────────────────────────────────────────────
//   1 rib along X at Y = 0 (bisects long dimension)
//   1 rib along Y at X = 0 (bisects short dimension)
module support_ribs() {
    rib_z = outer_wall;              // ribs sit on top of the floor
    rib_h = ob_h - outer_wall;      // ribs stop flush with the top of the box

    difference() {
        union() {
            // Along X (bisects long / Y dimension)
            translate([-ob_inner_w / 2, -rib_t / 2, rib_z])
                cube([ob_inner_w, rib_t, rib_h]);
            // Along Y (bisects short / X dimension)
            translate([-rib_t / 2, -ob_inner_d / 2, rib_z])
                cube([rib_t, ob_inner_d, rib_h]);
        }
        // Clear rib material only where the inner tray sits (above the gap)
        // +rib_clearance per side so the inner tray slides in freely
        translate([-(tray_outer_w / 2 + rib_clearance) - 0.1,
                   -(tray_outer_d / 2 + rib_clearance) - 0.1,
                   outer_wall + outer_gap - 0.1])
            cube([tray_outer_w + 2 * rib_clearance + 0.2,
                  tray_outer_d + 2 * rib_clearance + 0.2,
                  rib_h + 0.2]);
    }
}

// ── Barcode tab (short +Y face, top) ──────────────────────────
//   Triangular brace at top of +Y face; 6 notches cut from the tip inward.
module barcode_tab() {
    end_y  = ob_d / 2;

    difference() {
        translate([-ob_w / 2, end_y, ob_h])
            rotate([0, 90, 0])
                linear_extrude(height = ob_w)
                    polygon([[0, 0], [bc_tab_proj, 0], [0, bc_tab_proj]]);

        // Each notch: bc_notch_w wide (X), bc_notch_len deep from tip (Y)
        for (offset = bc_notch_offsets) {
            nx = ob_w / 2 - offset - bc_notch_w;
            translate([nx,
                       end_y + bc_tab_proj - bc_notch_len - 0.1,
                       ob_h - bc_tab_proj - 0.1])
                cube([bc_notch_w,
                      bc_notch_len + 0.2,
                      bc_tab_proj + 0.2]);
        }
    }
}

// ================================================================
//  ASSEMBLY
// ================================================================

outer_box();
support_ribs();
barcode_tab();
