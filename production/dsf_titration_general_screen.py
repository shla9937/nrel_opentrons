from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - general screen',
    'author': 'Shawn Laursen',
    'description': '''
    ''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_buff(protocol)
    add_sypro(protocol)
    add_metal(protocol)
    titrate(protocol)
    add_protein(protocol)
    add_water(protocol)
    add_controls(protocol)
    message(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, pcr, trough, tubes, p20m, plate, p300m, tips300
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    pcr = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    plate = protocol.load_labware('greiner_96_wellplate_300ul', 4)  
    
    # reagents
    global sypro, prot, water, pos, neg, metals_loc, buff1
    sypro = tubes.wells()[16]
    prot = tubes.wells()[20]
    pos = tubes.wells()[21].bottom(8)
    neg = tubes.wells()[22].bottom(8)
    metals_loc = [tubes.wells()[i].bottom(8) for i in range(0, 16)]
    buff1 = trough.wells()[0]

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[1]
    waste1 = trough.wells()[2]
    water2 = trough.wells()[3]
    waste2 = trough.wells()[4]
    water3 = trough.wells()[5]
    waste3 = trough.wells()[6]

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

def add_buff(protocol):
    pickup_tips(8, p20m, protocol)
    for col in range(0, 12):
        p20m.aspirate(5, buff1)             
        p20m.dispense(5, pcr.rows()[0][col])
    p20m.drop_tip()

def add_sypro(protocol):
    # add spyro to first well of plate
    pickup_tips(1, p300m, protocol)
    for row in range(0, 8):
        p300m.aspirate(70, sypro)            
        p300m.dispense(70, plate.rows()[row][0])
    p300m.drop_tip()

    pickup_tips(8, p20m, protocol)
    for col in range(0, 12):
        p20m.aspirate(5, plate.rows()[0][0])             
        p20m.dispense(5, pcr.rows()[0][col])
        clean_tips(p20m, 20, protocol)
    p20m.drop_tip()

def add_metal(protocol):
    # add 10x metals
    pickup_tips(8, p300m, protocol)
    for col in [1,2]:
        p300m.aspirate(90, water3)             
        p300m.dispense(90, plate.rows()[0][col])
    p300m.drop_tip()

    for row in range(0,8):
        metal = metals_loc[row]
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10, metal)  
        p20m.dispense(10, plate.wells()[row+8])
        p20m.mix(3,20)
        p20m.aspirate(1, plate.wells()[row+8])            
        p20m.dispense(1, pcr.rows()[row][0])
        p20m.drop_tip()

    for row in range(8,16):
        metal = metals_loc[row]
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10, metal)  
        p20m.dispense(10, plate.wells()[row+8])
        p20m.mix(3,20)
        p20m.aspirate(1, plate.wells()[row+8])            
        p20m.dispense(1, pcr.rows()[row-8][5])
        p20m.drop_tip()

def titrate(protocol):
    # titrate 2µL into 10µL
    for i in [0, 5]:
        pickup_tips(8, p20m, protocol)
        p20m.mix(3, 5, pcr.rows()[0][0+i])
        p20m.transfer(2,pcr.rows()[0][0+i:4+i],pcr.rows()[0][1+i:5+i],
                    mix_after=(3, 5),new_tip='never')
        p20m.aspirate(2, pcr.rows()[0][4+i])
        p20m.drop_tip()

def add_protein(protocol): 
    # add 10µL of protein
    pickup_tips(1, p300m, protocol)
    for row in range(0, 8):
        p300m.aspirate(150, prot)            
        p300m.dispense(150, plate.rows()[row][3])
    p300m.drop_tip()

    pickup_tips(8, p20m, protocol)
    for col in range(0, 10):
        p20m.aspirate(10, plate.rows()[0][3])
        p20m.dispense(10, pcr.rows()[0][col])
        p20m.mix(3,10)
        clean_tips(p20m, 20, protocol)
    p20m.drop_tip()

    pickup_tips(4, p20m, protocol)
    p20m.aspirate(10, plate.rows()[row][3])
    p20m.dispense(10, pcr.rows()[3][10])
    p20m.mix(3,10)
    p20m.drop_tip()

def add_water(protocol):
    # add 10µL of water
    pickup_tips(4, p20m, protocol)
    p20m.aspirate(10, water3)
    p20m.dispense(10, pcr.rows()[7][10])
    p20m.mix(3,10)
    p20m.drop_tip()

def add_controls(protocol):
    # add 10µL of positive control
    pickup_tips(1, p20m, protocol)
    for well in range(88, 92):
        p20m.aspirate(10, pos)
        p20m.dispense(10, pcr.wells()[well])
        p20m.mix(3,10)
        clean_tips(p20m, 20, protocol)
    p20m.drop_tip()

    # add 10µL of negative control
    pickup_tips(1, p20m, protocol)
    for well in range(92, 96):
        p20m.aspirate(10, neg)
        p20m.dispense(10, pcr.wells()[well])
        p20m.mix(3,10)
        clean_tips(p20m, 20, protocol)
    p20m.drop_tip()

def message(protocol):
    protocol.comment(msg="Protcol complete, please spin plate and equillibrate for 30mins \
                        before thermocycling.")

def clean_tips(pipette, clean_vol, protocol):
    if pipette == p20m:
        p20m.aspirate(clean_vol, water1)
        p20m.dispense(clean_vol, waste1.top().move(Point(3,0,-10)))
        p20m.move_to(waste1.top().move(Point(3,0,0)))
        p20m.aspirate(clean_vol, water2)
        p20m.dispense(clean_vol, waste2.top().move(Point(3,0,-10)))
        p20m.move_to(waste2.top().move(Point(3,0,0)))
        p20m.aspirate(clean_vol, water3)
        p20m.dispense(clean_vol, waste3.top().move(Point(3,0,-10)))
        p20m.move_to(waste3.top().move(Point(3,0,0)))