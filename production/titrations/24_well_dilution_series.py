from opentrons import protocol_api


metadata = {
    'protocolName': 'General 24-well 1:1 serial dilution with blank',
    'author': 'Shawn Laursen',
    'description': '''
    Runs 16 independent series across a 384-well plate, each with
    23 sample wells and a diluent-only blank in column 24.
    Each 1:1 sample:diluent transfer halves the concentration.
    Column 1 is undiluted stock; column 23 is stock / 2**22.

    Deck: 300 uL tips in slot 2, Greiner 96-well source plate in slot 4,
    Corning 384-well destination plate in slot 5, NEST reservoir in slot 6.
    P300 multichannel Gen2 mounted on the left.
    Source A1-H1 feeds destination rows A,C,E,G,I,K,M,O.
    Source A2-H2 feeds destination rows B,D,F,H,J,L,N,P.

    At the default rxn_vol = 40, load 100 uL stock in each source well
    (80 uL transferred, 20 uL extra). Load at least 10 mL diluent in
    EACH of reservoir wells A1 and A2, and 2 mL buffer in A12 for the
    column 24 blanks. Fill the blanks first, reusing tips for diluent.
    Each destination well finishes
    with 40 uL, reaching 80 uL during dilution. Mixing uses 40 uL strokes. Excess
    from column 23 is discarded into the fixed trash.''',
    'apiLevel': '2.26'}

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
    global buff, blank_buff
    buff = trough.wells()[:2]
    blank_buff = trough.wells()[-1]

    # volumes
    global rxn_vol, start_vol, mix_vol, mix_repetitions
    rxn_vol = 40
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3

def define_liquids(protocol):
    buff_liquid = protocol.define_liquid(
        name='Diluent',
        description='Load 10 mL in each reservoir well A1 and A2.',
        display_color='#00BFFF')
    for well in buff:
        well.load_liquid(liquid=buff_liquid, volume=10000)

    blank_liquid = protocol.define_liquid(
        name='Blank buffer',
        description='Load 2 mL buffer in reservoir well A12 for column 24.',
        display_color='#00BFFF')
    blank_buff.load_liquid(liquid=blank_liquid, volume=2000)

    for sample_column in samples.columns()[:2]:
        for well in sample_column:
            sample_liquid = protocol.define_liquid(
                name=f'Sample {well.well_name}',
                description=(f'Undiluted stock in {well.well_name}; load '
                             f'{start_vol + 20} uL ({start_vol} uL transferred, 20 uL extra).'),
                display_color='#FF6B6B')
            well.load_liquid(liquid=sample_liquid, volume=start_vol + 20)

def add_buff(protocol):
    rows = [0,1]

    p300m.pick_up_tip()
    p300m.transfer(rxn_vol, blank_buff, [plate.rows()[row][23] for row in rows], new_tip='never')
    for row, buff_well in zip(rows, buff):
        p300m.transfer(rxn_vol, buff_well, plate.rows()[row][1:23], new_tip='never')
    p300m.drop_tip()

def add_samples_and_titrate(protocol):
    rows = [0,1]
    sample_cols = [0,1]

    for row, sample_col in zip(rows, sample_cols):
        dilution_wells = plate.rows()[row][:23]
        p300m.pick_up_tip()
        p300m.transfer(start_vol, samples.rows()[0][sample_col], dilution_wells[0], new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            p300m.transfer(rxn_vol, source, destination, mix_before=(mix_repetitions,mix_vol), new_tip='never')
        p300m.mix(mix_repetitions,mix_vol, dilution_wells[-1])
        p300m.aspirate(rxn_vol, dilution_wells[-1])
        p300m.dispense(rxn_vol, protocol.fixed_trash)
        p300m.drop_tip()