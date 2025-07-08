from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Xylenol Orange Titration - 12 point 1:1 dilution, 384 well plate',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 16 metals in 12 point 1:1 dilution series.
    Half of titrations are with protein, half are without.
    128µM highest metal concentration.
    5µM final protein concentration.
    10µM final xylenol orange concentration.
    20mM MES.
    Steps:
        - Add 50µL of buffs to wells 2-11, 66.6µL to well 1
        - Spike in 2µL of metals to each and titrate 1:3 (aka 16.66 in 50µL)''',
    'apiLevel': '2.23'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    distribute_buffs(protocol)
    add_metal(protocol)
    titrate(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, tubes, p20m, plate, p300m, tips300
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)  
    
    # reagents
    global metals_loc, buff, prot_buff
    metals_loc = [tubes.wells()[i].bottom(8) for i in range(0, 16)]
    buff = trough.wells()[0]
    prot_buff = trough.wells()[1]

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

def distribute_buffs(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.transfer(66.6, buff, plate.rows()[0][0], new_tip='never')
    p300m.transfer(50, buff, plate.rows()[0][1:12], new_tip='never')
    p300m.transfer(66.6, buff, plate.rows()[0][12], new_tip='never')
    p300m.transfer(50, buff, plate.rows()[0][13:24], new_tip='never')
    p300m.drop_tip()

    pickup_tips(8, p300m, protocol)
    p300m.transfer(66.6, prot_buff, plate.rows()[1][0], new_tip='never')
    p300m.transfer(50, prot_buff, plate.rows()[1][1:12], new_tip='never')
    p300m.transfer(66.6, prot_buff, plate.rows()[1][12], new_tip='never')
    p300m.transfer(50, prot_buff, plate.rows()[1][13:24], new_tip='never')
    p300m.drop_tip()

def add_metal(protocol):
    for metal in range(0,8):
        pickup_tips(1, p20m, protocol)
        p20m.transfer(2, metals_loc[metal], plate.rows()[metal*2][0], mix_after=(3,5), new_tip='never')
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.transfer(2, metals_loc[metal], plate.rows()[metal*2+1][0], mix_after=(3,5), new_tip='never')
        p20m.drop_tip()
    for metal in range(0,8):
        pickup_tips(1, p20m, protocol)
        p20m.transfer(2, metals_loc[metal+8], plate.rows()[metal*2][12], mix_after=(3,5), new_tip='never')
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.transfer(2, metals_loc[metal+8], plate.rows()[metal*2+1][12], mix_after=(3,5), new_tip='never')
        p20m.drop_tip()

def titrate(protocol):
    rows = [0,0,1,1]
    cols = [0,12,0,12]
    for row, col in zip(rows,cols):
        pickup_tips(8, p20m, protocol)
        p20m.transfer(16.66, plate.rows()[0+row][0+col:10+col], plate.rows()[0+row][1+col:11+col], 
                    mix_before=(5, 20), new_tip='never')
        p20m.drop_tip()

