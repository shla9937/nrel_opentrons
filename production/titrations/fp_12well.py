from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'FP - 12 well titrations',
    'author': 'Shawn Laursen',
    'description': '''
    Adds buff + spyro + protein
    Titrates 32 DNAs in 12 point dilution series. (1mM, 333µM, 111µM, 37µM, 12.3µM, 4.1µM, 1.37µM, 457nM, 152nM, 51nM, 17nM, 6nM)

    Stocks:
    -   DNA: 5x (25nM) -> 5nM final (65µL into wells A1-H4)
    -   protein: 5x (50µM) -> 10µM 42µL into wells)

    Buff should be ~50mM buff, 150mM NaCl (10mL in trough)''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_buff_and_dna(protocol)
    add_protein_and_titrate(protocol) 
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, dnas, plate, trough, p20m
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 2)
    dnas = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5) 
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
         
    # reagents     
    global buff, protein
    buff = trough.wells()[0]
    protein= dnas.rows()[0][11]

    # rows
    global rxn_vol, start_vol, dilution_factor
    rxn_vol = 20   
    dilution_factor = 2 # i.e. 1:2, not 1 in 2
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

def add_buff_and_dna(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]
    dna_col = [0,1,2,3]
    
    pickup_tips(8, p20m, protocol)
    for row, col in zip(rows, cols):
        p20m.transfer(start_vol*(3/5), buff, plate.rows()[row][col], new_tip='never')
        p20m.transfer(rxn_vol*(4/5), buff, plate.rows()[row][col+1:col+12], new_tip='never')
    p20m.return_tip()
    pickup_tips(8, p20m, protocol)
    for row, col, dna_col in zip(rows, cols, dna_col):
        p20m.transfer(start_vol*(1/5), dnas.rows()[0][dna_col], plate.rows()[row][col], new_tip='never')
        p20m.transfer(rxn_vol*(1/5), dnas.rows()[0][dna_col], plate.rows()[row][col+1:col+12], new_tip='never')
    p20m.return_tip()

def add_protein_and_titrate(protocol):
    rows = [0,1,0,1]
    cols = [0,0,12,12]

    for row, col in zip(rows, cols):
        pickup_tips(8, p20m, protocol)
        p20m.transfer(start_vol*(1/5), protein, plate.rows()[row][col], new_tip='never', 
                mix_before=(3,rxn_vol))
        p20m.transfer(rxn_vol/dilution_factor, plate.rows()[row][col+0:col+10], plate.rows()[row][col+1:col+11], 
                    mix_before=(3,rxn_vol), new_tip='never')    
        p20m.mix(3,rxn_vol, plate.rows()[row][col+10])
        p20m.aspirate(rxn_vol/dilution_factor, plate.rows()[row][col+10])
        p20m.return_tip()