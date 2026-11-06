from opentrons import protocol_api


metadata = {
    'protocolName': 'Metal dilution series - 8 proteins in quadruplicate',
    'author': 'Shawn Laursen',
    'description': '''
    8 proteins, quadruplicate, 20uL/well, 5uM protein in every well.
    Metal: 11 concentrations at 1.5-fold steps (1000 to 17.34153uM) + zero control.
    Proteins 1-8: row pairs A/B, C/D, E/F, G/H, I/J, K/L, M/N, O/P.
    Series: columns 1-12 and 13-24, zero metal in columns 12/24.

    LOAD:
    - Slot 4 Greiner A1-H1: proteins 1-8, 200uL/well at 50uM.
    - Slot 6 trough A1: 12mL matching protein buffer.
    - Slot 6 trough A2: 2mL of 10mM Tb in matching buffer.
    - Slot 3 NEST deep-well, slot 4 columns 2-3 and slot 5 Corning 384: empty.
    Robot prepares 1000uL/well of protein diluent in slot 3 column 1.
    OT-2, P300 multichannel Gen2 left, 300uL tips in slot 2, 80 tips used.''',
    'apiLevel': '2.28'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    prepare_mixes(protocol)
    add_samples_and_titrate(protocol)
    protocol.set_rail_lights(False)


def setup(protocol):
    global tips300, proteins, samples, plate, trough, p300m
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    proteins = protocol.load_labware('nest_96_wellplate_2ml_deep', 3)
    samples = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6, label='trough')
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    global rxn_vol, dilution_vol, transfer_vol, start_vol, mix_vol, mix_repetitions, series_groups
    rxn_vol = 20
    dilution_vol = rxn_vol
    transfer_vol = 2 * dilution_vol
    start_vol = dilution_vol + transfer_vol
    mix_vol = transfer_vol
    mix_repetitions = 3
    series_groups = [(0, 0), (1, 0), (0, 12), (1, 12)]


def define_liquids(protocol):
    for protein_index, well in enumerate(samples.columns()[0]):
        protein_number = protein_index + 1
        destination_rows = 'ABCDEFGHIJKLMNOP'[protein_index * 2:protein_index * 2 + 2]
        protein_liquid = protocol.define_liquid(
            name=f'Protein {protein_number}',
            description=(f'50uM protein stock for rows {destination_rows}. '
                         'Load 200uL in slot 4 column 1, 140uL used. Robot dilutes to 5uM.'),
            display_color='#E69F00')
        well.load_liquid(liquid=protein_liquid, volume=200)
    buffer_liquid = protocol.define_liquid(
        name='Buffer',
        description='Matching protein buffer. Load 12mL in trough A1, 9.76mL used.',
        display_color='#0072B2')
    trough['A1'].load_liquid(liquid=buffer_liquid, volume=12000)
    metal_liquid = protocol.define_liquid(
        name='Tb stock',
        description='10mM Tb in matching buffer. Load 2mL in trough A2, 320uL used.',
        display_color='#009E73')
    trough['A2'].load_liquid(liquid=metal_liquid, volume=2000)


def prepare_mixes(protocol):
    p300m.pick_up_tip()
    p300m.transfer(900, trough['A1'], proteins['A1'], new_tip='never')
    p300m.transfer(160, trough['A1'], samples.rows()[0][1:3], new_tip='never')
    p300m.drop_tip()

    p300m.pick_up_tip()
    p300m.transfer(100, samples['A1'], proteins['A1'],
                   mix_before=(mix_repetitions, 160),
                   mix_after=(mix_repetitions, 300), new_tip='never')
    p300m.drop_tip()

    for sample in samples.rows()[0][1:3]:
        p300m.pick_up_tip()
        p300m.transfer(20, samples['A1'], sample, new_tip='never')
        p300m.drop_tip()
        p300m.pick_up_tip()
        p300m.transfer(20, trough['A2'], sample, mix_after=(mix_repetitions, 160), new_tip='never')
        p300m.drop_tip()


def add_samples_and_titrate(protocol):
    for row, first_column in series_groups:
        destinations = [well.bottom(1) for well in plate.rows()[row][first_column + 1:first_column + 12]]
        dilution_wells = plate.rows()[row][first_column:first_column + 11]
        sample = samples.rows()[0][first_column // 12 + 1]
        protein_source = proteins['A1']
        p300m.pick_up_tip()
        p300m.mix(mix_repetitions, 300, protein_source)
        p300m.distribute(dilution_vol, protein_source, destinations,
                         disposal_volume=0, new_tip='never')
        p300m.transfer(start_vol, sample, dilution_wells[0],
                       mix_before=(mix_repetitions, start_vol), new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            p300m.transfer(transfer_vol, source, destination, mix_before=(mix_repetitions, mix_vol), new_tip='never')
        p300m.mix(mix_repetitions, mix_vol, dilution_wells[-1])
        p300m.aspirate(transfer_vol, dilution_wells[-1])
        p300m.dispense(transfer_vol, protocol.fixed_trash)
        p300m.drop_tip()