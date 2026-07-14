from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Magnetic purification - 24well',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 24 well plate using StrepXT mag beads'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    pickup_24(protocol)
    fill_24well(protocol)
    # lyse(protocol)
    # wash(protocol)
    # elute(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, mid_tips1000, tips1000_24well, tips24_adapter, buff, plate
    trash = protocol.load_trash_bin ('A3')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B3')
    mid_tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D1')
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D2')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'C3')
    pipette = protocol.load_instrument('flex_96channel_1000', tip_racks=[tips1000])
    buff = protocol.load_labware('nest_1_reservoir_195ml', 'A1')
    plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'B1')

def define_liquids(protocol):
    buffer_liquid = protocol.define_liquid(
        name="Buff",
        description="Buffer mixture",
        display_color="#50C878")
    buff['A1'].load_liquid(liquid=buffer_liquid,volume=195000)

# def pickup_tips(layout, racks, protocol):
#     if racks is None:
#         racks = [tips1000, tips1000_2, tips1000_3, tips1000_4]
#     else:
#         racks = [racks]
#     if layout == 'column':
#         pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12", tip_racks=racks)   
#     elif layout == 'row':
#         pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=racks)
#     elif layout == 'single':
#         pipette.configure_nozzle_layout(style=protocol_api.SINGLE,start="H12",tip_racks=racks)
#     elif layout == 'all':
#         pipette.configure_nozzle_layout(style=protocol_api.ALL,start="A1",tip_racks=racks)
#     else:
#         raise ValueError("Invalid layout. Choose from 'column', 'row', 'single', or 'all'.")
#     pipette.pick_up_tip()

def pickup_24(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000])
    for row in range(4):
        pipette.pick_up_tip()
        pipette.drop_tip(mid_tips1000.rows()[row*2][0])
    
    mid_tips1000.reset()
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12",tip_racks=[mid_tips1000])
    for col in range(6):
        pipette.pick_up_tip()
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    tips1000_24well.reset()
    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL,tip_racks=[tips1000_24well])
    pipette.pick_up_tip()

def fill_24well(protocol):
    pipette.transfer(50, buff.wells()[0], plate.wells()[0], new_tip='never')
    pipette.drop_tip()