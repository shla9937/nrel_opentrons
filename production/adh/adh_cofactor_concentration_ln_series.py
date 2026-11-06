from opentrons import protocol_api


metadata = {
    'protocolName': 'ADH cofactor concentration + Ln dilution series - Flex',
    'author': 'Shawn Laursen',
    'description': '''
    One ADH protein, final cofactor 1-9uM in 1uM steps, three Ln series each,
    plus five series at 0uM cofactor. Each series: 11 twofold Ln dilutions
    (100 to 0.09765625uM final) plus a zero-Ln well.
    Series 1-16: rows A-P, columns 1-12, 17-32: rows A-P, columns 13-24.
    Series 1-3: 1uM cofactor, 4-6: 2uM, ... 25-27: 9uM, 28-32: 0uM.
    Final: 60uL/well = 30uL prepared mix + 30uL ADH, 1uM ADH throughout.
    Automatically prepares 2x cofactor mixes, start D2 and B3 plates EMPTY.

    LOAD (final stock concentrations and total volumes, including all additions):
        - C1 trough A1, 12mL: 100mM MES, pH 6, 200uM PQQ, 20mM EtOH, 300uM DCPIP, 2mM PMS
        - C1 trough A2, 12mL: 100mM MES, pH 6, 200uM PQQ, 20mM EtOH, 300uM DCPIP, 2mM PMS
        - C1 trough A3, 14mL: 100mM MES, pH 6, 200uM PQQ, 20mM EtOH, 300uM DCPIP, 2mM PMS, 20uM PedG
        - C1 trough A4, 3mL: 100mM MES, pH 6, 200uM PQQ, 20mM EtOH, 300uM DCPIP, 2mM PMS, 2mM Ln
        - B2 reservoir A1, 50mL: 100mM MES, pH 6, 2uM ADH
    - D2, B3 and C2 plates: empty.
    Minimum reagent transfer 30uL, prepares 600uL/mix in D2 and 300uL in B3.
    Tips: C3 single-nozzle and A1 column racks WITHOUT adapters, D3 full-head
    rack WITH adapter. All racks 1000uL, 189 tips used. Pauses before ADH addition.'''}

requirements = {'robotType': 'Flex', 'apiLevel': '2.29'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    prepare_cofactor_mixes(protocol)
    add_samples_and_titrate(protocol)
    add_ADH(protocol)
    protocol.set_rail_lights(False)


def setup(protocol):
    global tips_columns, tips_96, tips_single, cofactors, samples, plate, enzyme, trough, trash, pipette
    tips_columns = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips_96 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3', adapter='opentrons_flex_96_tiprack_adapter')
    tips_single = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'C3')
    cofactors = protocol.load_labware('nest_96_wellplate_2ml_deep', 'D2')
    samples = protocol.load_labware('greiner_96_wellplate_323ul', 'B3')
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 'C2')
    enzyme = protocol.load_labware('nest_1_reservoir_195ml', 'B2')
    trough = protocol.load_labware('nest_12_reservoir_15ml', 'C1', label='trough')
    trash = protocol.load_trash_bin('D1')
    pipette = protocol.load_instrument('flex_96channel_1000')
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start='H12', tip_racks=[tips_single])

    global rxn_vol, start_vol, mix_vol, mix_repetitions, enzyme_volume, series_groups, cofactor_concentrations
    rxn_vol = 30
    start_vol = 2 * rxn_vol
    mix_vol = rxn_vol
    mix_repetitions = 3
    enzyme_volume = 30
    series_groups = [(0, 0), (1, 0), (0, 12), (1, 12)]
    cofactor_concentrations = [concentration for concentration in range(1, 10) for replicate in range(3)] + [0] * 5

    global cofactor_stock_concentration, ln_stock_concentration, source_ln_concentration, cofactor_prep_volume, sample_prep_volume
    cofactor_stock_concentration = 20
    ln_stock_concentration = 2000
    source_ln_concentration = 200
    cofactor_prep_volume = 600
    sample_prep_volume = 300


def define_liquids(protocol):
    buffer_liquid = protocol.define_liquid(
        name='MES assay mix',
        description='100 mM MES, pH 6 + 200 uM PQQ + 20 mM EtOH + 300 uM DCPIP + 2 mM PMS. No cofactor, Ln or ADH. Load 12 mL total each in C1 A1 and A2.',
        display_color='#9CA3AF')
    for well in trough.wells()[:2]:
        well.load_liquid(liquid=buffer_liquid, volume=12000)
    cofactor_liquid = protocol.define_liquid(
        name='Cofactor stock',
        description=f'{cofactor_stock_concentration} uM cofactor + 200 uM PQQ + 20 mM EtOH + 300 uM DCPIP + 2 mM PMS in 100 mM MES, pH 6. No Ln or ADH. Load 14 mL total in C1 A3.',
        display_color='#D81B60')
    trough['A3'].load_liquid(liquid=cofactor_liquid, volume=14000)
    ln_liquid = protocol.define_liquid(
        name='Ln stock',
        description=f'{ln_stock_concentration} uM Ln + 200 uM PQQ + 20 mM EtOH + 300 uM DCPIP + 2 mM PMS in 100 mM MES, pH 6. No cofactor or ADH. Load 3 mL total in C1 A4.',
        display_color='#FFB000')
    trough['A4'].load_liquid(liquid=ln_liquid, volume=3000)
    enzyme_liquid = protocol.define_liquid(
        name='ADH',
        description='2 uM ADH in 100 mM MES, pH 6; no PQQ, EtOH, DCPIP, PMS, Ln or cofactor. 1 uM ADH final. Load 50 mL.',
        display_color='#0072B2')
    enzyme['A1'].load_liquid(liquid=enzyme_liquid, volume=50000)


