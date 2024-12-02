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
        display_name="Number of samples",
        description="Number of proteins to test",
        default=1,
        minimum=1,
        maximum=8,
        unit="proteins")
    parameters.add_int(
        variable_name="metals",
        display_name="Number of metals",
        description="Number of metals/titrations to be screened",
        default=16,
        minimum=1,
        maximum=16,
        unit="metals")
    parameters.add_int(
        variable_name="len_titration",
        description="Number of wells in titration",
        display_name="Length of titration",
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
    parameters.add_int(
        variable_name="temp",
        display_name="Temp deck temperature",
        description="Temp to keep proteins at in C.",
        default=23,
        minimum=4,
        maximum=100,
        unit="C")

def run(protocol):
    protocol.set_rail_lights(True)
    # tempdeck.set_temperature(celsius=protocol.params.temp)
    setup(protocol)
    check_params(protocol)
    titrate(protocol)
    add_protein(protocol)
    add_titration(protocol)
    message(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tempdeck, temp_buffs, rt_5ml, deep96_prot, metal_plate, \
           tips300, tips20, pcr1, pcr2, pcr3, pcr4, p300m, p20m
    tempdeck = protocol.load_module('temperature module gen2', 1)
    temp_buffs = tempdeck.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    rt_5ml = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 4)
    metal_plate = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 5)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 3)
    pcr1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 6)
    pcr2 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 7)
    pcr3 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 10)
    pcr4 = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 11)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    
    # plates
    global plates_loc
    plates_loc = [pcr1, pcr2, pcr3, pcr4]

    # reagents
    global sypro2, sypro4
    sypro2 = rt_5ml.wells()[0].top(-95)
    sypro4 = rt_5ml.wells()[1].top(-95)
    
    # set up plates
    global steepness, rxn_vol, samples, metals, len_titration, max_vol, wells_in_row, \
           wells_in_col, wells_in_plate, metals_loc
    steepness = protocol.params.steepness
    rxn_vol = protocol.params.rxn_vol
    samples = protocol.params.samples
    metals = protocol.params.metals
    len_titration = protocol.params.len_titration
    max_vol = 2000 # max volume of deepwell block
    wells_in_row = 12 # in rxn plate, later this will change to 24 for 384 well
    wells_in_col = 8 # in rxn plate, later this will change to 16 for 384 well
    wells_in_plate = wells_in_col * wells_in_row
    samples_loc = [temp_buffs.wells()[i] for i in range(0, samples)]
    metals_loc = [temp_buffs.wells()[i] for i in range(samples, metals+samples)]

    # find out how many pcr plates are needed
    global titrations_per_row, titrations_per_plate, plates, titrations
    titrations_per_row = len_titration // wells_in_row
    titrations_per_plate = titrations_per_row * wells_in_col
    plates = (samples * metals) / titrations_per_plate
    titrations = metals * samples

    # tips
    global tip20_dict, tip300_dict
    tip20_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    # tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    tip300_dict = {key: ['A','B','C','D','E','F','G','H'] for key in range(1, 12 + 1)}

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
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
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
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
         
def check_params(protocol):
    True
    # if start_vol > max_vol:
    #     protocol.comment(f"Error: Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")
    #     raise ValueError(f"Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")
    # if metals > metals_per_plate:
    #     protocol.comment("Combination of metals and length of titration exceeds max.")
    #     raise ValueError("Combination of metals and length of titration exceeds max.")
    # elif plates > 4:
    #     protocol.comment("Combination of inputs exceeds number of plates.")
    #     raise ValueError(f"Starting volume ({start_vol}) exceeds maximum of {max_vol}µL.")

