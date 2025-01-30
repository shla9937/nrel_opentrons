from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - battery screen',
    'author': 'Shawn Laursen',
    'description': '''
    Protocol:

    ''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_sypro(protocol)
    add_buff(protocol)
    add_metal(protocol)
    titrate(protocol)
    add_protein(protocol)
    add_water(protocol)
    add_controls(protocol)
    message(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, tips300, pcr, trough, tubes, p300m, p20m
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    pcr = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    
    # reagents
    global sypro4, prot, water, pos, neg, metals_loc, buff1, buff2, buff3
    sypro4 = tubes.wells()[8]
    prot = tubes.wells()[12]
    water = tubes.wells()[16]
    pos = tubes.wells()[20]
    neg = tubes.wells()[21]
    metals_loc = [tubes.wells()[i] for i in range(0, 7)]
    buff1 = trough.wells()[0]
    buff2 = trough.wells()[1]
    buff3 = trough.wells()[2]

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[3]
    waste1 = trough.wells()[4]
    water2 = trough.wells()[5]
    waste2 = trough.wells()[6]
    water3 = trough.wells()[7]
    waste3 = trough.wells()[8]

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

def add_sypro(protocol):
    # add 4x spyro to first well of plate
    pickup_tips(1, p300m, protocol)
    for well in range(0, 8):
        p300m.aspirate(60, sypro4)             
        p300m.dispense(60, pcr.wells()[well])
    p300m.drop_tip()

    # distribute spyro into other wells
    pickup_tips(8, p20m, protocol)
    p20m.transfer(5, pcr.rows()[0][0], pcr.rows()[0][1:12], new_tip='never')
    p20m.drop_tip()

def add_buff(protocol):
    # add pH 1.5
    pickup_tips(7, p20m, protocol)
    for col in range(0, 5):
        p20m.aspirate(5, buff1)             
        p20m.dispense(5, pcr.rows()[6][col])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()
    pickup_tips(1, p20m, protocol)
    for well in ["A11", "A12", "D11", "D12"]:
        p20m.aspirate(5, buff1)             
        p20m.dispense(5, pcr.wells_by_name()[well])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()

    # add pH 5.3
    pickup_tips(4, p20m, protocol)
    for col in range(5, 10):
        p20m.aspirate(5, buff2)             
        p20m.dispense(5, pcr.rows()[3][col])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()
    pickup_tips(1, p20m, protocol)
    for well in ["H1","H2","H3","H4","H5","B11","B12","E11","E12"]:
        p20m.aspirate(5, buff2)             
        p20m.dispense(5, pcr.wells_by_name()[well])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()

    # add pH 6.6
    pickup_tips(4, p20m, protocol)
    for col in range(5, 10):
        p20m.aspirate(5, buff3)             
        p20m.dispense(5, pcr.rows()[7][col])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()
    pickup_tips(1, p20m, protocol)
    for well in ["C11","C12","F11","F12"]:
        p20m.aspirate(5, buff3)             
        p20m.dispense(5, pcr.wells_by_name()[well])
        clean_tips(p20m, 5, protocol)
    p20m.drop_tip()

def add_metal(protocol):
    # add 10x metals
    metals_dict = {"Co": ["A1", "H1", "E6"],
                   "Mn": ["B1", "A6", "F6"],
                   "Ni": ["C1", "B6", "G6"],
                   "Li": ["D1", "C6", "H6"],
                   "Cu": ["E1", "D6"],
                   "Al": ["F1"],
                   "Fe": ["G1"]}
    
    count = 0
    for metal in metals_dict:
        pickup_tips(1, p20m, protocol)
        for well in metals_dict[metal]:
            p20m.aspirate(1, metals_loc[count])            
            p20m.dispense(1, pcr.wells_by_name()[well])
            clean_tips(p20m, 5, protocol)
        p20m.drop_tip()
        count += 1

def titrate(protocol):
    # titrate 1µL into 10µL
    for i in [0, 5]:
        pickup_tips(8, p20m, protocol)
        p20m.mix(3, 5 ,pcr.rows()[0][0+i])
        p20m.transfer(1,pcr.rows()[0][0+i:4+i],pcr.rows()[0][1+i:5+i],
                    mix_after=(3, 5),new_tip='never')
        p20m.aspirate(1, pcr.rows()[0][4+i])
        p20m.drop_tip()

def add_protein(protocol): 
    # add 10µL of protein
    pickup_tips(1, p20m, protocol)
    for well in range(0, 83):
        p20m.aspirate(10, prot)
        p20m.dispense(10, pcr.wells()[well].top(-3).move(Point(1,0,0)))
    for well in range(88, 91):
        p20m.aspirate(10, prot)
        p20m.dispense(10, pcr.wells()[well].top(-3).move(Point(1,0,0)))
    p20m.drop_tip()

def add_water(protocol):
    # add 10µL of water
    pickup_tips(1, p20m, protocol)
    for well in range(83, 86):
        p20m.aspirate(10, water)
        p20m.dispense(10, pcr.wells()[well].top(-3).move(Point(1,0,0)))
    for well in range(91, 94):
        p20m.aspirate(10, prot)
        p20m.dispense(10, pcr.wells()[well].top(-3).move(Point(1,0,0)))
    p20m.drop_tip()

def add_controls(protocol):
    # add 10µL of positive control
    pickup_tips(1, p20m, protocol)
    for well in ["G11","G12"]:
        p20m.aspirate(10, pos)
        p20m.dispense(10, pcr.wells_by_name()[well].top(-3).move(Point(1,0,0)))
    p20m.drop_tip()
    # add 10µL of negative control
    pickup_tips(1, p20m, protocol)
    for well in ["H11","H12"]:
        p20m.aspirate(10, neg)
        p20m.dispense(10, pcr.wells_by_name()[well].top(-3).move(Point(1,0,0)))
    p20m.drop_tip()

def message(protocol):
    protocol.pause(msg="Protcol complete, please spin plate and equillibrate for 30mins \
                        before thermocycling.")

def clean_tips(pipette, clean_vol, protocol):
    if pipette == p20m:
        p20m.aspirate(clean_vol, water1)
        p20m.dispense(clean_vol, waste1.top().move(Point(2,0,-10)))
        p20m.move_to(waste1.top().move(Point(2,0,0)))
        p20m.aspirate(clean_vol, water2)
        p20m.dispense(clean_vol, waste2.top().move(Point(2,0,-10)))
        p20m.move_to(waste2.top().move(Point(2,0,0)))
        p20m.aspirate(clean_vol, water3)
        p20m.dispense(clean_vol, waste3.top().move(Point(2,0,-10)))
        p20m.move_to(waste3.top().move(Point(2,0,0)))
    elif pipette == p300m:
        p300m.aspirate(clean_vol, water1)
        p300m.dispense(clean_vol, waste1.top().move(Point(2,0,-10)))
        p300m.move_to(waste1.top().move(Point(2,0,0)))
        p300m.aspirate(clean_vol, water2)
        p300m.dispense(clean_vol, waste2.top().move(Point(2,0,-10)))
        p300m.move_to(waste2.top().move(Point(2,0,0)))
        p300m.aspirate(clean_vol, water3)
        p300m.dispense(clean_vol, waste3.top().move(Point(2,0,-10)))
        p300m.move_to(waste3.top().move(Point(2,0,0)))