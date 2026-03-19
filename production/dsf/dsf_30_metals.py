from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - 384 well, 30 metals',
    'author': 'Shawn Laursen',
    'description': '''
    Adds buff + spyro + protein
    Titrates 29 metals in 12 point dilution series. 
    For 1:2 dultion - (1mM, 333µM, 111µM, 37µM, 12.3µM, 4.1µM, 1.37µM, 457nM, 152nM, 51nM, 17nM, 6nM)
    For 1:1 dilution - (100µM, 50.0µM, 25.0µM, 12.5µM, 6.25µM, 3.13µM, 1.56µM, 781nM, 391nM, 195nM, 97.7nM, 48.8nM)

    Stocks:
    -   metal: 5x (5mM/500µM) -> 1mM/100µM final (into 15mL Falcons)
    -   EDTA: 5x (500mM/500µM) -> 100mM/100µM final (into last 15mL Falcon)
    -   Apo: buff (50µL into well H4)
    -   protein + sypro + rox: 5x (25µM, 50x, 250nM) -> 5µM, 10x, 50nM final (2mL total -> 250µL into wells)

    Buff should be ~100mM buff, 150mM NaCl (10mL in trough)''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    dilute_metals(protocol)
    add_protein_and_sypro(protocol) 
    add_metal_and_titrate(protocol) # titrate into protein/buff wells, diluted in protein/buff
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, tips300, metals, plate, trough, p20m, p300s, tubes1, tubes2
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 2)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    metals = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5) 
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300s = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips300])
    tubes1 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 7)
    tubes2 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 8)
         
    # reagents     
    global buff, protein_and_sypro
    buff = trough.wells()[0]
    protein_and_sypro = metals.rows()[0][11]

    # rows
    global rxn_vol, start_vol, dilution_factor
    rxn_vol = 20   
    dilution_factor = 1 # i.e. 1:2, not 1 in 2
    start_vol = rxn_vol + (rxn_vol/dilution_factor)

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

def dilute_metals(protocol):
    # add buff to wells
    p300s.pick_up_tip()
    p300s.transfer(190, buff, metals.wells()[0:31], new_tip='never')
    p300s.transfer(200, buff, metals.wells()[31], new_tip='never')
    p300s.return_tip()

    # add metal to buffs
    well = 0
    for rack in [tubes1, tubes2]:
        for tube in range(15):
            p300s.pick_up_tip()
            p300s.transfer(10, rack.wells()[tube], metals.wells()[well], new_tip='never', mix_after=(3,50))         
            p300s.return_tip()   
            well += 1
            
    # add extra EDTA well
    p300s.pick_up_tip()
    p300s.transfer(10, tubes2.wells()[14], metals.wells()[30], new_tip='never', mix_after=(3,50))         
    p300s.return_tip()   

def add_protein_and_sypro(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    
    pickup_tips(8, p20m, protocol)
    for row, col in zip(rows, cols):
        p20m.transfer(start_vol*(3/5), buff, plate.rows()[row][col], new_tip='never')
        p20m.transfer(rxn_vol*(4/5), buff, plate.rows()[row][col+1:col+12], new_tip='never')
    for row, col in zip(rows, cols):
        p20m.transfer(start_vol*(1/5), protein_and_sypro, plate.rows()[row][col], new_tip='never')
        p20m.transfer(rxn_vol*(1/5), protein_and_sypro, plate.rows()[row][col+1:col+12], new_tip='never')
    p20m.return_tip()

def add_metal_and_titrate(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    metal_col = [0,1,2,3]

    for row, col, metal in zip(rows, cols, metal_col):
        pickup_tips(8, p20m, protocol)
        p20m.transfer(start_vol*(1/5), metals.rows()[0][metal], plate.rows()[row][col], new_tip='never', 
                mix_before=(3,rxn_vol))
        p20m.transfer(rxn_vol/dilution_factor, plate.rows()[row][col+0:col+11], plate.rows()[row][col+1:col+12], 
                    mix_before=(3,rxn_vol), new_tip='never')    
        p20m.mix(3,rxn_vol, plate.rows()[row][col+11])
        p20m.aspirate(rxn_vol/dilution_factor, plate.rows()[row][col+11])
        p20m.return_tip()