# nrel_opentrons

This repository is all of Shawn Laursen's scripts for Opentrons robots at NREL.

## Flex 96-well inoculation

[innoculation_96well_flex.py](production/purification/Flex/innoculation_96well_flex.py) is a standalone protocol using the Flex 96-channel head, chilled PCR plate and NEST 96-well 2 mL culture plate. Select the DNA start well, construct count and reconstitution setting at runtime. Well numbering is column-wise: A1=1, B1=2, H1=8, A2=9. Selections cannot extend beyond H12.

### Transfer modes

- **96 constructs:** direct full-rack pickup on the A3 adapter. DNA reconstitution, DNA transfer and inoculation each treat the whole plate simultaneously. Fresh racks are preloaded in A4 and C4 and automatically moved onto A3 before media and inoculation. Four gripper moves replace both spent racks; there are no manual refill pauses.
- **48-95 constructs:** the robot prepares the selected tip pattern automatically, using columns and edge singles, then picks it up with `ALL`. Each liquid-handling step treats all selected wells together, including shifted selections. Fresh patterns are prepared for DNA, media and inoculation.
- **1-47 constructs:** the existing column/single-tip DNA and inoculation workflow remains. Media uses the selected tips together.

Cell distribution uses one tip across all stock tubes, discarding it only after all selected PCR wells receive cells. A separate stock tube supplies each batch of up to 24 constructs; all tubes should contain the same cell suspension. Tip staging is still required for partial plates because the API has no native half-plate nozzle layout.

### Starting deck

| Slot | Labware |
| --- | --- |
| A1 | Full Flex 1000 uL column-tip rack for fewer than 96 constructs; empty for 96 |
| A2 | Empty parking position |
| A3 | Flex tip-rack adapter; full 1000 uL rack for 96 constructs, physically empty pickup rack otherwise |
| A4 | Full Flex 1000 uL spare rack when at least five complete DNA columns are selected |
| B1 | Additional Omega 600 mL water reservoir for 96 constructs; empty otherwise |
| B2 | Full Flex 1000 uL single-tip rack, without an adapter |
| B3 | NEST 12-channel 15 mL water reservoir for 1-47 constructs; empty for larger runs |
| B4 | Additional Omega 600 mL water reservoir for 48-95 constructs; unused otherwise |
| C1 | Temperature module with `opentrons_96_aluminumblock_biorad_wellplate_200ul` |
| C2 | Greiner 96-well 300 uL DNA plate |
| C3 | Opentrons 24-position Eppendorf 1.5 mL snap-cap tube rack; cell stocks |
| C4 | Second full Flex 1000 uL spare rack when at least nine complete DNA columns are selected |
| D1 | Trash bin; no waste chute required |
| D2 | NEST 96-well 2 mL deep-well culture plate |
| D3 | Omega 600 mL media reservoir |
| D4 | Empty parking position for the first spent tip rack |

Install/configure the column-four staging fixtures used by the selected layout, including D4 whenever a spare rack is loaded. Leave D4 empty initially. For 48-95 constructs, B4 holds water, which moves B4 -> B1 only after the DNA tip pattern is prepared, then returns to B4 after DNA transfer. No pipetting occurs in staging slots and no gripper moves occur with tips attached. Culture and media stay in D2 and D3 for all runs of 48 or more constructs.

Full 96-well runs start with full racks in A3, A4, C4 and B2. The B2 rack supplies the single cell-dispensing tip. Before media, the gripper moves the spent A3 rack to D4 and the fresh A4 rack onto A3. Before inoculation, it moves the spent A3 rack to the now-empty A4 and the fresh C4 rack onto A3.

For other counts, the protocol preloads only the required column-tip spares. Each complete selected DNA column needs three sets of eight tips across DNA, media and inoculation: up to four columns need no spare, five to eight need A4, and nine to twelve need both A4 and C4. Column-tip racks are swapped automatically at their current pickup position, using D4 first and then the vacated spare slot for spent racks. The original B2 rack has enough single tips for cells and all edge wells. No rack is refilled or reset in software. Do not prefill the empty pickup rack: it must contain only the tips staged by the protocol.

For fewer than 48 constructs, the existing clearance moves remain: media may park in A2 for DNA edge transfers, and tip racks swap positions for column handling. After media addition, culture moves to B1, media to D2 and the single-tip rack to D3; the column-tip rack moves through B2 and A1 for inoculation.

### Liquids and mapping

- Load 1500 uL cells per stock tube: A1 for samples 1-24, B1 for 25-48, C1 for 49-72 and D1 for 73-96. These are sample numbers within the selected range, not absolute DNA well numbers. Half plates use two tubes; full plates use four.
- With reconstitution enabled, load **30 mL water in the additional Omega reservoir for 48-96 constructs**, or **10 mL in NEST reservoir channel A1 for 1-47 constructs**. The full-width Omega allows simultaneous aspiration. Do not substitute the 12-channel reservoir in the large-run layout. With reconstitution off, DNA wells are assumed to contain 50 uL hydrated DNA each.
- Load media at 1 mL per selected construct plus a 20 mL reservoir allowance: 68 mL for 48 constructs or 116 mL for 96. Confirm water and media loading allowances against actual reservoir dead volume and aspiration height.
- PCR wells start empty. The protocol waits for 4 C, then distributes 50 uL cells per selected well, with a small source mix and no disposal volume. Reconstitution adds 50 uL water per DNA well; 5 uL DNA is transferred to each matching PCR position.
- DNA, PCR and culture positions match exactly. Sparse `ALL` pickup retains the selected positions; unselected wells are not pipetted. Inoculation transfers 50 uL per culture well, giving 1050 uL final volume. There is no additional incubation or heat-shock step.

Import the Greiner and Omega definitions from [custom_labware](custom_labware). Eleven representative Opentrons 10.0.0/API 2.28 simulations passed, including full/half plates, shifted ranges and small-run rack swaps. A tip-inventory model checked all 9312 valid start/count/reconstitution combinations using only preloaded racks, verifying selected positions, fresh tips, slot occupancy and gripper timing. These checks do not establish physical clearance, sparse pickup or liquid-handling performance: perform a supervised dry run, especially for staged rack swaps, partial racks and the water reservoir.

## Flex 24-well base

Load the 24-well base script's media reservoir in **D4**, with the D4 staging fixture installed and **D3 initially empty**. The gripper moves it to D3 after DNA addition and before media-tip pickup, clearing the single-nozzle approach to the DNA plate in C2. Verify filled-reservoir handling and pickup clearance with a supervised dry run.

The separate 24-well base is [innoculation_flex.py](production/purification/Flex/innoculation_flex.py), adapted to a PCR plate with rows A/C/E/G and columns 1/3/5/7/9/11 for its 24-tip arrangement. It is not changed by the 96-well acceleration. The experimental [innoculation_24well_flex.py](production/purification/Flex/innoculation_24well_flex.py) is not the current 24-well base; the 96-well loading instructions above do not apply to either 24-well script.