def titrate(protocol):
    dil_vol = (samples * (rxn_vol / 2)) + 20 # 40
    titration_dil_vol = dil_vol * (len_titration - 1) # 200
    start_vol = (dil_vol * steepness) + (samples * (rxn_vol / 2)) + 20 # 40 + 20 + 20
    transfer_vol = dil_vol * steepness # 40
    
    # set up metal plates
    global metal_cols, metal_rows, metal_wells, metals_per_row, metals_per_plate
    metal_cols = 12
    metal_rows = 8
    metal_wells = metal_rows * metal_cols
    metals_per_row = len_titration // metal_cols
    metals_per_plate = metals_per_row * metal_rows

    # add 2x spyro to last well of deep well
    pickup_tips(1, p300m, protocol)
    for metal in range(0, metals):
        p300m.aspirate(titration_dil_vol, sypro2)
        row = metal % metal_rows
        col = ((metal // metal_rows) * len_titration) + (len_titration - 1)
        p300m.dispense(titration_dil_vol, metal_plate.rows()[row][col])
    p300m.drop_tip()

    # distribute spyro to 4 other wells
    for metal in range(0, metals):
        if (metal + 1) % metal_rows == 0:
            pickup_tips(8, p300m, protocol)
            for j in range(1, len_titration - 1):
                stock = ((metal // metal_rows) * len_titration) + (len_titration - 1)
                col = ((metal // metal_rows) * len_titration) + j
                p300m.aspirate(dil_vol, metal_plate.rows()[0][stock])
                p300m.dispense(dil_vol, metal_plate.rows()[0][col])
            p300m.drop_tip()
    if metals % 8 != 0:
        num_tips = metals % 8
        pickup_tips(num_tips, p300m, protocol)
        metal = metals - 1
        for j in range(1, len_titration - 1):
            stock = ((metal // metal_rows) * len_titration) + (len_titration - 1)
            col = ((metal // metal_rows) * len_titration) + j
            p300m.aspirate(dil_vol, metal_plate.rows()[0][stock])
            p300m.dispense(dil_vol, metal_plate.rows()[0][col])
        p300m.drop_tip()
 
    # num_tips = metals % 8
    # if num_tips == 0:
    #     num_tips = 8

    # pickup_tips(num_tips, p300m, protocol)
    # for j in range(1, len_titration - 1):
    #     stock = ((metals // metal_rows)  * len_titration) + (len_titration - 1)
    #     col = ((metals // metal_rows) * len_titration) + j
    #     p300m.aspirate(dil_vol, metal_plate.rows()[0][stock])
    #     p300m.dispense(dil_vol, metal_plate.rows()[0][col])
    # p300m.drop_tip()

    # # add 4x sypro to the first well
    # pickup_tips(1, p300m, protocol)
    # spyro4_vol = (dil_vol + transfer_vol) / 2
    # for metal in range(0, metals):
    #     p300m.aspirate(spyro4_vol, sypro4)            
    #     row = metal % metal_rows 
    #     col = (metal // metal_rows) * len_titration
    #     p300m.dispense(transfer_vol, metal_plate.rows()[row][col])
    # p300m.drop_tip()

    # # add_4x_metal(protocol) 
    # metal_vol = spyro4_vol
    # for metal in range(0, metals):
    #     pickup_tips(1, p300m, protocol)
    #     p300m.aspirate(metal_vol, metals_loc[metal])            
    #     row = metal % metal_rows 
    #     col = (metal // metal_rows) * len_titration
    #     p300m.dispense(metal_vol, metal_plate.rows()[row][col])
    #     p300m.drop_tip()

    # # titrate 10 rxn + 10 rxn + 20 extra
    # if metals > 8:
    #     for i in range(0, (metals // 8) - 1):
    #         pickup_tips(8, p300m, protocol)
    #         col = (metal // metal_rows) * len_titration
    #         p300m.transfer(transfer_vol,metal_plate.rows()[0][col:col+len_titration-2],
    #                     metal_plate.rows()[0][col+1:col+len_titration-1],
    #                     mix_after=(3, 20), new_tip='never')
    #         p300m.aspirate(40, metal_plate.rows()[0][len_titration-2])
    #         p300m.drop_tip()




def add_protein(protocol): # add 10µL of protein
    True
#     # for each sample, pipette into first well
#     for sample in range(0, samples):
#         for metal in range(0, metals):
#             pickup_tips(1, p300m, protocol)
#             p300m.aspirate(60, samples_loc[sample])            
#             row = metal % 8 
#             col = (metal // 8) + (sample * 6)
#             p300m.dispense(60, pcr1.rows()[row][col])
#             p300m.drop_tip()

#     # pick up eight tips (eventually change to number of metals) and distrribute
#     for sample in range(0, samples):
#         pickup_tips(8, p300m, protocol) # change to "metals" later, accounting for > 8
#         col = sample * 6
#         p300m.distribute(10, pcr1.rows()[0][col],
#                     pcr1.rows()[0][col+1:col+len_titration],
#                     disposal_volume=0, new_tip='never')
#         p300m.drop_tip()

def add_titration(protocol): # add 10µL of titration
    True
#     # plate titration into each sample, go from least to most, only to top
#     pickup_tips(8, p20m, protocol) # need to adjust to metals later
#     for col in range(len_titration -1 , -1, -1):
#         row = 0
#         p20m.aspirate(20, metal_plate.rows()[row][col])
#         for sample in range(0, samples):
#             pcr_col = col + (sample * 6)
#             p20m.dispense(10, pcr1.rows()[row][pcr_col].top(-3))
#     p20m.drop_tip()

def message(protocol):
    True
#     protocol.pause(msg="Protcol complete, please spin plate and equillibrate for 30 \
#                         before thermocycling.")
