from opentrons import protocol_api


metadata = {
    'protocolName': 'ADH cofactor + Ln dilution series - Flex',
    'author': 'Shawn Laursen',
    'description': '''
    32 protein mixes, each with 11 twofold La dilutions (100 to 0.09765625 uM
    final) plus a zero-La, matching-protein control.
    Mixes 1-16: rows A-P, columns 1-12; mixes 17-32: rows A-P, columns 13-24.
    Final: 60 uL/well = 30 uL prepared mix + 30 uL ADH; 1 uM ADH.
    Other proteins: 2-fold dilution overall; load at 2x final concentration
    in BOTH La-free and La-containing mixes to keep protein constant.
    Load D2: 600 uL/well La-free mix; C3: 100 uL/well matching mix + 200 uM La.
    Load B2: 50 mL of 2 uM ADH. Full 96-channel head adds ADH to all wells.'''}

requirements = {'robotType': 'Flex', 'apiLevel': '2.29'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_protein_mixes(protocol)
    add_samples_and_titrate(protocol)
    add_ADH(protocol)
    protocol.set_rail_lights(False)


def setup(protocol):
    global tips_columns, tips_96, proteins, samples, plate, enzyme, trash, pipette
    tips_columns = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A2')
    tips_96 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A3', adapter='opentrons_flex_96_tiprack_adapter')
    proteins = protocol.load_labware('nest_96_wellplate_2ml_deep', 'D2')
    samples = protocol.load_labware('greiner_96_wellplate_323ul', 'C3')
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 'C2')
    enzyme = protocol.load_labware('nest_1_reservoir_195ml', 'B2')
    trash = protocol.load_trash_bin('D1')
    pipette = protocol.load_instrument('flex_96channel_1000')
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN, start='A12', tip_racks=[tips_columns])

    global rxn_vol, start_vol, mix_vol, mix_repetitions, enzyme_volume, series_groups
    rxn_vol = 30
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3
    enzyme_volume = 30
    series_groups = [(0, 0), (1, 0), (0, 12), (1, 12)]


def define_liquids(protocol):
    for column_index, protein_column in enumerate(proteins.columns()[:4]):
        row_offset, first_column = series_groups[column_index]
        for row_index, well in enumerate(protein_column):
            protein_number = (column_index // 2) * 16 + row_index * 2 + row_offset + 1
            destination_row = 'ABCDEFGHIJKLMNOP'[row_index * 2 + row_offset]
            destination = f'{destination_row}{first_column + 1}-{destination_row}{first_column + 12}'
            protein_liquid = protocol.define_liquid(
                name=f'Protein mix {protein_number}',
                description=(f'La-free mix for {destination}. All proteins at 2x final '
                             'concentration; no ADH. Load 600 uL; 330 uL used.'),
                display_color='#E69F00')
            well.load_liquid(liquid=protein_liquid, volume=600)
            sample_liquid = protocol.define_liquid(
                name=f'La + protein mix {protein_number}',
                description=(f'200 uM La plus SAME 2x protein mix for {destination}; '
                             'no ADH. Load 100 uL; 60 uL used.'),
                display_color='#009E73')
            samples.columns()[column_index][row_index].load_liquid(
                liquid=sample_liquid, volume=100)
    enzyme_liquid = protocol.define_liquid(
        name='ADH',
        description='2 uM ADH in matching buffer; 30 uL into 30 uL gives 1 uM final. Load 50 mL.',
        display_color='#4169E1')
    enzyme['A1'].load_liquid(liquid=enzyme_liquid, volume=50000)


def add_protein_mixes(protocol):
    for column_index, (row, first_column) in enumerate(series_groups):
        destinations = plate.rows()[row][first_column + 1:first_column + 12]
        pipette.pick_up_tip()
        pipette.transfer(rxn_vol, proteins.rows()[0][column_index], destinations, new_tip='never')
        pipette.drop_tip()


def add_samples_and_titrate(protocol):
    for column_index, (row, first_column) in enumerate(series_groups):
        dilution_wells = plate.rows()[row][first_column:first_column + 11]
        pipette.pick_up_tip()
        pipette.transfer(start_vol, samples.rows()[0][column_index], dilution_wells[0], new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            pipette.transfer(rxn_vol, source, destination, mix_before=(mix_repetitions, mix_vol), new_tip='never')
        pipette.mix(mix_repetitions, mix_vol, dilution_wells[-1])
        pipette.aspirate(rxn_vol, dilution_wells[-1])
        pipette.dispense(rxn_vol, trash)
        pipette.drop_tip()


def add_ADH(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ALL, start='A1', tip_racks=[tips_96])
    pipette.pick_up_tip()
    destinations = [plate[well] for well in ['A1', 'A2', 'B2', 'B1']]
    total_volume = enzyme_volume * len(destinations) + 20
    pipette.aspirate(total_volume, enzyme['A1'].bottom(1))
    for destination in destinations:
        pipette.dispense(enzyme_volume, destination.top(z=-1))
    pipette.blow_out(trash)
    pipette.drop_tip()