from opentrons import protocol_api
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'TnT protein expression',
    'author': 'Shawn Laursen',
    'description': '''Protocol: 
    -   At 4°C
    -   Add mix
    -   Add Methionine
    -   Add DNA
    -   Add water
    -   Incuate at 30°C for 60-90 min
    -   Return to 4°C''',
    'apiLevel': '2.20'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples",
        description="Number of proteins to be expressed.",
        default=1,
        minimum=1,
        maximum=96,
        unit="samples")
    parameters.add_int(
        variable_name="rxn_vol",
        display_name="Reaction size",
        description="Amount of TnT mix to add to each.",
        default=20,
        minimum=10,
        maximum=100,
        unit="µL")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    reconstitute_dna(protocol)
    add_rxn_mix(protocol)
    add_dna(protocol)
    incubate(protocol)
    # purify(protocol)
    protocol.set_rail_lights(False)

def strobe(blinks, hz, leave_on, protocol):
    i = 0
    while i < blinks:
        protocol.set_rail_lights(True)
        time.sleep(1/hz)
        protocol.set_rail_lights(False)
        time.sleep(1/hz)
        i += 1
    protocol.set_rail_lights(leave_on)

def setup(protocol):
    # equiptment
    global tips300, tips20, p300m, p20m
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 2)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20]) 
    twist_plate = protocol.load_labware('greiner_96_wellplate_300ul', 5)
    tempdeck1 = protocol.load_module('temperature module gen2', 1)
    temp_buffs24 = tempdeck1.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    tempdeck2 = protocol.load_module('temperature module gen2', 4)
    temp_plate = tempdeck2.load_labware()
    trough = protocol.load_labware(),6)

    # reagents

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

    elif pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        p300m.pick_up_tip(tips300)

def reconstitute_dna(protocol):
    
    True
def add_rxn_mix(protocol):
    True
def add_dna(protocol):
    True
def incubate(protocol):
    True