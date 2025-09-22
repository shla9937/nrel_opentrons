from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Dot blot prep',
    'author': 'Shawn Laursen',
    'description': '''Dot 96 lysates onto nitrocellulose membrane from 96 well deep well.''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    make_slide(protocol)
    add_standard(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, dirty_tips20, p20m, deepwell, blot, trough, standards
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])   
    deepwell = protocol.load_labware('nest_96_wellplate_2ml_deep', 6)
    blot = protocol.load_labware('shawn_104_well_blot_holder_2ul', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 2)
    standards = protocol.load_labware('greiner_96_wellplate_300ul', 8)

    # reagents
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[0]
    waste1 = trough.wells()[1]
    water2 = trough.wells()[2]
    waste2 = trough.wells()[3]
    water3 = trough.wells()[4]
    waste3 = trough.wells()[5]

    # tips
    global tip_20
    tip_20 = 0

def pickup_tips(number, pipette, protocol):
    global last_tip20, last_tip300, tip_20, tip_300
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
   
    if pipette == p20m: 
        last_tip20 = tip_20
        if number == 1:
            p20m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p20m.configure_nozzle_layout(style=PARTIAL_COLUMN, start="H1", end=nozzle_dict[number])
        else:
            p20m.configure_nozzle_layout(style=ALL)
        p20m.pick_up_tip(tips20)
        if number == 8: # remove if ever figure out single return
            tip_20 += number

def return_tips(pipette):
    if pipette == p20m:
        # p20m.configure_nozzle_layout(style=ALL)
        p20m.drop_tip(dirty_tips20.wells()[last_tip20])

def make_slide(protocol):
    pickup_tips(8, p20m, protocol)
    for col in range(12):
        p20m.transfer(2, deepwell.columns()[col][0], blot.columns()[col][0], new_tip='never')
        clean_tips(p20m, protocol)
    return_tips(p20m)

def add_standard(protocol):
    pickup_tips(7, p20m, protocol)
    p20m.transfer(20, water3, standards.columns()[0][7], new_tip='never')
    p20m.drop_tip()

    pickup_tips(1, p20m, protocol)
    for well in range(7):
        p20m.transfer(2, standards.wells()[well], blot.wells()[well+96], new_tip='never')
        p20m.transfer(20, standards.wells()[well], standards.wells()[well+1], mix_after=(3,20), new_tip='never')
    p20m.transfer(2, standards.wells()[7], blot.wells()[7+96], new_tip='never')    
    p20m.drop_tip()

def clean_tips(pipette, protocol):
    if pipette == p20m:
        p20m.aspirate(20, water1)
        p20m.dispense(20, waste1.top().move(Point(2,0,-10)))
        p20m.move_to(waste1.top().move(Point(2,0,0)))
        p20m.aspirate(20, water2)
        p20m.dispense(20, waste2.top().move(Point(2,0,-10)))
        p20m.move_to(waste2.top().move(Point(2,0,0)))
        p20m.aspirate(20, water3)
        p20m.dispense(20, waste3.top().move(Point(2,0,-10)))
        p20m.move_to(waste3.top().move(Point(2,0,0)))
