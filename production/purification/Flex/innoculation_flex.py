from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Innoculation - 24well',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 24 well plate using StrepXT mag beads'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="constructs",
        display_name="Number of constructs",
        description="Number of constructs to test",
        default=96,
        minimum=1,
        maximum=96,
        unit="constructs")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    rack_24well(protocol)
    define_liquids(protocol)
    for plate in range(num_plates):
        twist_start_well = plate * 24
        twist_end_well = min(twist_start_well + 24, protocol.params.constructs)
        add_cells(plate, twist_start_well, twist_end_well, protocol)
        add_dna(plate, twist_start_well, twist_end_well, protocol)
        add_media(plate, protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, tips200, empty_tiprack, tips1000_24well, tips24_adapter, expression_plates, twist_plate, tubes, media, num_plates
    # A row
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A2')

    # B row
    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    media = protocol.load_labware('nest_1_reservoir_195ml', 'B2')
    tips200 = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'B3')

    # C row
    twist_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C1')
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 'C3')

    # D row
    trash = protocol.load_trash_bin ('D1') 
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
   
    pipette = protocol.load_instrument('flex_96channel_1000')

    num_plates = math.ceil(protocol.params.constructs / 24)
    expression_plates = [protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', ['A4', 'B4', 'C4', 'D4'][i])
        for i in range(num_plates)]

def define_liquids(protocol):
    water = protocol.define_liquid(
        name="DEPC water",
        description="water",
        display_color="#4054B9")
    for well in tubes.wells()[0:num_plates]:
        well.load_liquid(liquid=water,volume=2000)

    cells = protocol.define_liquid(
        name="Isothermal comp cells",
        description="comp cells",
        display_color="#D59227")
    for well in tubes.wells()[4:num_plates+4]:
        well.load_liquid(liquid=cells,volume=2000)

    auto_tb = protocol.define_liquid(
        name="Auto TB",
        description="Auto TB + metals + glycerol + AMP",
        display_color="#DFEB36")
    media.wells()[0].load_liquid(liquid=auto_tb, volume=195000)

def rack_24well(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000])
    for row in range(4):
        pipette.pick_up_tip()
        pipette.drop_tip(empty_tiprack.rows()[row*2][0])

    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col])
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    protocol.move_labware(labware=tips1000,new_location='A1',use_gripper=True)

def add_cells(plate, twist_start_well, twist_end_well, protocol):
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start="A1", tip_racks=[empty_tiprack])
    cells_lc = protocol.get_liquid_class("glycerol_50")
    protocol.move_labware(labware=expression_plates[plate],new_location='C2',use_gripper=True)
    pipette.distribute_with_liquid_class(cells_lc, 50, tubes.wells()[plate+4], expression_plates[plate].wells()[0:twist_end_well - twist_start_well], new_tip="once")

def add_dna(plate, twist_start_well, twist_end_well, protocol):
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start="A12", tip_racks=[tips200])
    for well in range(twist_start_well, twist_end_well):
        pipette.pick_up_tip()
        pipette.transfer(50, tubes.wells()[plate], twist_plate.wells()[well], new_tip="never")
        pipette.transfer(5, twist_plate.wells()[well], expression_plates[plate].wells()[0:twist_end_well - twist_start_well], new_tip='never', mix_before=(5, 25), mix_after=(3, 25))
        pipette.drop_tip()

def add_media(plate, protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])

    pipette.transfer(5000, media.wells()[0], expression_plates[plate].wells()[0].top(), new_tip='never')
    if plate == (num_plates-1):
        pipette.drop_tip()
    else:
        pipette.return_tip()

    protocol.move_labware(labware=expression_plates[plate],new_location=['A4', 'B4', 'C4', 'D4'][plate],use_gripper=True)