from opentrons import protocol_api


metadata = {
    'protocolName': 'Metal dilution series - 8 proteins in quadruplicate',
    'author': 'Shawn Laursen',
    'description': '''
    8 proteins, quadruplicate, 40uL/well, 5uM protein in every well.
    Metal: 11 concentrations at 1.5-fold steps (1000 to 17.34153uM) + zero control.
    Proteins 1-8: row pairs A/B, C/D, E/F, G/H, I/J, K/L, M/N, O/P.
    Series: columns 1-12 and 13-24, zero metal in columns 12/24.

    LOAD:
    - Slot 3 NEST deep-well A1-H1: proteins 1-8, 300uL/well at 50uM.
    - Slot 6 trough A1: 10mL matching protein buffer.
    - Slot 6 trough A2: 12mL matching protein buffer.
    - Slot 6 trough A3: 2mL of 10mM metal in matching buffer.
    - Slot 3 columns 2-3, slot 4 Greiner and slot 5 Corning 384: empty.
    Robot prepares 1000uL/well of protein diluent in slot 3 columns 2-3.
    OT-2, P300 multichannel Gen2 left, 300uL tips in slot 2, 88 tips used.''',
    'apiLevel': '2.28'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    prepare_mixes(protocol)
    add_samples_and_titrate(protocol)
    top_up_proteins(protocol)
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
    rxn_vol = 40
    dilution_vol = rxn_vol / 2
    transfer_vol = 2 * dilution_vol
    start_vol = dilution_vol + transfer_vol
    mix_vol = transfer_vol
    mix_repetitions = 3
    series_groups = [(0, 0), (1, 0), (0, 12), (1, 12)]


def define_liquids(protocol):
    for protein_index, well in enumerate(proteins.columns()[0]):
        protein_number = protein_index + 1
        destination_rows = 'ABCDEFGHIJKLMNOP'[protein_index * 2:protein_index * 2 + 2]
        protein_liquid = protocol.define_liquid(
            name=f'Protein {protein_number}',
            description=(f'50uM protein stock for rows {destination_rows}. '
                         'Load 300uL, 240uL used. Robot dilutes to 5uM.'),
            display_color='#E69F00')
        well.load_liquid(liquid=protein_liquid, volume=300)
    buffer_liquid = protocol.define_liquid(
        name='Buffer',
        description='Matching protein buffer. Trough A1: 10 mL; A2: 12 mL.',
        display_color='#0072B2')
    trough['A1'].load_liquid(liquid=buffer_liquid, volume=10000)
    trough['A2'].load_liquid(liquid=buffer_liquid, volume=12000)
    metal_liquid = protocol.define_liquid(
        name='Metal stock',
        description='10 mM metal in matching buffer. Load 2 mL in trough A3; 640 uL used.',
        display_color='#009E73')
    trough['A3'].load_liquid(liquid=metal_liquid, volume=2000)


def prepare_mixes(protocol):
    p300m.pick_up_tip()
    p300m.transfer(900, trough['A1'], proteins['A2'], new_tip='never')
    p300m.transfer(900, trough['A2'], proteins['A3'], new_tip='never')
    p300m.transfer(140, trough['A2'], samples.rows()[0][:2], new_tip='never')
    p300m.drop_tip()

    p300m.pick_up_tip()
    p300m.mix(mix_repetitions, 200, proteins['A1'])
    p300m.distribute(100, proteins['A1'], [proteins['A2'].top(), proteins['A3'].top()],
                     disposal_volume=0, new_tip='never')
    for destination in proteins.rows()[0][1:3]:
        p300m.mix(mix_repetitions, 300, destination)
    p300m.drop_tip()

    for sample in samples.rows()[0][:2]:
        p300m.pick_up_tip()
        p300m.transfer(20, proteins['A1'], sample, new_tip='never')
        p300m.drop_tip()
        p300m.pick_up_tip()
        p300m.transfer(40, trough['A3'], sample, mix_after=(mix_repetitions, 160), new_tip='never')
        p300m.drop_tip()


def add_samples_and_titrate(protocol):
    for row, first_column in series_groups:
        destinations = plate.rows()[row][first_column + 1:first_column + 12]
        dilution_wells = plate.rows()[row][first_column:first_column + 11]
        sample = samples.rows()[0][first_column // 12]
        protein_source = proteins.rows()[0][first_column // 12 + 1]
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


def top_up_proteins(protocol):
    p300m.pick_up_tip()
    for row, first_column in series_groups:
        destinations = [well.top() for well in plate.rows()[row][first_column:first_column + 12]]
        protein_source = proteins.rows()[0][first_column // 12 + 1]
        p300m.mix(mix_repetitions, 300, protein_source)
        p300m.distribute(rxn_vol - dilution_vol, protein_source, destinations,
                         disposal_volume=0, new_tip='never')
    p300m.drop_tip()