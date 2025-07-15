from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - test 384 well plate',
    'author': 'Shawn Laursen',
    'description': '''Loads plate with 20, 15, 10 and 5 µL''',
    'apiLevel': '2.23'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    distribute_buffs(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, tubes, p20m, plate, p300m, tips300, dirty_tips20, dirty_tips300
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    plate = protocol.load_labware('appliedbiosystemsmicroamp_384_wellplate_40ul', 5)  
    
    # reagents
    global metals_loc, buff, prot_buff
    metals_loc = [tubes.wells()[i].bottom(8) for i in range(0, 16)]
    buff = trough.wells()[0]
    prot_buff = trough.wells()[1]

    #single tips
    global tip_20, tip_300
    tip_20 = 0
    tip_300 = 0

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
        tip_20 += number

    elif pipette == p300m:
        last_tip300 = tip_300
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        p300m.pick_up_tip(tips300)
        tip_300 += number

def return_tips(pipette):
    if pipette == p20m:
        # p20m.configure_nozzle_layout(style=ALL)
        p20m.drop_tip(dirty_tips20.wells()[last_tip20])
    elif pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def distribute_buffs(protocol):
    pickup_tips(8, p20m, protocol)
    p20m.transfer(20, buff, plate.rows()[0][0:6], new_tip='never')
    p20m.transfer(20, buff, plate.rows()[1][0:6], new_tip='never')
    p20m.transfer(15, buff, plate.rows()[0][6:12], new_tip='never')
    p20m.transfer(15, buff, plate.rows()[1][6:12], new_tip='never')
    p20m.transfer(10, buff, plate.rows()[0][12:18], new_tip='never')
    p20m.transfer(10, buff, plate.rows()[1][12:18], new_tip='never')
    p20m.transfer(5, buff, plate.rows()[0][18:24], new_tip='never')
    p20m.transfer(5, buff, plate.rows()[1][18:24], new_tip='never')
    return_tips(p20m)


