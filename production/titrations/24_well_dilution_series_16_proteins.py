from opentrons import protocol_api


metadata = {
    'protocolName': 'Terbium TRF 24 well dilution series',
    'author': 'Shawn Laursen',
    'description': '''
    One metal titrated into 16 proteins, one protein per 384-well row A-P.
    Final volume: 40 uL/well; constant 5 uM protein in columns 1-23.
    Columns 1-22: twofold metal dilutions from 5 mM.
    Column 23: matching protein only. Column 24: protein-free buffer.
    Protein sources: NEST 96-well 2 mL deep-well plate in slot 3.
    A1-H1: proteins 1, 3, 5, 7, 9, 11, 13, 15 -> rows A,C,E,G,I,K,M,O.
    A2-H2: proteins 2, 4, 6, 8, 10, 12, 14, 16 -> rows B,D,F,H,J,L,N,P.
    Load 1200 uL/well of 5 uM protein, no metal; 880 uL/well used.
    Starting mixtures: Greiner 96-well plate in slot 4, same well mapping.
    Load 100 uL/well of 5 mM metal + the matching 5 uM protein.
    Prepare these mixtures manually using the SAME metal in all 16 wells.
    Reservoir A12: 2 mL matching buffer, no protein or metal.
    Slots: tips 2, proteins 3, starting mixtures 4, Corning 384 plate 5,
    reservoir 6. P300 multichannel Gen2, left; 40 tips used.
    Peak destination well volume: 80 uL. No replicate rows.''',
    'apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_buff(protocol)
    add_samples_and_titrate(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global tips300, proteins, samples, plate, trough, p300m
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    proteins = protocol.load_labware('nest_96_wellplate_2ml_deep', 3)
    samples = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    global protein, buff
    protein = proteins.rows()[0][:2]
    buff = trough.wells()[-1]

    global rxn_vol, start_vol, mix_vol, mix_repetitions
    rxn_vol = 40
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3

def define_liquids(protocol):
    buff_liquid = protocol.define_liquid(
        name='buff',
        description='No protein or metal. Load 2 mL matching base buffer in A12.',
        display_color='#0072B2')
    buff.load_liquid(liquid=buff_liquid, volume=2000)

    for column_index, protein_column in enumerate(proteins.columns()[:2]):
        for row_index, well in enumerate(protein_column):
            protein_number = row_index * 2 + column_index + 1
            destination_row = 'ABCDEFGHIJKLMNOP'[protein_number - 1]
            protein_liquid = protocol.define_liquid(
                name=f'Protein {protein_number}',
                description=(f'5 uM protein {protein_number}, no metal, for row '
                             f'{destination_row}. Load 1200 uL in {well.well_name} '
                             'of the deep-well plate; 880 uL transferred.'),
                display_color='#E69F00')
            well.load_liquid(liquid=protein_liquid, volume=1200)
            sample_liquid = protocol.define_liquid(
                name=f'Metal + protein {protein_number}',
                description=(f'5 mM metal + 5 uM protein {protein_number}, for row '
                             f'{destination_row}. Load {start_vol + 20} uL in '
                             f'{well.well_name} of the Greiner plate; '
                             f'{start_vol} uL transferred.'),
                display_color='#009E73')
            samples.columns()[column_index][row_index].load_liquid(
                liquid=sample_liquid, volume=start_vol + 20)

def add_buff(protocol):
    rows = [0,1]

    p300m.pick_up_tip()
    p300m.transfer(rxn_vol, buff, [plate.rows()[row][23] for row in rows], new_tip='never')
    p300m.drop_tip()
    for row, protein_well in zip(rows, protein):
        p300m.pick_up_tip()
        p300m.transfer(rxn_vol, protein_well, plate.rows()[row][1:23], new_tip='never')
        p300m.drop_tip()

def add_samples_and_titrate(protocol):
    rows = [0,1]
    sample_cols = [0,1]

    for row, sample_col in zip(rows, sample_cols):
        dilution_wells = plate.rows()[row][:22]
        p300m.pick_up_tip()
        p300m.transfer(start_vol, samples.rows()[0][sample_col], dilution_wells[0], new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            p300m.transfer(rxn_vol, source, destination, mix_before=(mix_repetitions,mix_vol), new_tip='never')
        p300m.mix(mix_repetitions,mix_vol, dilution_wells[-1])
        p300m.aspirate(rxn_vol, dilution_wells[-1])
        p300m.dispense(rxn_vol, protocol.fixed_trash)
        p300m.drop_tip()