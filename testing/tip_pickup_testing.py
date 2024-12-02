from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
import time
import sys
import math
import random
import subprocess

metadata = {
    'protocolName': 'Tip pickup test',
    'author': 'Shawn Laursen',
    'description': '''New tip pickup test''',
    'apiLevel': '2.20'
    }

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    new_p300_without_tracking(protocol)
    new_p300_with_tracking(protocol)
    new_targeting(protocol)
    new_p20_single(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips300_partial, tips300, tips20, p300m, p20m, plate, tip300_dict
    tips300_partial = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 6)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_partial])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])    
    plate = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul', 8)
    
    # tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    tip300_dict = {key: ['A','B','C','D','E','F','G','H'] for key in range(1, 12 + 1)}

def track_pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    if number > 8 or number < 1 or pipette not in [p300m]:
        protocol.comment(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
        raise ValueError(f"Custom tip pick up function doesn't support combination of \
                           {pipette} for pipette and {number} for tips.")
    elif pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        for col in tip300_dict:
            if len(tip300_dict[col]) >= number:
                p300m.pick_up_tip(tips300_partial[str(tip300_dict[col][number-1] + str(col))])
                tip300_dict[col] = tip300_dict[col][number:]
                break
    else:
        protocol.comment("Custom tip pick up function doesn't recognize inputs.")
        raise ValueError("Custom tip pick up function doesn't recognize inputs.")

def new_p300_without_tracking(protocol):
    p300m.configure_nozzle_layout(style=SINGLE,start="H1")
    p300m.pick_up_tip(tips300)
    protocol.delay(seconds=5)
    p300m.drop_tip()
    p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end="E1")
    p300m.pick_up_tip(tips300)
    protocol.delay(seconds=5)
    p300m.drop_tip()
    p300m.configure_nozzle_layout(style=ALL)
    p300m.pick_up_tip(tips300)
    protocol.delay(seconds=5)
    p300m.drop_tip()

def new_p300_with_tracking(protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    p300m.configure_nozzle_layout(style=SINGLE,start="H1")
    for col in tip300_dict:
        if len(tip300_dict[col]) >= 1:
            p300m.pick_up_tip(tips300_partial[str(tip300_dict[col][1-1] + str(col))])
            tip300_dict[col] = tip300_dict[col][1:]
            break
    protocol.delay(seconds=5)
    p300m.drop_tip()
    p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[4])
    for col in tip300_dict:
        if len(tip300_dict[col]) >= 4:
            p300m.pick_up_tip(tips300_partial[str(tip300_dict[col][4-1] + str(col))])
            tip300_dict[col] = tip300_dict[col][4:]
            break
    protocol.delay(seconds=5)
    p300m.drop_tip()
    p300m.configure_nozzle_layout(style=ALL)
    for col in tip300_dict:
        if len(tip300_dict[col]) >= 8:
            p300m.pick_up_tip(tips300_partial[str(tip300_dict[col][8-1] + str(col))])
            tip300_dict[col] = tip300_dict[col][8:]
            break
    protocol.delay(seconds=5)
    p300m.drop_tip()

def new_targeting(protocol):
    p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end="E1")
    p300m.pick_up_tip(tips300)
    p300m.aspirate(100, plate.rows()[0][0])
    p300m.dispense(100, plate.rows()[0][6])
    p300m.drop_tip()    

def new_p20_single(protocol):
    p20m.configure_nozzle_layout(style=SINGLE,start="H1")
    p20m.pick_up_tip(tips20)
    protocol.delay(seconds=5)
    p20m.drop_tip()