def prepare_cofactor_mixes(protocol):
    preparations = []
    for column_index, (row_offset, first_column) in enumerate(series_groups):
        for row_index in range(8):
            series_index = (column_index // 2) * 16 + row_index * 2 + row_offset
            source_cofactor = cofactor_concentrations[series_index] * (rxn_vol + enzyme_volume) / rxn_vol
            for labware, volume, ln_concentration in [(cofactors, cofactor_prep_volume, 0),
                                                       (samples, sample_prep_volume, source_ln_concentration)]:
                destination = labware.columns()[column_index][row_index]
                cofactor_volume = source_cofactor * volume / cofactor_stock_concentration
                ln_volume = ln_concentration * volume / ln_stock_concentration
                buffer_volume = volume - cofactor_volume - ln_volume
                if any(amount != 0 and not 30 <= amount <= 1000
                       for amount in (buffer_volume, cofactor_volume, ln_volume)):
                    raise ValueError('Preparation transfers must be zero or between 30 and 1000 uL.')
                preparations.append((destination, trough.wells()[column_index // 2],
                                     buffer_volume, cofactor_volume, ln_volume, volume))

    pipette.pick_up_tip()
    for destination, buffer, buffer_volume, cofactor_volume, ln_volume, volume in preparations:
        if buffer_volume > 0:
            pipette.transfer(buffer_volume, buffer, destination.top(),
                             mix_before=(mix_repetitions, 300), new_tip='never')
    pipette.drop_tip()

    pipette.pick_up_tip()
    for destination, buffer, buffer_volume, cofactor_volume, ln_volume, volume in preparations:
        if cofactor_volume > 0 and ln_volume > 0:
            pipette.transfer(cofactor_volume, trough['A3'], destination.top(),
                             mix_before=(mix_repetitions, 300), new_tip='never')
    pipette.drop_tip()

    for destination, buffer, buffer_volume, cofactor_volume, ln_volume, volume in preparations:
        if ln_volume > 0 or cofactor_volume == 0:
            continue
        pipette.pick_up_tip()
        pipette.transfer(cofactor_volume, trough['A3'], destination,
                         mix_before=(mix_repetitions, 300),
                         mix_after=(mix_repetitions, min(300, volume * 0.8)), new_tip='never')
        pipette.drop_tip()
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN, start='A12', tip_racks=[tips_columns])
    ln_volume = source_ln_concentration * sample_prep_volume / ln_stock_concentration
    for destination in samples.rows()[0][:len(series_groups)]:
        pipette.pick_up_tip()
        pipette.transfer(ln_volume, trough['A4'], destination,
                         mix_before=(mix_repetitions, min(300, sample_prep_volume * 0.8)),
                         mix_after=(mix_repetitions, min(300, sample_prep_volume * 0.8)), new_tip='never')
        pipette.drop_tip()


def add_samples_and_titrate(protocol):
    for column_index, (row, first_column) in enumerate(series_groups):
        destinations = plate.rows()[row][first_column + 1:first_column + 12]
        dilution_wells = plate.rows()[row][first_column:first_column + 11]
        pipette.pick_up_tip()
        pipette.mix(mix_repetitions, min(300, cofactor_prep_volume * 0.8), cofactors.rows()[0][column_index])
        pipette.distribute(rxn_vol, cofactors.rows()[0][column_index], destinations,
                           disposal_volume=0, new_tip='never')
        pipette.transfer(start_vol, samples.rows()[0][column_index], dilution_wells[0],
                 mix_before=(mix_repetitions, min(300, sample_prep_volume * 0.8)), new_tip='never')
        for source, destination in zip(dilution_wells[:-1], dilution_wells[1:]):
            pipette.transfer(rxn_vol, source, destination, mix_before=(mix_repetitions, mix_vol), new_tip='never')
        pipette.mix(mix_repetitions, mix_vol, dilution_wells[-1])
        pipette.aspirate(rxn_vol, dilution_wells[-1])
        pipette.dispense(rxn_vol, trash)
        pipette.drop_tip()


def add_ADH(protocol):
    protocol.pause('Dilutions complete: 30 uL per well, no ADH added. Resume when ready to initiate the reaction with 30 uL ADH per well (1 uM ADH final).')
    pipette.configure_nozzle_layout(style=protocol_api.ALL, start='A1', tip_racks=[tips_96])
    pipette.pick_up_tip()
    destinations = [plate[well] for well in ['A1', 'A2', 'B2', 'B1']]
    total_volume = enzyme_volume * len(destinations) + 20
    pipette.mix(mix_repetitions, 300, enzyme['A1'].bottom(1))
    pipette.aspirate(total_volume, enzyme['A1'].bottom(1))
    for destination in destinations:
        pipette.dispense(enzyme_volume, destination.top(z=-1))
    pipette.blow_out(trash)
    pipette.drop_tip()