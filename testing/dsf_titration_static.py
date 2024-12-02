from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF metal titration - static',
    'author': 'Shawn Laursen',
    'description': '''Follow up on hits from DSF screen
    Variables:
    -   csv with hits from 96 well plate [do math to figure out how many plates]
        (plate will already be normalized to 2x protein (2-10µM), or if the anti-
        body method they won't be normalized and I'll need to write plate 
        coating and washing steps)
    -   # of metals to be screened [1-16]
    -   length of titrations (last poitn is 0) [2-12]
    -   steepness of titration in for 1:X [0.5-10]
    -   volume of reaction (5-30µL)
    Protocol:
    -   collect hits from csv
    -   determine how many plates will be used
    -   stock metals start at 4x
    -   Sypro buffer starts at 4x
    -   titrate metals in spare 96 well plate at 2x 
    -   *potential plate coating step*
    -   add protein to bottom of plate
    -   *potential plate washing step*
    -   add metals + spyro to top of plate
    -   message to spin, incubate, and qPCR
    ''',
    'apiLevel': '2.20'
    }

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    titrate(protocol)
    add_protein(protocol)
    add_titration(protocol)
    message(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tempdeck, temp_buffs, rt_5ml, metal_plate, tips300, tips20, pcr1, p300m, p20m
    tempdeck = protocol.load_module('temperature module gen2', 10)
    temp_buffs = tempdeck.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    rt_5ml = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 11)
    metal_plate = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 7)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 9)
    pcr1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    
    # reagents
    global sypro2, sypro4, metals_loc, metals, samples, samples_loc, len_titration
    sypro2 = rt_5ml.wells()[0].top(-95)
    sypro4 = rt_5ml.wells()[1].top(-95)
    metals_loc = [rt_5ml.wells()[i].top(-95) for i in range(2, 10)]
    metals = 8
    samples = 2
    samples_loc = [temp_buffs.wells()[i] for i in range(0, 2)]
    len_titration = 6

    # tips
    global tip20_dict, tip300_dict
    tip20_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "B1", 3: "C1", 4: "D1", 5: "E1", 6: "F1", 7: "G1"}
    if number > 8 or number < 1 or pipette not in [p20m, p300m]:
        protocol.comment(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
        raise ValueError(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
    elif pipette == p20m:
        if number == 1:
            p20m.configure_nozzle_layout(style=SINGLE,start="A1")
        elif number > 1 and number < 8:
            p20m.configure_nozzle_layout(style=PARTIAL_COLUMN, start="A1", end=nozzle_dict[number])
        else:
            p20m.configure_nozzle_layout(style=ALL)
        for col in tip20_dict:
            if len(tip20_dict[col]) >= number:
                p20m.pick_up_tip(tips20[str(tip20_dict[col][number-1] + str(col))])
                tip20_dict[col] = tip20_dict[col][number:]
                break
    elif pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="A1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="A1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        for col in tip300_dict:
            if len(tip300_dict[col]) >= number:
                p300m.pick_up_tip(tips300[str(tip300_dict[col][number-1] + str(col))])
                tip300_dict[col] = tip300_dict[col][number:]
                break
    else:
        protocol.comment("Custom tip pick up function doesn't recognize inputs.")
        raise ValueError("Custom tip pick up function doesn't recognize inputs.")

def titrate(protocol):
    # add 2x spyro to last well of deep well
    pickup_tips(1, p300m, protocol)
    for metal in range(0, metals):
        p300m.aspirate(200, sypro2)            
        row = metal % 8 
        col = (metal // 8) + (len_titration - 1)
        p300m.dispense(200, metal_plate.rows()[row][col])
    p300m.drop_tip()

    # distribute spyro to 4 other wells
    pickup_tips(8, p300m, protocol)
    for well in range(1, len_titration - 1):
        p300m.aspirate(40, metal_plate.rows()[0][len_titration - 1])
        p300m.dispense(40, metal_plate.rows()[0][well])
    p300m.drop_tip()

    # add 4x sypro to the first well
    pickup_tips(1, p300m, protocol)
    for metal in range(0, metals):
        p300m.aspirate(40, sypro4)            
        row = metal % 8 
        col = (metal // 8)
        p300m.dispense(40, metal_plate.rows()[row][col])
    p300m.drop_tip()

    # add_4x_metal(protocol) 
    for metal in range(0, metals):
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(40, metals_loc[metal])            
        row = metal % 8 
        col = (metal // 8)
        p300m.dispense(40, metal_plate.rows()[row][col])
        p300m.drop_tip()

    # titrate 10 rxn + 10 rxn + 20 extra
    pickup_tips(8, p300m, protocol)
    p300m.transfer(40,metal_plate.rows()[0][0:len_titration-2],
                   metal_plate.rows()[0][1:len_titration-1],
                   mix_after=(3, 20), new_tip='never')
    p300m.aspirate(40, metal_plate.rows()[0][len_titration-2])
    p300m.drop_tip()

def add_protein(protocol): # add 10µL of protein
    # for each sample, pipette into first well
    for sample in range(0, samples):
        for metal in range(0, metals):
            pickup_tips(1, p300m, protocol)
            p300m.aspirate(60, samples_loc[sample])            
            row = metal % 8 
            col = (metal // 8) + (sample * 6)
            p300m.dispense(60, pcr1.rows()[row][col])
            p300m.drop_tip()

    # pick up eight tips (eventually change to number of metals) and distrribute
    for sample in range(0, samples):
        pickup_tips(8, p300m, protocol) # change to "metals" later, accounting for > 8
        col = sample * 6
        p300m.distribute(10, pcr1.rows()[0][col],
                    pcr1.rows()[0][col+1:col+len_titration],
                    disposal_volume=0, new_tip='never')
        p300m.drop_tip()

def add_titration(protocol): # add 10µL of titration
    # plate titration into each sample, go from least to most, only to top
    pickup_tips(8, p20m, protocol) # need to adjust to metals later
    for col in range(len_titration -1 , -1, -1):
        row = 0
        p20m.aspirate(20, metal_plate.rows()[row][col])
        for sample in range(0, samples):
            pcr_col = col + (sample * 6)
            p20m.dispense(10, pcr1.rows()[row][pcr_col].top(-3))
    p20m.drop_tip()

def message(protocol):
    protocol.pause(msg="Protcol complete, please spin plate and equillibrate for 30 \
                        before thermocycling.")
