from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Lyse 24 well plate',
    'author': 'Shawn Laursen',
    'description': '''Perform the lysis step of 24 well purification.'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    lyse(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global trash, pipette, tips1000,  empty_tiprack, tips1000_24well, tips24_adapter, lysis_buff, plate24 
    trash = protocol.load_trash_bin ('D1')
    pipette = protocol.load_instrument('flex_96channel_1000')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B2')
    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'C1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'C2')
    lysis_buff = protocol.load_labware('nest_1_reservoir_195ml', 'D2')
    plate24 = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D3')

def define_liquids(protocol):
    buffer_liquid = protocol.define_liquid(
        name="Lysis buff",
        description="50mM Tris/Hepes pH 7.5, 300mM NaCl, 5\%\ glycerol, 0.1\%\ B-OG, 0.1mg/mL DNaseI, 1mg/mL Lysozyme",
        display_color="#50C878")
    lysis_buff['A1'].load_liquid(liquid=buffer_liquid,volume=60000)


def pickup_24(protocol):
    global half_filled
    half_filled = False
    try:
        protocol.move_labware(tips1000_24well, "C1", use_gripper=True)
    except:
        None

    if half_filled is False:
        pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000])
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
    
def lyse(protocol):
    protocol.pause("Make sure to centrifuge cultures and decant.")
    pickup_24(protocol)
    pipette.transfer(2000, lysis_buff.wells()[0], plate24.wells()[0].top(), new_tip='never')
    pipette.mix(10, 1000, plate24.wells()[0].bottom(5))
    pipette.drop_tip()
    protocol.pause("Shake for ~2 hrs in cold room.")