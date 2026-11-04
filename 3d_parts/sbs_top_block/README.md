# Seal Top Block and Raised Dock

The top remains a largely solid rectangular block, not a hollow shell, with localized tab-clamp clearances. Its companion dock adds a raised SBS-footprint pedestal, corner guides and one smaller backing clamp with a round finger button. Both are intended as separate one-piece prints, without screw hardware or powered parts. Gold in the previews identifies integral jaw/button flexures, not separate components.

## Files

- [Top underside preview](underside.png)
- [Dock overview](dock_dock.png)
- [Top STL](top_block.stl)
- [Dock STL](dock.stl)
- [Top OpenSCAD source](concept.scad)
- [Dock OpenSCAD source](dock.scad)

Only these two PNG previews and the two normal-state STLs are retained. Other posed and section views remain available in the OpenSCAD source but are not exported by default.

## Seal Registration

1. The top's raised loading guides are removed. A 120 x 78 mm rectangular indentation, 0.2 mm deep, matches the assumed adhesive-region outline. Align that region with the recess, then insert the handling tabs into the two slots. The release bars retain their original height and interrupt the recess near its ends; they are not recessed or shortened.
2. Align the backing with the dock's matching 120 x 78 x 0.2 mm shallow indentation. The four raised liner fences are removed. The clamp opening and deeper outboard relief interrupt the recess at its positive-x end. The larger corner stops still locate the top block, not the seal.
3. Pre-peel the modeled 5 mm edge, press the dock's finger button, and feed the backing along the fixed slot wall until it reaches the insertion stop. This remains 2.2 mm below the original deck level, now 2.0 mm below the shallow recess floor. Release the button to clamp. Flexible or curled liner can still bend into adjacent jaw clearances; confirm reliable stop contact on a sample.

The top's tab stops are now 7.2 mm below the nominal face, rather than half the block thickness. The sharp-fold model uses an 8.5 mm tab, subtracts a 0.7 mm approach to the gripping wall, and accounts for 0.4 mm bar protrusion plus 0.2 mm modeled film thickness: 8.5 - 0.7 - 0.4 - 0.2 = 7.2 mm. Change the seal/tab parameters after measuring the real consumable. Bend radius, material thickness and slack are not validated; a curled tab may bypass the nominal stop into adjacent relief.

The recesses are positioning references, not a guarantee of uniform sealing pressure or support at the illustrated assembly height. The top recess changes contact with the central film area; confirm flat-placement contact and the separate long-edge pressing motion with the actual plate. The film and backing poses are illustrative, not a deformation simulation. Dock standoff pads remain removed; its clamp and corner stops are unchanged.

## Raised Dock

The dock is one printed piece, with an SBS-footprint pedestal, a flared platform, four corner stops, a shallow seal-registration indentation and exactly one backing-clamp slot on the positive-x side. A round finger button releases that clamp. The opposite clamp and the deep central clearance well remain removed; deeper adhesive relief is outside the remaining slot. It adds no screws, latch, magazine or powered parts.

| Feature | Provisional dimension |
| --- | --- |
| Lower footprint | 127.76 x 85.48 mm |
| Height before widening | 26 mm, adjustable with `deck_clearance_height` |
| Flare | 8 mm high, widening to 155 x 110 mm |
| Platform top | 38 mm above the base |
| Top's illustrated reference height | 40.5 mm above the base; support pads removed, not a resting position |
| Corner guides | Compact L-shaped stops: 6 mm inner legs, 1.6 mm walls, 7 mm above platform (45 mm total); 0.5 mm side clearance and 1 mm-high entry chamfer |
| Seal registration | 120 x 78 mm indentation, 0.2 mm deep; no raised liner fences |
| Backing slot | One 80 mm-long slot; x = 56.457 to 57.057 mm; insertion stop 2.2 mm below original deck level, 2.0 mm below the registration floor |
| Offset from top slot | 3.843 mm inward from the top's fixed gripping wall at x = 60.9 mm |
| Finger button | 10 mm diameter; flush and clamped when unpressed; press 0.35 mm below the deck surface to release; beside the liner, accessible with the top removed |
| Backing gripping mouth | 0.03556 mm nominal gap against a 0.0508 mm liner; print calibration required |
| Pre-peel allowance | 5 mm total: 2.8 mm sloping approach plus 2.2 mm inserted |
| Outboard clearance recess | Begins at x = 58.257 mm, beyond a 1.2 mm fixed-jaw wall; opens toward the positive-x platform edge; 84 mm wide and 3 mm deep |
| Adhesive air gap | At least 1.5 mm in the modeled pose; greater above the outboard recess |

