from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Pull 96 sups',
    'author': 'Shawn Laursen',
    'description': '''
    Pulls supernatant from 96 well deep well into new 96 well plate.''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="volume",
        display_name="Volume to transfer",
        description="Volume to transfer from each well to 96 well plate.",
        default=1000,
        minimum=20,
        maximum=2000,)

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    pull_sup(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips300, dirty_tips300, old_plate96, new_plate96, p300m
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    old_plate96 = protocol.load_labware('nest_96_wellplate_2ml_deep', 2)  
    new_plate96 = protocol.load_labware('nest_96_wellplate_2ml_deep', 5)  

    # tips
    global tip_300
    tip_300 = 0

def pickup_tips(number, pipette, protocol):
    global last_tip300, tip_300
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}

    if pipette == p300m:
        last_tip300 = tip_300
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        p300m.pick_up_tip(tips300)
        if number == 8: # remove if ever figure out single return
            tip_300 += number

def return_tips(pipette):
    if pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def pull_sup(protocol):
    volume = protocol.params.volume
    for col in range(12):
        pickup_tips(8, p300m, protocol)
        p300m.transfer(volume, old_plate96.wells()[col*8].bottom(5).move(Point(0,-2,0)), new_plate96.columns()[col], new_tip='never')
        return_tips(p300m)
