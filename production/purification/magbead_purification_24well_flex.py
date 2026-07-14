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
    wash(protocol)
    # elute(protocol)
    # cleanup(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, tips1000_1, empty_tiprack, tips1000_24well, tips24_adapter, buff, plate, mag_24well
    trash = protocol.load_trash_bin ('A3')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D1')
    tips1000_1 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D2')
    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A2')
    pipette = protocol.load_instrument('flex_96channel_1000')
    buff = protocol.load_labware('nest_1_reservoir_195ml', 'B3')
    mag_24well = protocol.load_adapter('shawn_24well_magnet_adapter', 'C2')
    plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'B2')

def define_liquids(protocol):
    buffer_liquid = protocol.define_liquid(
        name="Buff",
        description="Buffer mixture",
        display_color="#50C878")
    buff['A1'].load_liquid(liquid=buffer_liquid,volume=195000)

def pickup_24(protocol):
    global half_filled
    half_filled = False
    try:
        protocol.move_labware(tips1000_24well, "A1", use_gripper=True)
    except:
        None

    if half_filled is False:
        pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000, tips1000_1])
        for row in range(4):
            pipette.pick_up_tip()
            pipette.drop_tip(empty_tiprack.rows()[row*2][0])
        half_filled = True
    else:    
        half_filled = False

    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col])
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])
    
def fill_24well(protocol):
    pickup_24(protocol)
    pipette.transfer(50, buff.wells()[0], plate.wells()[0], new_tip='never')
    pipette.drop_tip()

def wash(protocol):
    fill_24well(protocol)
    protocol.move_labware(plate, mag_24well, use_gripper=True)

    # remove supernatant 
    # for sample_well in range(0,24):
    #     p1000.transfer(1500, well24.wells()[sample_well].bottom(3), deep_well.wells()[sample_well], mix_before=(3,500))
    
    # p1000.move_to(deep_well.wells()[sample_well].top(10))
    # mag_mod.engage(height_from_base=mag_height)
    # protocol.delay(seconds=mag_time)

    # for sample_well in range(0,24): 
    #     find_offset(sample_well)
    #     p1000.transfer(1500, pickup_pos, well24.wells()[sample_well].bottom(3))

    # # wash beads
    # p1000.pick_up_tip()
    # for sample_well in range(0,24):
    #     find_offset(sample_well)
    #     for i in range(0,3):
    #         p1000.transfer(1500, buff, deep_well.wells()[sample_well].top(), new_tip="never")
    #         p1000.transfer(1550, pickup_pos, waste.top(), new_tip="never")
    #         clean_tips(p1000, 1000, protocol)
    # p1000.drop_tip()
    # mag_mod.disengage()