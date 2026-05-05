from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF screen - 12 point 1:1 dilution, 8 metals',
    'author': 'Shawn Laursen',
    'description': '''
    12 well dilution = 11 well dilution series (1mM -> 1µM) + 0 point
    Use 20µM stock protein -> 5µM final. (5µl x 96) + extra 
    Use 200mM Metal -> 1mM highest, then 2x dilution x 10 (1024 x total) to >1µM.
    Get 7 metals, plus, bottom row is HCl
    Col 12 is controls: 3 WT protein, 3 EDTA, 2 blanks
    ''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_sypro(protocol)
    add_buff(protocol)
    add_metal(protocol)
    titrate(protocol)
    add_edta(protocol)
    add_water(protocol)
    add_protein(protocol)
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
    global sypro, prot, edta, metals_loc, buff1
    sypro = tubes.wells()[16]
    prot = tubes.wells()[20]
    edta = tubes.wells()[21].bottom(8)
    metals_loc = [tubes.wells()[i].bottom(8) for i in range(0, 8)]
    buff1 = trough.wells()[0]

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3, water
    water1 = trough.wells()[1]
    waste1 = trough.wells()[2]
    water2 = trough.wells()[3]
    waste2 = trough.wells()[4]
    water3 = trough.wells()[5]
    waste3 = trough.wells()[6]
    water = trough.wells()[7]

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
    # add spyro to first well of staging plate
    pickup_tips(1, p300m, protocol)
    for row in range(0, 8):
        p300m.aspirate(70, sypro)            
        p300m.dispense(70, plate.rows()[row][0])

    # add spyro to first well of pcr plate
    p300m.aspirate(90, sypro) 
    for row in range(0, 8):        
        p300m.dispense(10, pcr.rows()[row][0])
    p300m.drop_tip()

def add_buff(protocol):
    # add water to metal dilution wells 
    pickup_tips(8, p300m, protocol)
    p300m.aspirate(120, water)             
    p300m.dispense(120, plate.rows()[0][1])
    
    # add water to first well of staging plate
    p300m.aspirate(35, water)            
    p300m.dispense(35, plate.rows()[0][0])

    # add buff to first well of staging plate
    p300m.aspirate(35, buff1)            
    p300m.dispense(35, plate.rows()[0][0])
    p300m.mix(3, 100)
    p300m.drop_tip()

    # add buff to first well of pcr plate
    pickup_tips(8, p20m, protocol)
    p20m.aspirate(5, buff1)             
    p20m.dispense(5, pcr.rows()[0][0])

    # add buff to titration wells
    for col in range(1, 12):
        p20m.aspirate(10, plate.rows()[0][0])             
        p20m.dispense(10, pcr.rows()[0][col])
    p20m.drop_tip()

def add_metal(protocol):
    # dilute metals 25x from 200mM to 8mM
    for row in range(0,8):
        metal = metals_loc[row]
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(5, metal)  
        p20m.dispense(5, plate.rows()[row][1])
        p20m.mix(3,5)
        p20m.drop_tip()

def titrate(protocol):
    # mix 4mM with 1:1 sypro to get 2mM metal
    pickup_tips(8, p20m, protocol)
    p20m.mix(5,20, plate.rows()[0][1])
    p20m.aspirate(5, plate.rows()[0][1])            
    p20m.dispense(5, pcr.rows()[0][0])
    p20m.mix(5,10)
    
    # titrate 10µL into 10µL 11 times
    p20m.transfer(10,pcr.rows()[0][0:10],pcr.rows()[0][1:11],
                mix_after=(5, 10),new_tip='never')
    p20m.aspirate(10, pcr.rows()[0][10])
    p20m.drop_tip()

def add_edta(protocol):
    # add 25mM (final) EDTA, concentration not super accurate
    for well in range(91, 94):
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(1, edta)
        p20m.dispense(1, pcr.wells()[well])
        p20m.mix(5,5)
        p20m.drop_tip()

def add_water(protocol):
    # add 10µL of water to blanks
    pickup_tips(2, p20m, protocol)
    p20m.aspirate(10, water)
    p20m.dispense(10, pcr.rows()[7][11])
    p20m.drop_tip()

def add_protein(protocol): 
    # add stock protein for 8 channel to staging plate
    pickup_tips(1, p300m, protocol)
    for row in range(0, 8):
        p300m.aspirate(150, prot)            
        p300m.dispense(150, plate.rows()[row][2])
    p300m.drop_tip()

    # add 10µL of protein to titrations diluting metals 1:1 (1mM highest now)
    pickup_tips(8, p20m, protocol)
    for col in range(0, 11):
        p20m.aspirate(10, plate.rows()[0][2])
        p20m.dispense(10, pcr.rows()[0][col])
        p20m.mix(3,10)
        clean_tips(p20m, 20, protocol)
    p20m.drop_tip()

    # control WT and edta wells
    pickup_tips(1, p20m, protocol)
    for well in range(88, 94):
        p20m.aspirate(10, prot)
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