Only the lower pedestal has an SBS footprint. The 26 mm height is an assumption, NOT a measured Flex deck-tab clearance. Measure from the actual seating surface to the highest interfering deck feature and include clearance before setting this parameter. An SBS rectangle alone does not reproduce the Flex slot's locating, spring-tab, retention or underside geometry. Verify those before printing for deck use. The widened upper dock overhangs its slot: reserve clearance from neighboring labware, modules and robot paths.

The four small corner support pads remain removed. Locating guides are reduced to short L-shaped corner stops, with enough height for a small locating face above the top's 3 mm lower-edge radius at the reference height. This is a geometric sizing choice, not a validated minimum for strength or robot placement accuracy. The illustrated 40.5 mm top height and associated liner path require external positioning, such as a gripper holding the top. Setting the top down freely may contact the liner or buttons and lose the illustrated adhesive gap. Corner stops constrain lateral movement, but do not provide the previous standoff. Gripper clearance and repeatability remain unverified. The dock itself must resist the upward peel load rather than lifting out of the Flex slot.

### Backing Clamp

Pre-peel one short backing edge and insert that exposed liner into the single dock clamp. A liner with tabs at both ends can still use this dock by gripping only one end; there is no second slot. Independently grippable liner tabs may be used if their dimensions fit, but the model does not require tabs extending beyond the adhesive region. The dock retains the disposable backing; the top retains the sealing film. Film handling tabs and backing-liner tabs are different features.

The illustrated backing is 78 mm wide beneath the top model's assumed 120 mm-long sealing region. The slot is not aligned with the top clamp. `liner_insertion_depth` is an explicit 2.2 mm input, leaving 2.8 mm of a 5 mm pre-peel for the sloping approach. With a 1.9 mm vertical drop, the horizontal run is sqrt(2.8^2 - 1.9^2) = 2.057 mm. Starting at x = 55 mm puts the dock gripping wall at x = 57.057 mm, 3.843 mm inward of the top gripping wall at x = 60.9 mm. This accounts for inserted material and the height difference, not just an arbitrary lateral offset. Bend radii, loading slack and the actual seal dimensions still need checking; the existing top retains its original film-dimension assumptions.

The central deck remains solid beneath its 0.2 mm registration indentation. The deeper clearance recess is strictly outboard of the slot, toward the exposed end of the adhesive and the positive-x platform edge. A 1.2 mm wall remains immediately outside the slot to provide its fixed clamping face. At the externally held reference height, the lowest modeled adhesive surface clears the original deck level by 1.9 mm and the deeper recess floor by at least 4.9 mm. With the support pads removed, these are positioning-dependent clearances, not guaranteed resting clearances. Prevent exposed adhesive from drooping into the dock during loading.

With the top removed, the round finger button rests flush with the dock platform and the jaw is normally clamped. Press the button downward by 0.35 mm, below the platform surface, to open the jaw for inserting or removing the backing. Releasing it is intended to return the button to flush and grip the liner. Its pocket leaves 0.3 mm bottom clearance in the fully depressed pose. The button sits outside the liner's width and connects to the end of the jaw with a short integral arm; it is not a full-width release bar. Its spring action, force and resistance to jaw twisting are untested. Manual loading and spent-liner removal are assumed. The exploded view separates components for visibility and is not a validated lift/peel motion.

