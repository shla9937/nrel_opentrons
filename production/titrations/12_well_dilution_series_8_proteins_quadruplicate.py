from opentrons import protocol_api


metadata = {
    'protocolName': 'Metal dilution series - 8 proteins in quadruplicate',
    'author': 'Shawn Laursen',
    'description': '''
    Eight proteins, four independent 11+1 metal series each; 40 uL/well.
    Final protein: 100 nM in EVERY well, including the zero-metal controls.
    Metal: 11 twofold concentrations from 1000 to 0.9765625 uM, then zero.
    Proteins 1-8 occupy row pairs A/B, C/D, E/F, G/H, I/J, K/L, M/N, O/P.
    Each row has series in columns 1-12 and 13-24; columns 12/24 are zero metal.
    Slot 3, NEST deep-well A1-H1: load 500 uL/well of proteins 1-8 at 1 uM,
    no metal; 240 uL/well used. Leave deep-well column 2 and Greiner slot 4 EMPTY.
    Slot 6 trough: A1 10 mL buffer; A2 12 mL SAME buffer; A3 2 mL of 10 mM metal.
    Robot prepares 100 nM protein diluent in deep-well A2-H2 and matching
    100 nM protein + 1 mM metal mixtures in Greiner columns 1 and 2.
    OT-2: P300 multichannel Gen2 left; tips slot 2, Corning 384 plate slot 5.
    Uses 88 tips; peak destination volume 80 uL. No subsequent ADH addition.''',
    'apiLevel': '2.28'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    prepare_mixes(protocol)
    add_proteins(protocol)
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

    global rxn_vol, start_vol, mix_vol, mix_repetitions, series_groups
    rxn_vol = 40
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3
    series_groups = [(0, 0), (1, 0), (0, 12), (1, 12)]


def define_liquids(protocol):
    for protein_index, well in enumerate(proteins.columns()[0]):
        protein_number = protein_index + 1
        destination_rows = 'ABCDEFGHIJKLMNOP'[protein_index * 2:protein_index * 2 + 2]
        protein_liquid = protocol.define_liquid(
            name=f'Protein {protein_number}',
            description=(f'1 uM protein stock, no metal, for rows {destination_rows}. '
                         'Load 500 uL; 240 uL used. Robot dilutes to 100 nM.'),
            display_color='#E69F00')
        well.load_liquid(liquid=protein_liquid, volume=500)
    buffer_liquid = protocol.define_liquid(
        name='Buffer',
        description='Matching protein buffer, no protein or metal. Trough A1: 10 mL; A2: 12 mL.',
        display_color='#0072B2')
    trough['A1'].load_liquid(liquid=buffer_liquid, volume=10000)
    trough['A2'].load_liquid(liquid=buffer_liquid, volume=12000)
    metal_liquid = protocol.define_liquid(
        name='Metal stock',
        description='10 mM metal in matching buffer, no protein. Load 2 mL in trough A3; 320 uL used.',
        display_color='#009E73')
    trough['A3'].load_liquid(liquid=metal_liquid, volume=2000)


def prepare_mixes(protocol):
    p300m.pick_up_tip()
    p300m.transfer(900, trough['A1'], proteins['A2'], new_tip='never')
    p300m.transfer(900, trough['A2'], proteins['A2'], new_tip='never')
    p300m.transfer(160, trough['A2'], samples.rows()[0][:2], new_tip='never')
    p300m.drop_tip()

    p300m.pick_up_tip()
    p300m.transfer(200, proteins['A1'], proteins['A2'], mix_after=(mix_repetitions, 300), new_tip='never')
    p300m.drop_tip()

    for sample in samples.rows()[0][:2]:
        p300m.pick_up_tip()
        p300m.transfer(20, proteins['A1'], sample, new_tip='never')
        p300m.drop_tip()
        p300m.pick_up_tip()
        p300m.transfer(20, trough['A3'], sample, mix_after=(mix_repetitions, 160), new_tip='never')
        p300m.drop_tip()


def add_proteins(protocol):
    p300m.pick_up_tip()
    for row, first_column in series_groups:
        destinations = plate.rows()[row][first_column + 1:first_column + 12]
        p300m.transfer(rxn_vol, proteins['A2'], destinations, new_tip='never')
    p300m.drop_tip()


def add_samples_and_titrate(protocol):
    for row, first_column in series_groups:
        dilution_wells = plate.rows()[row][first_column:first_column + 11]
        sample = samples.rows()[0][first_column // 12]
        p300m.pick_up_tip()
        p300m.transfer(start_vol, sample, dilution_wells[0], new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            p300m.transfer(rxn_vol, source, destination, mix_before=(mix_repetitions, mix_vol), new_tip='never')
        p300m.mix(mix_repetitions, mix_vol, dilution_wells[-1])
        p300m.aspirate(rxn_vol, dilution_wells[-1])
        p300m.dispense(rxn_vol, protocol.fixed_trash)
        p300m.drop_tip()