from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - 384 well, custom dilution',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 30-32 metals in 12 point dilution series.
    1mM highest metal concentration (metal stocks are at 200mM).
    5µM final protein concentration.
    1x final sypro concentration.
    20mM buff, 150mM NaCl.
    Protein stock should be at 1.14x final concentration (5.7µM protein, 20mM buff, 150mM NaCl) - 15ml.
    Sypro stock should be at 8x (in 20mM buff, 150mM NaCl) - 2ml.
    EDTA stock at 500mM (in 20mM buff, 150mM NaCl).''',
    'apiLevel': '2.23'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_protein(protocol) # fill plate with protein in buff at 1.14x protein, 1x buff, 17.5µl
    add_metal_and_titrate(protocol) # titrate into protein/buff wells, diluted in protein/buff
    add_edta(protocol) # add edta to control wells, 2µl
    add_sypro(protocol) # add sypro to all wells, 2.5µL of 8x sypro in 1x buff
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
    global protein, sypro, water, edta, rxn_vol, dilutant_vol, protein_vol, dilutant_stock_vol, dilution_factor, start_vol
    protein = trough.wells()[0]
    sypro = trough.wells()[1]
    water = trough.wells()[2]
    edta = metals.wells()[-1]

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3
    water1 = trough.wells()[3]
    waste1 = trough.wells()[4]
    water2 = trough.wells()[5]
    waste2 = trough.wells()[6]
    water3 = trough.wells()[7]
    waste3 = trough.wells()[8]

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

def add_protein(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.distribute(197.34, protein, dilution_plate.rows()[0][0:4], new_tip='never') # add protein to metal dilution wells

    rows = [0,1,0,1]
    cols = [0,0,12,12]
    for row, col in zip(rows, cols):
        p300m.distribute([10,11.48,15.27,17.5,17.5,17.5,17.5,17.5,17.5,17.5,17.5,17.5], protein, plate.rows()[row][col:col+12], new_tip='never')# add protein to pcr plate
    return_tips(p300m)

def add_metal_and_titrate(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    i = 0
    for row, col in zip(rows, cols):
        pickup_tips(8, p20m, protocol)
        p20m.transfer(2.66, metals.rows()[0][i], dilution_plate.rows()[0][i], mix_after=(10,20), new_tip='never') # dilute 200mM to 2.6562mM (2.66)
        p20m.transfer(7.5, dilution_plate.rows()[0][i], plate.rows()[0+row][0+col], mix_after=(5,10), new_tip='never') # dliute to 1mM in plate
        p20m.transfer(6.02, dilution_plate.rows()[0][i], plate.rows()[0+row][1+col], mix_after=(5,10), new_tip='never') # dliute to 800µM in plate
        p20m.transfer(5.3, dilution_plate.rows()[0][i], plate.rows()[0+row][2+col], mix_after=(5,10), new_tip='never') # dliute to 600µM in plate
        p20m.transfer(3.07, plate.rows()[0+row][2+col:11+col], plate.rows()[0+row][3+col:12+col], mix_after=(3,10), new_tip='never') # titrate 6.7x dilution series
        p20m.aspirate(3.07, plate.rows()[0+row][11+col]) # remove excess
        i += 1 
        return_tips(p20m)

def add_edta(protocol):
    for col in range(12,18):
        pickup_tips(1, p20m, protocol)
        p20m.transfer(2, edta, plate.rows()[15][col], new_tip='never')
        p20m.drop_tip()    
    
def add_sypro(protocol):
    pickup_tips(8, p20m, protocol)
    for row in range(0,2):
        for col in range(0,24):
            p20m.transfer(2.5, sypro, plate.rows()[row][col], new_tip='never', mix_after=(3,10)) # add spyro to all
            clean_tips(p20m, 20, protocol)
    return_tips(p20m)

