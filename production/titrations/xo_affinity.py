from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'XO affinity assay - 12 point 1:1 dilution, 384 well plate',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 16 metals in 12 point 1:1 dilution series.
    5µM metal concentration.
    10µM xylenol orange concentration.
    Titrate protein concentration from 62.5µM.
    20mM MES.''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_str(
        variable_name="side",
        display_name="Side of plate",
        description="Left or right side of plate",
        choices=[
            {"display_name": "Left", "value": 0},
            {"display_name": "Right", "value": 12}],
         default="flex_1channel_50")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    make_high(protocol)
    make_low(protocol)
    add_protein(protocol) 
    titrate(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, tubes, p20m, plate, p300m, tips300, dirty_tips20, dirty_tips300, metals, dilution_plate
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    metals = protocol.load_labware('nest_96_wellplate_2ml_deep', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)  
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    dilution_plate = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    # reagents
    global protein, buff, water, side
    protein = tubes.wells()[0]
    buff = trough.wells()[0]
    water = trough.wells()[1]
    side = protocol.params.side

    #single tips
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
        tip_300 += number

def return_tips(pipette):
    if pipette == p20m:
        # p20m.configure_nozzle_layout(style=ALL)
        p20m.drop_tip(dirty_tips20.wells()[last_tip20])
    elif pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def make_high(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.distribute(166.5, buff, dilution_plate.rows()[0][0:4], new_tip='never')
    return_tips(p300m)
    
    for i in [0,1]:
        pickup_tips(8, p20m, protocol)
        p20m.transfer(6.7, metals.rows()[0][i], dilution_plate.rows()[0][i*2], mix_after=(5,20), new_tip='never')
        p20m.transfer(6.7, dilution_plate.rows()[0][i*2], dilution_plate.rows()[0][1+(2*i)], mix_after=(5,20), new_tip='never')
        p20m.transfer(25, dilution_plate.rows()[0][1+(2*i)], plate.rows()[i][0+side], new_tip='never')
        return_tips(p20m)

def make_low(protocol):
    for i in [0,1]:
        pickup_tips(8, p300m, protocol)
        p300m.transfer(148.2, water, dilution_plate.rows()[0][(i*2)+1], mix_after=(3,250) new_tip='never')
        p300m.distribute(25, dilution_plate.rows()[0][(i*2)+1], plate.rows[i][1+side:12+side], new_tip='never')
        return_tips(p300m)

def add_protein(protocol):
    for i in range(0,16):
        pickup_tips(1, p300m, protocol)
        p300m.transfer(25, protein, plate.rows()[i][0+side], mix_after=(3, 25), new_tip='never')
        p300m.drop_tip()

def titrate(protocol):
    for i in [0,1]:
        pickup_tips(8, p300m, protocol)
        p300m.transfer(25, plate.rows()[i][0+side:10+side], plate.rows()[i][1+side:11+side], 
                    mix_after=(5, 25), new_tip='never')
        p300m.aspirate(25, plate.rows()[i][10+side])
        return_tips(p300m)



