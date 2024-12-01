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
    global tempdeck, temp_buffs, rt_5ml, deep96_metal1, tips300, tips20, pcr1, p300m, p20m
    tempdeck = protocol.load_module('temperature module gen2', 10)
    temp_buffs = tempdeck.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    rt_5ml = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 11)
    deep96_metal1 = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 7)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 9)
    pcr1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    
    # reagents
    global sypro2, sypro4, metals_loc
    sypro2 = rt_5ml.wells()[0].top(-95)
    sypro4 = rt_5ml.wells()[1].top(-95)
    metals_loc = [rt_5ml.wells()[i].top(-95) for i in range(2, 10)]
    metals = 8
    samples = 2
    len_titration = 6
    metals_per_96well = 16
    rxn_vol = 20

#     # tips
#     global tip20_dict, tip300_dict
#     tip20_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
#     tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}

# def old_pickup_tips(number, pipette, protocol):
#     if pipette == p20m:
#         for col in tip20_dict:
#             if len(tip20_dict[col]) >= number:
#                 p20m.pick_up_tip(tips20[str(tip20_dict[col][number-1] + str(col))])
#                 tip20_dict[col] = tip20_dict[col][number:]
#                 break
#     if pipette == p300m:
#         for col in tip300_dict:
#             if len(tip300_dict[col]) >= number:
#                 p300m.pick_up_tip(tips300[str(tip300_dict[col][number-1] + str(col))])
#                 tip300_dict[col] = tip300_dict[col][number:]
#                 break

def pickup_tips(number, pipette, protocol):
    if number > 8 or number < 1 or pipette not in [p20m, p300m]:
        protocol.comment(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
        raise ValueError(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
    elif pipette == p20m:
        if number == 1:
            p20m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            nozzle_dict{2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
            p20m.configure_nozzle_layout(style=PARTIAL_COLUMN,start=nozzle_dict[number])
        else:
            p20m.configure_nozzle_layout(style=ALL)
    elif pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            nozzle_dict{2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
    else:
        protocol.comment("Custom tip pick up function doesn't recognize inputs.")
        raise ValueError("Custom tip pick up function doesn't recognize inputs.")

def titrate(protocol):

    # add_4x_first(protocol)
    # add_4x_metal(protocol)

    # add 2x spyro to last well of deep well
    pickup_tips(1, p300m, protocol)
    for sample in range(0, samples):
        for metal in range(0, metals):
            p300m.aspirate(200, sypro2)            
            row = metal % 8 
            col = (metal // 8) + (len_titration - 1)
            p300m.dispense(dilution_vol, deep96_metal1.rows()[row][col])
    p300m.drop_tip()

    # distribute spyro to 4 other wells
    pickup_tips(8, p300m, protocol)
    for well in range(1, len_titration):
        p300m.aspirate(40, deep96_metal1.rows()[0][len_titration - 1])
        p300m.dispense(40, deep96_metal1.rows()[0][well])
    p300m.drop_tip()


# def distribute_dilutions(protocol):
#     # distribute 2x sypro across columns (except first)

#     # add 4x sypro to first well 
#     for metal in range(0, metals):
#         pickup_tips(1, p300m, protocol)

# def add_4x_first(protocol):
#     # single channel add sypro into first well of titration
#     pickup_tips(1, p300m, protocol)
#     for row in range(0,8):
#         if counter < 100:    
#             p300m.aspirate(300, tubes.rows()[0][0].top(-95))
#             counter = 300
#         p300m.dispense(100, pcr_strips.rows()[row][col])
#         counter -= 100
#     p300m.drop_tip()

# def add_4x_metal(protocol):

# def add_protein(protocol):
#     # single channel to pipette total amount for each titration into first well of each row, write handling for multiple plates 
#     # distribute from first well into whole plate 

# def add_titration(protocol):
#     # 
# def message(protocol):



 