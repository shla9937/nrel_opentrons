from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'ICP-MS mixture',
    'author': 'Shawn Laursen',
    'description': '''
    Plates 24 proteins in triplicate with 3 controls per row, adds mixture of metals, desalts.
    5µM final protein and metal concentration.
    Stock metals should be at 25µM in proper pH buffer (5mL).
    Protein should be at 25µM in proper pH buffer (100µL).
    3.89% ppt nitric acid (125mL).
    Buff (300mL).
    Rxn vol is 150µL.
    Steps:
    -   Add buff
    -   Add metal
    -   Add protein
    -   Incubate (15 min)
    -   Prep desalt plate
    -   Add acid
    -   Add desalted protein to acid
    *use Nunc 96 well deep plates, not Nest''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_buff(protocol)
    add_metal(protocol)    
    add_protein(protocol)
    incubate(protocol) 
    prep_desalt(protocol)
    add_acid(protocol)
    desalt(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global p300m, tips300, tips300_1, desalt_plate, res1, rxn_plate, icp_plate, proteins, res2, trough
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1])
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 1)
    res1 = protocol.load_labware('nest_1_reservoir_195ml', 2)
    rxn_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 5)
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 11)
    proteins = protocol.load_labware('greiner_96_wellplate_300ul', 4)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 8)

    global buff, acid, metal_mix, rxn_vol
    buff = res1.wells()[0]
    acid = res2.wells()[0]
    metal_mix = trough.wells()[0]
    rxn_vol = 150 # needs to be 100 for desalting plus extra to pick up effectively

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    if number == 1:
        p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300, tips300_1])
    elif number > 1 and number < 8:
        p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300, tips300_1])
    else:
        p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300, tips300_1])
    p300m.pick_up_tip()

def add_buff(protocol):
    # add buff to wells 1-9
    pickup_tips(8, p300m, protocol)
    p300m.transfer(rxn_vol*(3/5), buff, rxn_plate.rows()[0][0:9], new_tip='never')

    # add buff to control wells 10-12
    p300m.transfer(rxn_vol*(4/5), buff, rxn_plate.rows()[0][9:12], new_tip='never')
    p300m.return_tip()

def add_metal(protocol):
    # add metal to all wells
    p300m.transfer(rxn_vol*(1/5), metal_mix, rxn_plate.rows()[0][0:12], new_tip='once', trash=False)

def add_protein(protocol):
    # add protein to wells 1-9
    for col in range(3):
        p300m.transfer(rxn_vol*(1/5), proteins.rows()[0][col], rxn_plate.rows()[0][col*3:(col*3)+3], 
                       new_tip='once', trash=False, mix_after=(3,100))

def incubate(protocol):
    global start_time
    start_time = time.time()

def prep_desalt(protocol):
    protocol.pause("Start prepping desalt plate by removing bottom foil, \
        placing on wash plate, removing top seal. Centrifuge 2 min at 1000rcf.")
    protocol.pause("Place desalt plate back in slot 1.")

    pickup_tips(8, p300m, protocol)
    destinations = [well.top() for well in desalt_plate.rows()[0]]
    for wash in range(4):
        p300m.transfer(250, buff, destinations, new_tip='never')
        p300m.move_to(buff.top())
        protocol.pause("Centrifuge desalt plate 2 min at 1000rcf, set on wash plate again, and return to slot 1.")
    p300m.return_tip()
    protocol.pause("Ready to resume protocol.")

def add_acid(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.transfer(900, acid, icp_plate.rows()[0][0:12], new_tip='never')
    p300m.return_tip()

def desalt(protocol):
    if not protocol.is_simulating():
        while time.time() - start_time < 900:
            protocol.delay(1)
    destinations = [well.top() for well in desalt_plate.rows()[0]]
    p300m.transfer(100, rxn_plate.rows()[0][0:12], destinations, new_tip='always', trash=False)
    protocol.pause("Put desalt plate on acid 96 well, centrifuge desalt plate 2 min at 1000rcf.")
