from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'ICP-MS - 12 point 1:2 dilution, 96 well plate',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 8 metals (7 single, 1 mix) in 12 point 1:2 dilution series.
    Starts at 1mM metal concentration goes to 5nM. (1mM, 333µM, 111µM, 37µM, 12.3µM, 4.1µM, 1.37µM, 457nM, 152nM, 51nM, 17nM, 6nM)
    Uses 1µM protein concentration.
    Stock metals should be at 5mM in proper pH buffer.
    Protein should be at 5µM in proper pH buffer.
    Rxn vol is 125µL.
    Steps:
    -   Add protein
    -   Titration metal
    -   Incubate (15 min)
    -   Prep desalt plate
    -   Add acid
    -   Add desalted protein to acid''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_protein(protocol)    
    titrate_metal(protocol)
    incubate(protocol) 
    prep_desalt(protocol)
    add_acid(protocol)
    desalt(protocol)
    add_desalted(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global p300m, tips300, tips300_1, tips300_2, desalt_plate, res1, desalt_elution, rxn_plate, trough, icp_plate, metals, res2
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    tips300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 11)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1, tips300_2])
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 1) # make custom
    res1 = protocol.load_labware('nest_1_reservoir_195ml', 2)
    desalt_elution = protocol.load_labware('nest_96_wellplate_2ml_deep', 8) # make custom
    rxn_plate = protocol.load_labware('greiner_96_wellplate_300ul', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 7)
    metals = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 4)
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 10)

    global protein, buff, acid
    protein = trough.wells()[0]
    buff = res1.wells()[0]
    acid = res2.wells()[0]

def pickup_tips(number, pipette, protocol):
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    if number == 1:
        p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300, tips300_1, tips300_2])
    elif number > 1 and number < 8:
        p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300, tips300_1, tips300_2])
    else:
        p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300, tips300_1, tips300_2])
    p300m.pick_up_tip()

def add_protein(protocol):
    pickup_tips(8, p300m, protocol)
    p300m.transfer(150, buff, rxn_plate.rows()[0][0], new_tip='never')
    p300m.transfer(75, buff, rxn_plate.rows()[0][0:12], new_tip='never')
    p300m.transfer(50, protein, rxn_plate.rows()[0][0], new_tip='never')
    p300m.transfer(25, protein, rxn_plate.rows()[0][1:12], new_tip='never')
    p300m.return_tip()

def titrate_metal(protocol):
    for metal in range(8): 
        pickup_tips(1, p300m, protocol)
        p300m.transfer(50, metals.wells()[metal], rxn_plate.rows()[metal][0], new_tip='never')
        p300m.drop_tip()

    pickup_tips(8, p300m, protocol)
    p300m.transfer(125, rxn_plate.rows()[0][0:10], rxn_plate.rows()[0][1:11], 
                mix_before=(5, 125), new_tip='never')    
    p300m.mix(5, 125, rxn_plate.rows()[0][11])
    p300m.return_tip()

def incubate(protocol):
    global start_time
    start_time = time.time()

def prep_desalt(protocol):
    protocol.pause("Start prepping desalt plate by removing bottom foil, \
        placing on wash plate, removing top seal. Centrifuge 2 min at 1000rcf.")
    protocol.pause("Place desalt plate in slot 1.")

    pickup_tips(8, p300m, protocol)
    for wash in range(4):
        p300m.transfer(250, buff, desalt_plate.rows()[0][0:12], new_tip='never')
        protocol.pause("Centrifuge desalt plate 2 min at 1000rcf, swap wash plate for elution plate, and return to slot 1.")
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
    p300m.transfer(100, rxn_plate.rows()[0][0:12], desalt_plate.rows()[0][0:12], new_tip='always', trash=False)
    protocol.pause("Centrifuge desalt plate 2 min at 1000rcf and return elution plate to slot 4.")

def add_desalted(protocol):
    protocol.pause("Ensure desalt elution plate is in slot 4.")
    p300m.transfer(100, desalt_elution.rows()[0][0:12], icp_plate.rows()[0][0:12], new_tip='always', trash=False)