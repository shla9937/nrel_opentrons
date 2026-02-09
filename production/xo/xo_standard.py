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
    Makes 2 x 10 point (1:1) standard curve for Lanthanide (put ~200µL in A1 of dilution plate).
    Put buffer (20mM MES in trough well 1).
    Adds samples in duplicate to 96 optical plate (start in 96 well plate).
    Adds 200µL of xylenol orange to each well (100µM in trough well 2).
    ''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="start_col",
        display_name="Column to start in",
        description="Which column to start with (first unused column).",
        default=1,
        minimum=1,
        maximum=12,)
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples",
        description="Number of samples (will be plated in duplicate).",
        default=1,
        minimum=1,
        maximum=40,)

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_xo(protocol)
    make_standard_curve(protocol)
    add_samples(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global trough, sample_plate, plate, p300m, tips300, dirty_tips300, dilution_plate
    sample_plate = protocol.load_labware('greiner_96_wellplate_300ul', 2)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 5)  
    trough = protocol.load_labware('nest_12_reservoir_15ml', 4)
    dilution_plate = protocol.load_labware('greiner_96_wellplate_300ul', 8)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    # reagents
    global buff, xo, samples, start_col
    buff = trough.wells()[0]
    xo = trough.wells()[1]
    start_col = protocol.params.start_col - 1 
    samples = protocol.params.samples

    #single tips
    global tip_300
    tip_300 = 0

def pickup_tips(number, pipette, protocol):
    global last_tip300, tip_300
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}

    if pipette == p300m:
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
    if pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def add_xo(protocol):
    pickup_tips(8, p300m, protocol)
    for i in range(2):
        p300m.transfer(200, xo, plate.columns()[i][0], new_tip='never')

    for i in range(samples // 8):
        p300m.transfer(200, xo, plate.columns()[i+2][0], new_tip='never')
    return_tips(p300m)

    pickup_tips(samples % 8, p300m, protocol)
    if samples % 8 != 0:
        p300m.transfer(200, xo, plate.columns()[samples // 8 + 2][samples % 8], new_tip='never')
    p300m.drop_tip()

def make_standard_curve(protocol):    
    for i in range(2):
        pickup_tips(1, p300m, protocol)
        for well in range(1,8):
            p300m.transfer(100, buff, dilution_plate.columns()[start_col+i][well], new_tip='never')
        for well in range(1,8):
            p300m.transfer(100, dilution_plate.columns()[start_col+i][well-1], dilution_plate.columns()[start_col+i][well], new_tip='never', mix_after=(3, 100))
        p300m.drop_tip()
        pickup_tips(8, p300m, protocol)
        p300m.transfer(100, dilution_plate.columns()[start_col+i][0], plate.columns()[start_col+i][0], new_tip='never', mix_after=(3,100))
        return_tips(p300m)

def add_samples(protocol):
    for i in range(samples // 8):
        pickup_tips(8, p300m, protocol)
        p300m.transfer(20, sample_plate.columns()[i][0], plate.columns()[i+2][0], mix_after=(3, 200), new_tip='never')
        return_tips(p300m)

    pickup_tips(samples % 8, p300m, protocol)
    if samples % 8 != 0:
        p300m.transfer(20, sample_plate.columns()[samples // 8][samples % 8], plate.columns()[samples // 8 + 2][samples % 8], mix_after=(3, 200), new_tip='never')
    p300m.drop_tip()