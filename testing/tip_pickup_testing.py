from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
import time
import sys
import math
import random
import subprocess

metadata = {
    'protocolName': 'Tip pickup test',
    'author': 'Shawn Laursen',
    'description': '''New tip pickup test''',
    'apiLevel': '2.20'
    }

def run(protocol):
    strobe(12, 8, True, protocol)
    setup(protocol)
    new_targeting(protocol)
    new_p20_single(protocol)
    strobe(12, 8, False, protocol)

def setup(protocol):
    # equiptment
    global tips300, tips20, p300m, p20m, plate
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 6)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    plate = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)

def strobe(blinks, hz, leave_on, protocol):
    i = 0
    while i < blinks:
        protocol.set_rail_lights(True)
        time.sleep(1/hz)
        protocol.set_rail_lights(False)
        time.sleep(1/hz)
        i += 1
    protocol.set_rail_lights(leave_on)

def new_targeting(protocol):
    p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end="E1")
    p300m.pick_up_tip(tips300)
    p300m.aspirate(10, plate.rows()[3][0])
    p300m.aspirate(10, plate.rows()[3][6])
    p300m.drop_tip()   

def new_p20_single(protocol):
    p20m.configure_nozzle_layout(style=SINGLE,start="H1")
    p20m.pick_up_tip(tips20)
    protocol.delay(seconds=5)
    p20m.drop_tip()