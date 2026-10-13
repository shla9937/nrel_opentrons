from opentrons import protocol_api


metadata = {
    'protocolName': 'Innoculation - 96well culture',
    'author': 'Shawn Laursen',
    'description': 'Reconstitute DNA, transform cells in a chilled PCR plate, and inoculate 96 well cultures.'}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="constructs",
        display_name="Number of constructs",
        description="Number of constructs to test",
        default=24,
        minimum=1,
        maximum=96,
        unit="constructs")
    parameters.add_int(
        variable_name="twist_start_well",
        display_name="Twist start well",
        description="First DNA well: A1=1, B1=2, H1=8, A2=9",
        default=1,
        minimum=1,
        maximum=96,
        unit="well")
    parameters.add_bool(
        variable_name="recon_dna",
        display_name="Reconstitute DNA?",
        description="On = add water to DNA, Off = DNA already has water",
        default=True)

def run(protocol):
    setup(protocol)
    protocol.set_rail_lights(True)
    define_liquids(protocol)
    temp_mod.await_temperature(4)
    add_cells(protocol)
    add_dna(protocol)
    add_media(protocol)
    inoculate(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global trash, pipette, tips1000, tips1000_column, tip_order, single_tip, column_tip, expression_plate, twist_plate, tubes, water_res, media, temp_mod, temp_plate, twist_start_well, twist_end_well, constructs, media_vol, transfer_groups
    global tips1000_media, tips96_adapter, single_nozzle, column_nozzle, column_tip_order
    constructs = protocol.params.constructs
    twist_start_well = protocol.params.twist_start_well - 1
    twist_end_well = twist_start_well + constructs - 1
    transfer_groups = plan_transfers(protocol.params.twist_start_well, constructs)
    media_vol = 1000

    tips1000_column = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips96_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A3')
    tips1000_media = tips96_adapter.load_labware('opentrons_flex_96_tiprack_1000ul', label='Empty media-tip pickup rack')

    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B2')
    water_res = protocol.load_labware('nest_12_reservoir_15ml', 'B3')

    temp_mod = protocol.load_module('temperature module gen2', 'C1')
    temp_mod.start_set_temperature(4)
    temp_plate = temp_mod.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')
    twist_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C2')
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 'C3')

    trash = protocol.load_trash_bin('D1')
    expression_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 'D2')
    media = protocol.load_labware('omega_1_reservoir_600ml', 'D3')

    pipette = protocol.load_instrument('flex_96channel_1000')
    single_nozzle = "A1"
    column_nozzle = "A1"
    tip_order = [well for row in reversed(tips1000.rows()) for well in reversed(row)]
    column_tip_order = [column[0] for column in reversed(tips1000_column.columns())]
    single_tip = 0
    column_tip = 0

def define_liquids(protocol):
    cells = protocol.define_liquid(
        name="Isothermal comp cells",
        description="1500ul per stock tube",
        display_color="#D59227")
    for stock in range((constructs + 23) // 24):
        tubes.wells()[stock].load_liquid(liquid=cells, volume=1500)

    water = protocol.define_liquid(
        name="DEPC water",
        description="water",
        display_color="#4054B9")
    if protocol.params.recon_dna is True:
        water_res['A1'].load_liquid(liquid=water, volume=10000)

    auto_tb = protocol.define_liquid(
        name="Auto TB",
        description="Auto TB + metals + glycerol + AMP",
        display_color="#DFEB36")
    media.wells()[0].load_liquid(liquid=auto_tb, volume=constructs * media_vol + 20000)

    dna = protocol.define_liquid(
        name="DNA",
        description="Selected constructs",
        display_color="#27D435")
    for well in range(twist_start_well, twist_end_well + 1):
        twist_plate.wells()[well].load_liquid(liquid=dna, volume=0 if protocol.params.recon_dna else 50)

def pickup_tips(protocol, channels):
    global single_tip, column_tip, tip_order, column_tip_order
    if channels == 8:
        pipette.configure_nozzle_layout(style=protocol_api.COLUMN, start=column_nozzle, tip_racks=[tips1000_column])
        if column_tip == len(column_tip_order):
            protocol.pause(f'Replace the column-tip rack in {tips1000_column.parent} with a full 1000ul rack, without an adapter, then resume.')
            tips1000_column.reset()
            columns = reversed(tips1000_column.columns()) if column_nozzle == "A1" else tips1000_column.columns()
            column_tip_order = [column[0] for column in columns]
            column_tip = 0
        pipette.pick_up_tip(column_tip_order[column_tip])
        column_tip += 1
    else:
        pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start=single_nozzle, tip_racks=[tips1000])
        if single_tip == len(tip_order):
            protocol.pause(f'Replace the single-tip rack in {tips1000.parent} with a full 1000ul rack, without an adapter, then resume.')
            tips1000.reset()
            tip_order = ([well for row in reversed(tips1000.rows()) for well in reversed(row)] if single_nozzle == "A1"
                         else [well for row in tips1000.rows() for well in row])
            single_tip = 0
        pipette.pick_up_tip(tip_order[single_tip])
        single_tip += 1

