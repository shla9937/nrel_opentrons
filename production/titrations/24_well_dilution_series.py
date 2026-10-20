from opentrons import protocol_api


metadata = {
    'protocolName': 'UV metal titration',
    'author': 'Shawn Laursen',
    'description': '''
    384-well titration, 40 uL/well: Mn A-C, Zn D-F, Gd G-I, Lu J-L, Ca M-O.
    Columns 1-22: twofold metal dilutions from 5 mM, constant 5 uM protein.
    Column 23: protein only. 
    Column 24: protein-free buff.
    Source A1-H1: Mn, Mn, Zn, Gd, Gd, Lu, Ca, Ca.
    Source A2-H2: Mn, Zn, Zn, Gd, Lu, Lu, Ca, protein.
    Load 120 uL/source: 5 mM metal + 5 uM protein; H2: 5 uM protein only.
    Reservoir A1/A2: 20 mL protein each (5 uM, no metal).
    Reservoir A12: 10 mL buff (matching buffer, no protein or metal).
    Slots: tips 2, Greiner sources 4, Corning 384 plate 5, reservoir 6.
    P300 multichannel Gen2, left. Peak well volume: 80 uL.
    Analyse with --metals Mn Zn Gd Lu Ca --zero-metal-column 23.
    P1-P23: protein only; P24: buff. Row P is not included in default analysis.''',
    'apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_buff(protocol)
    add_samples_and_titrate(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global tips300, samples, plate, trough, p300m
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    samples = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    # reagents
    global protein, buff
    protein = trough.wells()[:2]
    buff = trough.wells()[-1]

    # volumes
    global rxn_vol, start_vol, mix_vol, mix_repetitions
    rxn_vol = 40
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3

def define_liquids(protocol):
    protein_liquid = protocol.define_liquid(
        name='protein',
        description='5 uM protein, no metal. Load 10 mL in each reservoir well A1 and A2.',
        display_color='#E69F00')
    for well in protein:
        well.load_liquid(liquid=protein_liquid, volume=10000)

    buff_liquid = protocol.define_liquid(
        name='buff',
        description='No protein or metal. Load 2 mL matching base buffer in A12 for column 24.',
        display_color='#0072B2')
    buff.load_liquid(liquid=buff_liquid, volume=2000)

    metal_colors = {
        'Mn': '#D62728',
        'Zn': '#009E73',
        'Gd': '#7B2CBF',
        'Lu': '#CC79A7',
        'Ca': '#00CED1',
    }
    row_conditions = ['Mn'] * 3 + ['Zn'] * 3 + ['Gd'] * 3 + ['Lu'] * 3 + ['Ca'] * 3 + ['protein']
    for column_index, sample_column in enumerate(samples.columns()[:2]):
        for row_index, well in enumerate(sample_column):
            destination_row = row_index * 2 + column_index
            condition = row_conditions[destination_row]
            if condition == 'protein':
                well.load_liquid(liquid=protein_liquid, volume=start_vol + 20)
                continue
            composition = f'5 mM {condition} + 5 uM protein'
            sample_liquid = protocol.define_liquid(
                name=f'{condition} for row {"ABCDEFGHIJKLMNOP"[destination_row]}',
                description=(f'{composition} in {well.well_name}; load '
                             f'{start_vol + 20} uL ({start_vol} uL transferred, 20 uL extra).'),
                display_color=metal_colors[condition])
            well.load_liquid(liquid=sample_liquid, volume=start_vol + 20)

def add_buff(protocol):
    rows = [0,1]

    p300m.pick_up_tip()
    p300m.transfer(rxn_vol, buff, [plate.rows()[row][23] for row in rows], new_tip='never')
    for row, protein_well in zip(rows, protein):
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