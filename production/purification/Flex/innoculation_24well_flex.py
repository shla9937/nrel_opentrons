from opentrons import protocol_api


metadata = {
    'protocolName': 'Innoculation - 24well culture',
    'author': 'Shawn Laursen',
    'description': 'Reconstitute DNA, transform cells in a chilled PCR plate, and inoculate 24 well cultures.'}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="constructs",
        display_name="Number of constructs",
        description="Number of constructs to test",
        default=24,
        minimum=1,
        maximum=24,
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
    global trash, pipette, tips1000, tip_order, single_tip, expression_plate, twist_plate, tubes, water_res, media, temp_mod, temp_plate, twist_start_well, twist_end_well, constructs, media_vol
    global tips1000_media, tips1000_column, empty_tiprack, tips24_adapter, single_nozzle, single_tiprack
    constructs = protocol.params.constructs
    twist_start_well = protocol.params.twist_start_well - 1
    twist_end_well = twist_start_well + constructs - 1
    if not 1 <= constructs <= 24:
        raise ValueError('Construct count must be between 1 and 24.')
    if twist_start_well < 0 or twist_end_well > 95:
        raise ValueError('Selected DNA wells must lie within wells 1 to 96.')
    media_vol = 5000

    tips1000_column = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    media = protocol.load_labware('omega_1_reservoir_600ml', 'A2')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A3')
    tips1000_media = tips24_adapter.load_labware('opentrons_flex_96_tiprack_1000ul', label='Empty media-tip pickup rack')

    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1', label='Empty 24-tip staging rack')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B2')
    water_res = protocol.load_labware('nest_12_reservoir_15ml', 'B3')

    temp_mod = protocol.load_module('temperature module gen2', 'C1')
    temp_mod.start_set_temperature(4)
    temp_plate = temp_mod.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')
    twist_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C2')
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 'C3')

    trash = protocol.load_trash_bin('D1')
    expression_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D2')

    pipette = protocol.load_instrument('flex_96channel_1000')
    single_nozzle = "A1"
    single_tiprack = tips1000
    tip_order = [well for row in reversed(tips1000.rows()) for well in reversed(row)]
    single_tip = 0

def define_liquids(protocol):
    cells = protocol.define_liquid(
        name="Isothermal comp cells",
        description="1500ul per stock tube",
        display_color="#D59227")
    tubes.wells()[0].load_liquid(liquid=cells, volume=1500)

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
    media.wells()[0].load_liquid(liquid=auto_tb, volume=24 * media_vol + 20000)

    dna = protocol.define_liquid(
        name="DNA",
        description="Selected constructs",
        display_color="#27D435")
    for well in range(twist_start_well, twist_end_well + 1):
        twist_plate.wells()[well].load_liquid(liquid=dna, volume=0 if protocol.params.recon_dna else 50)

def pickup_tips(protocol):
    global single_tip
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start=single_nozzle, tip_racks=[single_tiprack])
    pipette.pick_up_tip(tip_order[single_tip])
    single_tip += 1

def add_cells(protocol):
    pickup_tips(protocol)
    destinations = temp_plate.wells()[twist_start_well:twist_end_well + 1]
    pipette.distribute(50, tubes.wells()[0], destinations, new_tip="never", mix_before=(1, 25), disposal_volume=0)
    pipette.drop_tip()

def add_dna(protocol):
    columns = []
    singles = []
    well = twist_start_well
    while well <= twist_end_well:
        if well % 8 == 0 and well + 7 <= twist_end_well:
            columns.append(well)
            well += 8
        else:
            singles.append(well)
            well += 1

    for well in singles:
        pickup_tips(protocol)
        if protocol.params.recon_dna is True:
            pipette.transfer(50, water_res['A1'], twist_plate.wells()[well], new_tip="never", mix_after=(3, 25))
        pipette.transfer(5, twist_plate.wells()[well], temp_plate.wells()[well], new_tip='never', mix_after=(3, 25))
        pipette.drop_tip()

    for column, well in enumerate(columns):
        pipette.configure_nozzle_layout(style=protocol_api.COLUMN, start="A1", tip_racks=[tips1000_column])
        pipette.pick_up_tip(tips1000_column.columns()[11 - column][0])
        if protocol.params.recon_dna is True:
            pipette.transfer(50, water_res['A1'], twist_plate.wells()[well], new_tip="never", mix_after=(3, 25))
        pipette.transfer(5, twist_plate.wells()[well], temp_plate.wells()[well], new_tip='never', mix_after=(3, 25))
        pipette.drop_tip()

def add_media(protocol):
    global single_nozzle, single_tiprack, tip_order, single_tip
    protocol.move_labware(tips1000_column, 'D3', use_gripper=True)
    protocol.move_labware(tips1000_media, 'A1', use_gripper=True)
    pickup_24(protocol)
    pipette.transfer(media_vol, media.wells()[0], expression_plate.wells()[0], new_tip='never')
    pipette.drop_tip()
    single_nozzle = "H12"
    single_tiprack = empty_tiprack
    tip_order = [well for row in empty_tiprack.rows()[::2] for well in row[6:]]
    single_tip = 0

def pickup_24(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ROW, start="H1", tip_racks=[tips1000])
    for row in range(4):
        pipette.pick_up_tip()
        pipette.drop_tip(empty_tiprack.rows()[row*2][0])

    pipette.configure_nozzle_layout(style=protocol_api.COLUMN, start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col])
        pipette.drop_tip(tips1000_media.rows()[0][col*2])

    protocol.move_labware(tips1000_media, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_media.rows()[0][0])

def inoculate(protocol):
    for culture_well, well in enumerate(range(twist_start_well, twist_end_well + 1)):
        pickup_tips(protocol)
        pipette.transfer(50, temp_plate.wells()[well], expression_plate.wells()[culture_well], new_tip='never', mix_after=(3, 100))
        pipette.drop_tip()