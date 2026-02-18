from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'ICP-MS - desalt',
    'author': 'Shawn Laursen',
    'description': '''
    Preps desalt plate and transfers all but last row to desalt plate. 
    3.89% ppt nitric acid (125mL).
    Buff (200mL).
    Rxn vol is 150µL.
    Steps:
    -   Prep desalt plate
    -   Add acid
    -   Add desalted protein to acid
    *use Nunc 96 well deep plates, not Nest''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    prep_desalt(protocol)
    add_acid(protocol)
    desalt(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global p20, p300m, tips20, tips300, tips300_1, desalt_plate, buff, rxn_plate, icp_plate, metals, res2
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1])
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 1)
    buff = protocol.load_labware('nest_96_wellplate_2ml_deep', 2)
    rxn_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 5)
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 11)
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 8)

    global acid
    acid = res2.wells()[0]

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    if number == 1:
        p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300, tips300_1])
    elif number > 1 and number < 8:
        p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300, tips300_1])
    else:
        p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300, tips300_1])
    p300m.pick_up_tip()

def prep_desalt(protocol):
    protocol.pause("Start prepping desalt plate by removing bottom foil, \
        placing on wash plate, removing top seal. Centrifuge 2 min at 1000rcf.")
    protocol.pause("Place desalt plate back in slot 1.")

    for wash in range(4):
        pickup_tips(8, p300m, protocol)
        for col in range(6):
            p300m.transfer(250, buff.rows()[0][col], desalt_plate.rows()[0][col].top(), new_tip='never')
        p300m.drop_tip()
        pickup_tips(8, p300m, protocol)
        for col in range(6,12):
            p300m.transfer(250, buff.rows()[0][col], desalt_plate.rows()[0][col].top(), new_tip='never')
        p300m.drop_tip()
        p300m.move_to(buff.rows()[0][0].top())
        protocol.pause("Centrifuge desalt plate 2 min at 1000rcf, set on wash plate again, and return to slot 1.")
    protocol.pause("Ready to resume protocol.")

def add_acid(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.transfer(900, acid, icp_plate.rows()[0][0:12], new_tip='never')
    p300m.return_tip()

def desalt(protocol):
    for col in range(12):
        pickup_tips(7, p300m, protocol)
        p300m.transfer(100, rxn_plate.rows()[6][col], desalt_plate.rows()[6][col].top(), new_tip='never', trash=False)
        p300m.drop_tip()
        pickup_tips(1, p300m, protocol)
        p300m.transfer(100, rxn_plate.rows()[7][col], icp_plate.rows()[7][col].top(), new_tip='never', trash=False)
        p300m.drop_tip()
    protocol.pause("Put desalt plate on acid 96 well, centrifuge desalt plate 2 min at 1000rcf.")
