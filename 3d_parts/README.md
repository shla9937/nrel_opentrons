# NLR Robotics Desk Ornament

[NLR Robotics Desk Ornament source](nlr_robotics_desk_ornament.scad) is a self-contained, static ornamental sculpture. It is not a working robot, robot-handling accessory, or brand-approved artwork.

## Final distribution assets

- [Combined multipart core3MF](exports/nlr_robotics_desk_ornament/nlr_robotics_desk_ornament.3mf) — one build item containing four registered parts in a common coordinate system.
- [Unified solid STL](exports/nlr_robotics_desk_ornament/solid.stl) — a single-colour union; flush colour boundaries are not visible in this version.
- Previews: [front](exports/nlr_robotics_desk_ornament/front.png) and [three-quarter](exports/nlr_robotics_desk_ornament/three-quarter.png).
- Registered colour parts: [navy](exports/nlr_robotics_desk_ornament/parts/navy.3mf), [blue](exports/nlr_robotics_desk_ornament/parts/blue.3mf), [gold](exports/nlr_robotics_desk_ornament/parts/gold.3mf), and [white](exports/nlr_robotics_desk_ornament/parts/white.3mf).

Do not independently auto-arrange, centre, or drop the individual parts to the build plate. They are registered for co-printing as one object.

## Geometry

All dimensions are in millimetres. Front is −Y and the underside is Z=0.

| Feature | Design detail |
| --- | --- |
| Overall footprint | 127.4 × 85 × 86 mm |
| Base | 22 mm high, rounded rectangular side-grip base with 1 mm top and bottom chamfers |
| Mountain | Navy outline, white full-depth valley, blue mesa, and two flush white snow inlays |
| Text | Flush white `NLR` and `Robotic Biology` front inlays |
| Arm | White articulated arm and pedestal with a gold upright sun disk |

The colour regions are matching Boolean partitions with shared boundaries; they are not overlapping stacks. The XZ artwork outlines, vertical depth ridge, white valley, text, colours, arm, and dimensions are represented in the source model.

## Four-colour palette

| Part | Display colour | Contents |
| --- | --- | --- |
| navy | #003a69 | Base and navy mountain, excluding white pockets |
| blue | #0079C2 | Mesa |
| gold | #db9728 | Sun disk |
| white | #f2f4f5 | Valley, snow, lettering, arm, pedestal, and cup |

The combined core3MF supplies four named parts and core display colours only. It has **no AMS assignment**: assign navy, blue, gold, and white deliberately in the slicer.

## Bambu A1 starting point — unvalidated

For a 0.4 mm nozzle, use 0.16–0.20 mm layers, 3–4 walls, and 15–20% infill only as starter settings. Keep the 22 mm base flat on the bed and inspect sliced layers around lettering, snow, mountain tips, arm, pedestal, cup, and sun.

This model **must be sliced and physically test printed** before any intended use. Check imported part registration, support needs, purge strategy, colour interfaces, filament assignments, clearances, grip, collisions, and material behaviour on the actual machine. The model is not certified for Bambu A1 printing, Opentrons Flex, BioGripper, or any robotic handling workflow.

No assembly clearance, pins, or press fits are provided. Treat this as a display ornament and validate any handling or mechanical use independently.

## Omega 24-well friction lid — unverified fit prototype

- [Parametric source](omega_24well_friction_lid.scad)
- [Full print STL](omega_24well_friction_lid.stl)

This separate design leaves the legacy gripper lid, robot definitions and
protocols unchanged. It has **no side clips, tabs or gripping pads**.

The confirmed upper body is 111.2 × 74.8 mm, with 6×4 nominal 17 mm square
openings and 3.5 mm corner posts flush with the rim. **Grid centring and
18.0 mm uniform pitch are provisional**: the same-edge 89.8 mm span suggests
17.96 mm pitch; the reported 108 × 71 mm spans do not fully agree. Approximate
1 mm internal / 2 mm external walls are consistent with this starting layout,
not independent proof of fit.

The 2.4 mm roof provides flat film lands around 24 open, 13.8 mm rounded-square
passages (2.4 mm corner radius). Assumed straight 16.4 mm collars extend 5 mm
below the seating plane, with 0.3 mm clearance per flat side and a 0.8 mm axial
lead-in reducing each side by 0.4 mm. Reliefs around the nominal opening
vertices allow 1.75 mm post radius plus 0.3 mm clearance. The 4 mm skirt has
0.5 mm external clearance per side, 1.6 mm walls and a 0.6 mm lead-in.
Actual well taper, insertion depth, post positions and skirt obstructions
remain unmeasured.

Only zero-based wells `(1,1), (4,1), (1,2), (4,2)` carry opposing X-wall ribs:
17.1 mm across their extrema, or nominal 0.05 mm interference per side.
Adjust `retention_interference` and `retention_depth` in the source; these are
geometry settings, **not retention-force guarantees**. Ribs have rounded edges
and ramps at both ends; no feature projects into a passage.

Assembly coordinates are centred XY, with the rim at Z=0 and film face at
Z=2.4. The STL is already rotated 180° about X and translated so the
**film lands lie on the bed at Z=0**, with inserts upwards. Full size:
115.4 × 79 × 7.4 mm.

Regenerate from the repository root (`openscad` may be replaced by
`/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`):

```sh
openscad --export-format binstl -o 3d_parts/omega_24well_friction_lid.stl 3d_parts/omega_24well_friction_lid.scad
```

The CLI-rendered mesh was checked as a single connected, watertight solid with
24 through-passages. Mesh sections confirmed rib spans and approximately
1.206 mm minimum relieved wall thickness away from the lead-in; flat tip
walls are 0.9 mm. Nominal plate intersection contained only the eight intended
rib contacts, with no corner-post clearance-envelope collisions.
These checks do **not** validate the physical plate. Inspect sliced walls and
bed-side passage dimensions, then trial the printed lid gently without forcing
it onto the plate. Material shrinkage, film adhesion, sealing, removal force, retention,
shaking and robotic handling remain unqualified; no film or seal is included.