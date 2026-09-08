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