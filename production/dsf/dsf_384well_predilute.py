from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - 384 well, predilute',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 30-32 metals in 12 point 1:3 (1 in 4) dilution series.
    1mM highest metal concentration (metal stocks are at 200mM).
    5µM final protein concentration (2x stock).
    1x final sypro concentration (6x stock).
    100mM buffer (6x stock).''',
    'apiLevel': '2.23'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_sypro(protocol)
    add_buff(protocol)
    add_metal_and_titrate(protocol)
    add_edta(protocol)
    add_protein(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, p20m, plate, p300m, tips300, dirty_tips20, dirty_tips300, metals, dilution_plate
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    metals = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5) 
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    dilution_plate = protocol.load_labware('greiner_96_wellplate_300ul', 8)  
         
    # reagents     
    global buff, protein, sypro, water, edta, rxn_vol, dilutant_vol, protein_vol, dilutant_stock_vol, dilution_factor, start_vol
    buff = trough.wells()[0]
    protein = trough.wells()[1]
    sypro = trough.wells()[2]
    water = trough.wells()[3]
    edta = metals.wells()[-1]
    rxn_vol = 20
    dilutant_vol = rxn_vol/2
    protein_vol = dilutant_vol
    dilutant_stock_vol = (dilutant_vol * 11) + 30
    dilution_factor = 3 # 1:3 aka 1 in X+1
    start_vol = (dilutant_vol/dilution_factor) + dilutant_vol

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[4]
    waste1 = trough.wells()[5]
    water2 = trough.wells()[6]
    waste2 = trough.wells()[7]
    water3 = trough.wells()[8]
    waste3 = trough.wells()[9]

    # tips
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
        if number == 8: # remove if ever figure out single return
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
        if number == 8: # remove if ever figure out single return
            tip_300 += number

def return_tips(pipette):
    if pipette == p20m:
        # p20m.configure_nozzle_layout(style=ALL)
        p20m.drop_tip(dirty_tips20.wells()[last_tip20])
    elif pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def add_sypro(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.distribute(dilutant_stock_vol/3, sypro, dilution_plate.rows()[0][0:4], new_tip='never') # add spyro to first well of staging plate
    return_tips(p300m)

    pickup_tips(8, p20m, protocol)
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    for row, col in zip(rows, cols):        
        p20m.transfer(start_vol/3, sypro, plate.rows()[row][col], new_tip='never') # add spyro to first well of pcr plate
    return_tips(p20m)

def add_buff(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.distribute(((200/6)*5)-5, water, dilution_plate.rows()[0][4:8], new_tip='never') # add water to metal dilution wells
    p300m.distribute(dilutant_stock_vol/3, water, dilution_plate.rows()[0][0:4], new_tip='never')# add water to first wells of staging plate
    p300m.distribute(dilutant_stock_vol/3, buff, dilution_plate.rows()[0][0:4], new_tip='never')# add buff to first well of staging plate
    return_tips(p300m)

    pickup_tips(8, p20m, protocol)
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    for row, col in zip(rows, cols):
        p20m.transfer(start_vol/3, buff, plate.rows()[row][col], new_tip='never')# add buff to first well of pcr plate
    return_tips(p20m)
    
    rows = [0,1,0,1]
    cols = [1,1,13,13]
    i = 0
    pickup_tips(8, p300m, protocol)
    for row, col in zip(rows, cols):
        p300m.mix(3, dilutant_stock_vol/2, dilution_plate.rows()[0][i])
        p300m.distribute(dilutant_vol, dilution_plate.rows()[0][i], plate.rows()[row][col:col+11], new_tip='never')# add dilutant to titration wells
        i += 1
    return_tips(p300m)

def add_metal_and_titrate(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    i = 0
    for row, col in zip(rows, cols):
        pickup_tips(8, p20m, protocol)
        p20m.transfer(5, metals.rows()[0][i], dilution_plate.rows()[0][i+4], mix_after=(5, 20), new_tip='never') # dilute 200mM to 6mM
        p20m.transfer(start_vol/dilution_factor, dilution_plate.rows()[0][i+4], plate.rows()[0+row][0+col], mix_after=(5, start_vol/2), new_tip='never') # dliute 6mM to 2mM
        p20m.transfer(dilutant_vol/dilution_factor, plate.rows()[0+row][0+col:11+col], plate.rows()[0+row][1+col:12+col], mix_after=(3, dilutant_vol), new_tip='never') # titrate 1:1
        p20m.aspirate(dilutant_vol/dilution_factor, plate.rows()[0+row][11+col]) # remove excess
        i += 1 
        return_tips(p20m)

def add_edta(protocol):
    for col in range(12,18):
        pickup_tips(1, p20m, protocol)
        p20m.transfer(rxn_vol/10, edta, plate.rows()[15][col], new_tip='never')
        p20m.drop_tip()    

def add_protein(protocol):
    pickup_tips(8, p20m, protocol)
    for row in range(0, 2):
        for col in range(0, 24):
            p20m.transfer(protein_vol, protein, plate.rows()[row][col], new_tip='never', mix_after=(3, protein_vol)) # add protein to first two rows of pcr plate
            clean_tips(p20m, 20, protocol)
    return_tips(p20m)

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