The manufacturer specifications for [ThermalSeal RT2](https://excelscientific.com/wp-content/uploads/2021/12/Specs-ThermalSeal-RT2.pdf) and [ThermalSeal RTS](https://excelscientific.com/wp-content/uploads/2021/12/Specs-ThermalSeal-RTS.pdf) list 2 mil (0.0508 mm), +/-10% polyester release liners and film end tabs. They do not establish independent backing tabs. The dock's liner thickness is updated to that nominal value; the gripping gap is 70% of it to illustrate interference preload. This is not a validated print tolerance or a claim that either product fits the complete top-and-dock assembly.

### Dock Validation

The dock STL is base-down, labels and consumables excluded. It exports as one connected simple solid. The `adhesive_clearance` CAD check tests for dock material within a 1.5 mm zone beneath the lowest modeled adhesive surface at the externally held reference height; an empty result is expected. Other check views test reference-position top/dock overlap, liner/top overlap and depressed jaw/body overlap. These checks do not establish a stable resting position, spring force, physical release, dimensional tolerance, printability or real Flex fit. The approximately 0.036 mm mouth is below typical FDM clearance capability and is likely to fuse: test and calibrate a clamp section before attempting the full print. The flare and internal clearances may need process-specific support planning.

## Requested geometry

| Feature | Mockup dimension / behavior |
| --- | --- |
| Rectangular footprint | 145 x 100 mm, overhanging a nominal 127.76 x 85.48 mm SBS plate |
| Thickness | 40 mm provisional; adjust after measuring BioGripper 2 contact height |
| Outer body edges | 3 mm radius, including corners; overall nominal envelope unchanged |
| Sealing face | 120 x 78 x 0.2 mm registration recess in the underside; release bars retain their original height |
| Slits | Two cuts upward from the sealing face, full 100 mm width, open at both width ends |
| Slit depth | 7.2 mm nominal stop, derived from the assumed tab length and approach |
| Slit position | Inner edge 0.25 mm beyond each end of an assumed 120 mm-long sticky region |
| Nominal insertion channel | 0.65 mm wide, narrowing to a 0.15 mm gripping gap near the mouth |
| Release bars | Two 100 x 6 mm solid bars spanning the full block width, parallel to and entirely inboard of the slits, centered at x = +/-57 mm |
| Released-pressure state | Bars project 0.4 mm from the sealing face toward the plate; jaws normally closed |
| Pressed state | Each bar rises until flush; its jaw moves toward the block center, away from the fixed outer slit wall, to release that tab |
| Independence | Each side has its own bar, jaw and return flexures; no shared linkage |

The rectangular grip surfaces are the block's own ends; there are no added handles or grip pads. The block stays above the plate and need not fit into an SBS nest. The wider body preserves solid material outside the mechanisms. The 145 x 100 x 40 mm choice is provisional, not a verified BioGripper fit. Jaw opening, contact height, local stiffness and grip force need actual gripper dimensions.

## Loaded and unloaded mockups

The optional OpenSCAD views use a blue film with an assumed 120 x 78 mm sealing region and nominal 8.5 mm handling tabs. Tabs bend into the slots against their fixed outer walls and stop at the shortened slot floor. The center follows the shallow registration recess while the ends pass over the release bars. These are illustrative poses, not an elastic simulation. Section and workflow views remove part of the block only for visibility; the STL retains the whole body.

The three-stage comparison shows the loaded block above a plate, both bars pressed flush with the seal against the plate, and an empty raised block with the seal left on the plate and tabs unfolded. These are separately posed states, not a continuous release simulation. The unloaded view does not prove that the tabs clear before the clamps reclose as the block lifts.

The plate is a schematic 96-well proxy with a nominal SBS footprint and a sealing deck 0.2 mm below its perimeter. Solid end regions of that deck support the film beneath the inboard bars. Those heights are chosen to illustrate simultaneous seal and bar contact; they are not measurements of the user's plate. The illustrated film dimensions and tab folds also need checking against the actual seal. The proxy plate and film are preview-only and are not exported with the block STL.

## Rounded Pressing Edges

The intended pressing edge is the long edge, parallel to the 145 mm dimension, at either y end of the block. The main body's outside edges have a 3 mm radius. The release-bar and jaw ends are rounded to match that long-edge profile when both bars are depressed flush. The bars are deepened to retain their full 100 mm end-to-end span above the rounded lower corners; the flat underside contact length is shorter at the end fillets. The central sealing face and internal gripping edges remain flat.

The `edge_press` view shows an illustrative 25-degree rotation about the long axis, with the long edge against the seal and both bars posed flush. It is not a validated robot trajectory or pressure setting. In the relaxed state the rounded bar ends still protrude and can contact first; verify that end loading depresses both bars without twisting or binding. The slots and moving-part gaps interrupt the contact line, so uniform sealing pressure is not established by this mockup. Smooth the printed contact surface and check for film marking, plate support, collision clearance and acceptable sealing force with sacrificial seals. Rounding also reduces the flat area available for gripper contact, which needs checking on the actual hardware.

## Clamp principle

Each underside bar is continuous with its corresponding long jaw on the center-facing side of the slit. Three inclined printed beams attach that jaw to the main block above the slit depth. They are intended to bias the jaw closed and guide it toward the block center when its bar is pushed upward, opening the gap against the fixed outer wall. No linkage crosses the tab insertion path. The slit opens upward from the face: the film tab must bend into it. If a horizontal side-entry slit was intended instead, that is a different geometry.

The untouched nominal gap is 0.15 mm against an assumed 0.2 mm tab, intended to create interference preload. Pressed previews show a 0.4 mm upward bar displacement and a 0.3 mm jaw displacement toward the block center. These are geometric illustration values, not calculated flexure behavior or verified clamping/release performance. The flexible body is not literally solid throughout: small internal clearance pockets and return beams are necessary to let the bars move. The central block and upper region remain solid.

The main slit has a nominal 7.2 mm insertion stop. Jaw clearance is inboard of the insertion channel, with deeper local pockets for the return beams. Thin tabs can bend into unintended cavities; physical insertion needs testing rather than relying on nominal channel dimensions.

## Plate contact

Bar centers are at x = +/-57 mm. Each 6 mm-wide bar spans absolute x = 54 to 60 mm, with a 0.25 mm gap to the inner edge of its slit at absolute x = 60.25 mm. Thus both bars are entirely on the center-facing side of the slots. Pressing moves them a further 0.3 mm toward the center in the posed geometry. Both bars extend from y = -50 to +50 mm, flush with the block's width ends. The portions overhanging the 85.48 mm-wide plate are unsupported; verify adequate supported contact on the actual plate and uniform bar motion rather than assuming contact across the entire 100 mm length.

The bars lie inboard underneath the sealing region and extend beyond the film's width at both ends. Plate pressure is transmitted through the film where covered, with possible direct contact on uncovered plate-rim regions. Confirm that this contact does not crease, mark, puncture or drag the film, and that both bars can reach flush. The real seal dimensions and the BioGripper drawing were not provided.

The underside is intended to press the seal while both bars open their tab clamps. Neither a valid qPCR bond nor a collision-free release motion is demonstrated. If sliding before lifting, both bars must remain depressed until the tabs clear; the plate perimeter alone may not maintain contact through that motion. This model does not quietly reintroduce a release rail or latch to solve that issue.

## STL and printing limits

The top STL is the relaxed, normally closed state, with the plain upper face rotated onto z=0. The slotted/button face points upward for inspection; there are no labels, plates or display boards in the STL. With the raised loading guides removed, the 0.4 mm release-bar protrusions make the total nominal height 40.4 mm. The separate depressed STL has been removed.

The CAD body has no infill lattice or hollow core. Slicer infill is a separate print setting: use 100% infill if the printed body must also be solid, without filling the modeled mechanism clearances.

This is prototype geometry, not an assured working print. A 0.15 mm mouth and internal narrow relief can fuse with FDM; the inclined 0.5 mm beams may be weak, stiff, or unprintable depending on layer orientation, material and nozzle. Do not equate manifold mesh validation with physical printability. Test a section/coupon, adjust clearances, and verify return force before printing or robot-handling the full block. PETG or polypropylene are only materials to investigate, not qualified recommendations.

The thicker outboard grip regions still cannot be assumed to withstand BioGripper loads or isolate the flexures from grip force. Grip location, wall thickness, and flexure isolation must be validated on the actual gripper. Surface finish, cleanliness, film marking, plate support and required sealing pressure also require checks.

Use empty plates and sacrificial seals first. The same geometry cannot be assumed compatible with every SBS plate or qPCR film. The companion dock is a geometric prototype, and no robot program is supplied; previous concept folders are unchanged.