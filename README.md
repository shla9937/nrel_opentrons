# nrel_opentrons

This repository is all of Shawn Laursen's scripts for Opentrons robots at NREL.

## Flex PCR-plate inoculation

Both standalone protocols use a chilled 96-well PCR plate, the Flex 96-channel head and gripper:

- [innoculation_24well_flex.py](production/purification/Flex/innoculation_24well_flex.py): Thomson 24-well culture, up to 24 constructs, 5 mL media per well using `pickup_24`, and sequential single-tip inoculation.
- [innoculation_96well_flex.py](production/purification/Flex/innoculation_96well_flex.py): NEST 96-well 2 mL culture, up to 96 constructs, 1 mL media per selected well using the staged tip pattern, and position-matched column/edge inoculation.

The original [innoculation_flex.py](production/purification/Flex/innoculation_flex.py) with the 24-well temperature block is unchanged. Neither new script requires the other file to run.

Choose the script for your culture plate before uploading. Select the DNA start well, construct count and reconstitution setting at runtime; there is no culture-format parameter. Well numbering is column-wise: A1=1, B1=2, H1=8, A2=9. Selections cannot extend beyond H12.

### Starting deck

| Slot | Labware |
| --- | --- |
| A1 | Full Flex 1000 uL column-tip rack, without an adapter |
| A2 | Empty; receives the media reservoir later |
| A3 | Flex tip-rack adapter with an entirely empty media-tip pickup rack |
| B1 | Entirely empty Flex 1000 uL staging rack for 24-well culture; leave empty for 96-well culture |
| B2 | Full Flex 1000 uL tip rack for single-tip pickup and 24-tip preparation, without an adapter |
| B3 | NEST 12-channel 15 mL reservoir; water in A1 |
| C1 | Temperature module with the 96-well aluminium block and Bio-Rad 200 uL PCR plate |
| C2 | Greiner 96-well 300 uL DNA plate |
| C3 | Opentrons 24-position Eppendorf 1.5 mL snap-cap tube rack; cell stocks |
| D1 | Trash bin; stays here throughout the run |
| D2 | Thomson 24-well 10400 uL culture plate or NEST 96-well 2 mL deep-well culture plate |
| D3 | Empty for 24-well culture; Omega 600 mL media reservoir for 96-well culture |
| D4 | Omega 600 mL media reservoir for 24-well culture; unused for 96-well culture |

All required racks and the adapter are on deck from the beginning. There is no separate media-tip donor rack and no planned off-deck loading. The 24-well script needs two full boxes (A1 for DNA columns and B2 for singles/media preparation) and two empty racks, with no refill. The 96-well script retains its column-tip refill prompts. The gripper moves labware to maintain pipette clearance; do not rearrange it manually.

For the 24-well script, install and configure the staging-area fixture providing D4 before loading the protocol. Fourth-column slots are gripper-accessible staging positions, not pipetting positions. The reservoir moves to A2 before aspiration; the column-tip rack moves to D4 only after its last pickup.

The empty pickup rack on the A3 adapter and the 24-well staging rack in B1 must physically contain no tips. The protocol uses explicit locations to stage sparse media-tip patterns rather than automatic tip tracking in these racks.

In the 24-well script, single tips are taken from B2 starting at H12 and proceeding backwards across each row, preserving the top four rows for `pickup_24`. Cells and incomplete DNA columns use single tips. Complete DNA columns use direct eight-tip pickup from the full rack in A1, consuming columns from right to left with the A1 nozzle column. There is no DNA-tip reformatting. Both DNA reconstitution and transfer into the matching PCR column use those eight tips. At 24 constructs, 73 tips are consumed across the two boxes: one for cells, 24 for DNA, 24 for media and 24 for inoculation.

In the 96-well script, DNA edge wells are handled before full columns. When needed, the media reservoir temporarily parks in A2 during edge transfers; for column transfers, the single-tip rack parks in A2 and the column-tip rack moves to B2. Both return to their starting locations after DNA addition.

In the 24-well script, the media reservoir starts in D4, leaving A2 clear throughout DNA handling. After DNA addition, the reservoir moves to A2, the column-tip rack moves from A1 to the now-empty D4, and the empty media-tip pickup rack moves from the A3 adapter to A1. The original `pickup_24` row-to-column sequence uses the untouched upper rows of the single-tip rack and prepares the pickup rack in A1, then moves it back onto the A3 adapter. For 96-well media, the pickup rack moves to B1 while selected columns and edge tips are staged from the existing supplies, then returns to the adapter. Both formats use `ALL` for final media-tip pickup and dispensing.

The 24-well workflow has four gripper moves, with only one move of the filled reservoir. The staging rack stays in B1 and the culture plate stays in D2, including during inoculation. The staging rack's untouched tips in rows A, C, E and G, columns 7-12, supply single-tip inoculation; the single-tip donor rack remains in B2. These tips were only relocated, never used for liquid handling.

After 96-well media addition, the culture plate moves to B1, media to D2 and the single-tip rack to D3. The column-tip rack parks in B2 for single-tip inoculation and moves to A1 before column inoculation. No gripper moves occur with pipette tips attached. A full 96-construct run uses three full column-tip racks in total, including the starting rack, plus the starting single-tip rack; replacement racks are needed only at refill prompts.

Use the exact PCR plate/block combination defined by `opentrons_96_aluminumblock_biorad_wellplate_200ul`, not an arbitrary PCR plate with different geometry. Import the Greiner, Thomson (for 24-well culture) and Omega definitions from [custom_labware](custom_labware).

### Liquid loading and mapping

- Load 1500 uL cells per stock tube: A1 for constructs 1-24, B1 for 25-48, C1 for 49-72 and D1 for 73-96. These are construct numbers within the selected range, not absolute DNA well numbers.
- With reconstitution enabled, load 10 mL water into reservoir channel A1. Otherwise, the selected DNA wells are assumed to contain 50 uL hydrated DNA each.
- Load 140 mL media for 24-well culture: all 24 wells receive 5 mL, even with fewer constructs. For 96-well culture, load the construct count times 1 mL plus a 20 mL reservoir allowance; only selected wells receive media. Confirm the allowance is adequate for the physical reservoir and aspiration height.
- The PCR plate starts empty. The 24-well script starts cooling to 4 C asynchronously without waiting; pre-chill if the cells require a cold plate on arrival. The 96-well script waits for 4 C. `distribute` delivers 50 uL cells to each matching DNA position, mixing the source once at 25 uL before each aspiration, with no disposal volume or destination mixing during cell dispensing. Reconstitution adds 50 uL water per DNA well, then 5 uL DNA transfers into the matching PCR well.
- Both scripts use eight tips for complete DNA columns and individual tips at the edges. No unselected PCR or DNA wells are used.
- All culture media is added before inoculation, using the 24-tip pattern or the selected 96-well tip pattern in one head pickup. For 24-well inoculation, single tips map selected PCR wells sequentially into A1, B1, C1, D1, A2, etc. For 96-well inoculation, matching well positions are retained using columns and edge singles.
- Inoculum volume is 50 uL per culture well, giving 5050 uL total in the 24-well plate or 1050 uL in the 96-well plate. No additional incubation or heat-shock step is included.

Simulated with Opentrons 10.0.0 at API 2.28, including both culture formats, mid-column selections, the final plate wells, reconstitution off and a full 96-construct run. Earlier simulations did not flag the reservoir's reported physical obstruction, so simulation alone does not establish physical clearance or sparse-tip pickup. Confirm the pickup paths, staged tip patterns, labware offsets, gripper handling (including the filled reservoir) and liquid behaviour with a supervised dry run before using cells or DNA.