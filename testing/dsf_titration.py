from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF metal titration - hit follow up, 96well',
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

def add_parameters(parameters: protocol_api.Parameters):
    # parameters.add_csv(
    #     variable_name="hits_csv",
    #     display_name="Hits CSV",
    #     description="This CSV contains the hits and their 96 well location",
    #     default="/path/to/csv")
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples (to be replace with CSV)",
        description="Number of proteins to test",
        default=1,
        minimum=1,
        maximum=8,
        unit="proteins")
    parameters.add_int(
        variable_name="metals",
        display_name="Number of metals",
        description="Number of metals/titrations to be screened",
        default=8,
        minimum=1,
        maximum=16,
        unit="metals")
    parameters.add_int(
        variable_name="len_titration",
        description="Number of wells ",
        default=12,
        minimum=2,
        maximum=12,
        unit="wells")
    parameters.add_float(
        variable_name="steepness",
        display_name="Steepness of titration in 1:X",
        description="Dilution factor for titration (1:X) ",
        default=1,
        minimum=0.5,
        maximum=10)
    parameters.add_int(
        variable_name="rxn_vol",
        display_name="Volume of reaction",
        description="Volume of reaction in µL",
        default=10,
        minimum=5,
        maximum=30,
        unit="µL")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    check_params(protocol)
    titrate(protocol)
    add_protein(protocol)
    add_titration(protocol)
    message(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tempdeck, temp_buffs, rt_5ml, deep96_prot, deep96_metal1, deep96_metal2, \
           tips300, tips20, pcr1, pcr2, pcr3, pcr4, p300m, p20m
    tempdeck = protocol.load_module('temperature module gen2', 10)
    temp_buffs = tempdeck.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    rt_5ml = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 11)
    deep96_prot = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 7)
    deep96_metal1 = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)
    deep96_metal2 = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 9)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 6)
    pcr1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 1)
    pcr2 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 2)
    pcr3 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 3)
    pcr4 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 4)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    
    # reagents
    global sypro2, sypro4, metals_loc
    sypro2 = rt_5ml.wells()[0].top(-95)
    sypro4 = rt_5ml.wells()[1].top(-95)
    metals_loc = [rt_5ml.wells()[i].top(-95) for i in range(2, 18)]
    
    # set up plates
    global steepness, rxn_vol, max_vol, wells_in_row, wells_in_col, wells_in_plate, \
           samples, metals, len_titration, start_vol, dilution_vol
    steepness = protocol.params.steepness # 1
    rxn_vol = protocol.params.rxn_vol
    max_vol = 2000 # max volume of deepwell block
    wells_in_row = 12 # in rxn plate, later this will change to 24 for 384 well
    wells_in_col = 8 # in rxn plate, later this will change to 16 for 384 well
    wells_in_plate = wells_in_col * wells_in_row
    samples = protocol.params.samples # 2
    metals = protocol.params.metals # 8
    len_titration = protocol.params.len_titration # 6
    rxn_extra = rxn_vol + 20
    start_vol = rxn_extra * steepness * samples
    dilution_vol = rxn_extra * len_titration * samples

    # find out how many pcr plates are needed
    global titrations_per_row, titrations_per_plate, plates, titrations
    titrations_per_row = (len_titration + 1) // wells_in_row
    titrations_per_plate = titrations_per_row * wells_in_col
    plates = (samples * metals) / titrations_per_plate
    titrations = metals * samples

    # tips
    global tip20_dict, tip300_dict
    tip20_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}

def old_pickup_tips(number, pipette, protocol):
    if pipette == p20m:
        for col in tip20_dict:
            if len(tip20_dict[col]) >= number:
                p20m.pick_up_tip(tips20[str(tip20_dict[col][number-1] + str(col))])
                tip20_dict[col] = tip20_dict[col][number:]
                break
    if pipette == p300m:
        for col in tip300_dict:
            if len(tip300_dict[col]) >= number:
                p300m.pick_up_tip(tips300[str(tip300_dict[col][number-1] + str(col))])
                tip300_dict[col] = tip300_dict[col][number:]
                break

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

def check_params(protocol):
    if start_vol > max_vol:
        protocol.comment(f"Error: Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")
        raise ValueError(f"Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")
    elif plates > 4:
        protocol.comment(f"Combination of inputs exceeds number of plates.")
        raise ValueError(f"Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")

def titrate(protocol):
    metal_wells_in_row = 12
    metal_wells_in_col = 8
    metals_per_96well = 96 / len_titration
    metals_per_row_ = metal_wells_in_row / len_titration
     
    fill_dilutions(protocol)
    # distribute_dilutions(protocol)
    # add_4x_first(protocol)
    # add_4x_metal(protocol)

def fill_dilutions(protocol):
    metals_per_96well = 96 / len_titration # use to select right plate

    for metal in range(0, metals):
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(dilution_vol, sypro2)            
        row = metal % metal_wells_in_col 
        col = metal // metal
        if metal // metals_per_96well < 1:
            metal_plate = deep96_metal1
        elif metal // metals_per_96well < 2:
            metal_plate = deep96_metal2
            row = row - 8
        # elif metal // metals_per_96well < 3:
            metal_plate = deep96_metal3
            row = row - 16
        # elif metal // metals_per_96well < 4:
            metal_plate = deep96_metal4
            row = row - 24
        else:
            protocol.comment("Titration out of range.")
            raise ValueError(f"Titration out of range.")

        p300m.dispense(dilution_vol, metal_plate.rows()[row][col])
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



 