def add_cells(protocol):
    for offset in range(0, constructs, 24):
        pickup_tips(protocol, 1)
        destinations = temp_plate.wells()[twist_start_well + offset:min(twist_start_well + offset + 24, twist_end_well + 1)]
        pipette.distribute(50, tubes.wells()[offset // 24], destinations, new_tip="never", mix_before=(1, 25), disposal_volume=0)
        pipette.drop_tip()

def add_dna(protocol):
    column_setup = False
    media_parked = any(channels == 1 for well, channels in transfer_groups)
    if media_parked is True:
        protocol.move_labware(media, 'A2', use_gripper=True)
    for well, channels in sorted(transfer_groups, key=lambda group: group[1]):
        if channels == 8 and column_setup is False:
            if media_parked is True:
                protocol.move_labware(media, 'D3', use_gripper=True)
                media_parked = False
            protocol.move_labware(tips1000, 'A2', use_gripper=True)
            protocol.move_labware(tips1000_column, 'B2', use_gripper=True)
            column_setup = True
        pickup_tips(protocol, channels)
        if protocol.params.recon_dna is True:
            pipette.transfer(50, water_res['A1'], twist_plate.wells()[well], new_tip="never", mix_after=(3, 25))
        pipette.transfer(5, twist_plate.wells()[well], temp_plate.wells()[well], new_tip='never', mix_after=(3, 25))
        pipette.drop_tip()
    if media_parked is True:
        protocol.move_labware(media, 'D3', use_gripper=True)
    if column_setup is True:
        protocol.move_labware(tips1000_column, 'A1', use_gripper=True)
        protocol.move_labware(tips1000, 'B2', use_gripper=True)

def add_media(protocol):
    global single_nozzle, tip_order, single_tip, column_nozzle, column_tip_order, column_tip
    protocol.move_labware(tips1000_media, 'B1', use_gripper=True)
    pickup_96(protocol)
    pipette.transfer(media_vol, media.wells()[0], expression_plate.wells()[0], new_tip='never')
    pipette.drop_tip()
    protocol.move_labware(expression_plate, 'B1', use_gripper=True)
    protocol.move_labware(media, 'D2', use_gripper=True)
    protocol.move_labware(tips1000, 'D3', use_gripper=True)
    protocol.move_labware(tips1000_column, 'B2', use_gripper=True)
    single_nozzle = "H12"
    tip_order = [well for row in tips1000.rows() for well in row if well.has_tip]
    single_tip = 0
    column_nozzle = "A12"
    column_tip_order = [column[0] for column in tips1000_column.columns() if all(well.has_tip for well in column)]
    column_tip = 0

def pickup_96(protocol):
    column_setup = any(channels == 8 for well, channels in transfer_groups)
    if column_setup is True:
        protocol.move_labware(tips1000, 'A2', use_gripper=True)
        protocol.move_labware(tips1000_column, 'B2', use_gripper=True)
    for well, channels in transfer_groups:
        if channels == 8:
            pickup_tips(protocol, 8)
            pipette.drop_tip(tips1000_media.wells()[well])

    if column_setup is True:
        protocol.move_labware(tips1000_column, 'A1', use_gripper=True)
        protocol.move_labware(tips1000, 'B2', use_gripper=True)
    for well, channels in transfer_groups:
        if channels == 1:
            pickup_tips(protocol, 1)
            pipette.drop_tip(tips1000_media.wells()[well])

    protocol.move_labware(tips1000_media, tips96_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_media.rows()[0][0])

def inoculate(protocol):
    column_setup = False
    for well, channels in sorted(transfer_groups, key=lambda group: group[1]):
        if channels == 8 and column_setup is False:
            protocol.move_labware(tips1000_column, 'A1', use_gripper=True)
            column_setup = True
        pickup_tips(protocol, channels)
        pipette.transfer(50, temp_plate.wells()[well], expression_plate.wells()[well], new_tip='never', mix_after=(3, 100))
        pipette.drop_tip()

def plan_transfers(start_well, constructs):
    if not 1 <= constructs <= 96:
        raise ValueError('Construct count must be between 1 and 96.')
    if start_well < 1 or start_well + constructs - 1 > 96:
        raise ValueError('Selected DNA wells must lie within wells 1 to 96.')
    groups = []
    well_index = start_well - 1
    end_index = well_index + constructs
    while well_index < end_index:
        channels = 8 if well_index % 8 == 0 and end_index - well_index >= 8 else 1
        groups.append((well_index, channels))
        well_index += channels
    return groups