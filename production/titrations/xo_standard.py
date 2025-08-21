from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'XO standards',
    'author': 'Shawn Laursen',
    'description': '''
    Makes 3x 12 point standard curve for Lanthanide.
    Adds samples in triplicate to 96 well plate.
    Adds xylenol orange to each well.
    ''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="start_row",
        display_name="Row to start in",
        description="First row of titration will start here.",
        default=1,
        minimum=1,
        maximum=5,)
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples",
        description="Number of samples (will be plated in triplicate).",
        default=1,
        minimum=1,
        maximum=20,)

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    make_standard_curve(protocol)
    add_samples(protocol)
    add_xo(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, tubes, p20m, plate, p300m, tips300, dirty_tips20, dirty_tips300, metals, dilution_plate
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    dilution_plate = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5)  
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    # reagents
    global buff, xo, standard, samples, start_row
    buff = trough.wells()[0]
    standard = trough.wells()[1]
    xo = trough.wells()[2]
    samples = tubes.wells()[0:protocol.params.samples]
    start_row = protocol.params.start_row - 1 

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

def make_standard_curve(protocol):
    pickup_tips(3, p300m, protocol)
    dilute_vol = 0
    for i in range(10):
        p300m.transfer(dilute_vol, buff, dilution_plate.rows()[start_row+3][i], new_tip='never')
        dilute_vol += 10
    p300m.transfer(100, buff, dilution_plate.rows()[start_row+3][10:12], new_tip='never')
    return_tips(p300m)

    pickup_tips(3, p300m, protocol)
    standard_vol = 100
    for i in range(10):
        p300m.transfer(standard_vol, standard, dilution_plate.rows()[start_row+3][i], new_tip='never', mix_after=(3, 50))
        p300m.transfer(12.5, dilution_plate.rows()[start_row+3][i], plate.rows()[start_row+3][i], new_tip='never')
        dilute_vol -= 10
    return_tips(p300m)

def add_samples(protocol):
    for sample in samples:
        pickup_tips(1, p20m, protocol)
        p20m.transfer(12.5, sample.bottom(8), plate.rows()[start_row+4][0:3], new_tip='never')

def add_xo(protocol):