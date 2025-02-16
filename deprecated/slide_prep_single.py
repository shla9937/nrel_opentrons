from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'X-ray slide prep - single',
    'author': 'Shawn Laursen',
    'description': '''Prepare slide for SLAC x-ray absorption
    experiment. Takes 2 x 96well plates and pipettes 1µL onto
    3 x 2in quartz slide.
    ''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    make_slide(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, p20m, pcr1, pcr2, slide, trough
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 4)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    pcr1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 2)
    pcr2 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 8)
    slide = protocol.load_labware('shawn_192_well_slideholder_1ul', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)

    # reagents
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[0]
    waste1 = trough.wells()[1].top()
    water2 = trough.wells()[2]
    waste2 = trough.wells()[3].top()
    water3 = trough.wells()[4]
    waste3 = trough.wells()[5].top()

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    if pipette == p20m:
        if number == 1:
            p20m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p20m.configure_nozzle_layout(style=PARTIAL_COLUMN, start="H1", end=nozzle_dict[number])
        else:
            p20m.configure_nozzle_layout(style=ALL)
        p20m.pick_up_tip(tips20)

    elif pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        p300m.pick_up_tip(tips300)

def make_slide(protocol):
    pickup_tips(1, p20m, protocol)
    for well in range(0, 96, 1):
        p20m.aspirate(1, pcr1.wells()[well])
        p20m.dispense(1, slide.wells()[well])
        clean_tips(p20m, protocol)
    for well in range(0, 96, 1):
        p20m.aspirate(1, pcr2.wells()[well])
        p20m.dispense(1, slide.wells()[well])
        clean_tips(p20m, protocol)
    p20m.drop_tip()

def clean_tips(pipette, protocol):
    p20m.aspirate(20, water1)
    p20m.dispense(20, waste1)
    p20m.aspirate(20, water2)
    p20m.dispense(20, waste2)
    p20m.aspirate(20, water3)
    p20m.dispense(20, waste3)


