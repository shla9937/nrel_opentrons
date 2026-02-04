from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'ICP-MS - 6 x 12 point 1:1.5 protein dilution, 96 well plate',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 6 metals (6 single titrations, with 3 controls for each, 6 WT controls) in 12 point 1:2 dilution series.
    Starts at 100µM protein concentration goes to 1µM. (100µM, 66.6µM, 44.4µM, 29.6µM, 19.7µM, 13.1µM, 8.8µM, 5.9µM, 3.9µM, 2.6µM, 1.7µM, 1.2µM)
    5µM final metal concentration.
    Stock metals should be at 25µM in proper pH buffer (>400µL).
    Protein should be at 200µM in proper pH buffer ().
    3.89% ppt nitric acid (125mL).
    Buff (200mL).
    Rxn vol is 125µL.
    Steps:
    -   Add metal
    -   Titration protein
    -   Make controls
    -   Incubate (15 min)
    -   Prep desalt plate
    -   Add acid
    -   Add desalted protein to acid
    *use Nunc 96 well deep plates, not Nest''',
    'apiLevel': '2.26'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_metal(protocol)
    add_buff(protocol)    
    titrate_protein(protocol)
    incubate(protocol) 
    prep_desalt(protocol)
    add_acid(protocol)
    desalt(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global p20m, p300m, tips20, tips300, tips300_1, desalt_plate, res1, rxn_plate, icp_plate, metals, res2
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 7)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1])
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 1)
    res1 = protocol.load_labware('nest_1_reservoir_195ml', 2)
    rxn_plate = protocol.load_labware('greiner_96_wellplate_300ul', 5)
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 11)
    metals = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 4)
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 8)

    global protein, buff, acid
    protein = metals.wells()[8]
    buff = res1.wells()[0]
    acid = res2.wells()[0]

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
            p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300, tips300_1])
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300, tips300_1])
        else:
            p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300, tips300_1])
        p300m.pick_up_tip()

def add_metal(protocol):
    # add 5µM metal to top 6 rows
    for metal in range(6): 
        pickup_tips(1, p300m, protocol)
        p300m.transfer(90, metals.wells()[metal], rxn_plate.rows()[metal][0], new_tip='never', 
                        mix_before=(3,100))
        p300m.transfer(30, metals.wells()[metal], rxn_plate.rows()[metal][1:12], new_tip='never')
        p300m.transfer(30, metals.wells()[metal], rxn_plate.rows()[6][metal*2:(metal*2)+2], new_tip='never')
        p300m.drop_tip()
    
    # add mix to control wells
    pickup_tips(1, p300m, protocol)
    p300m.transfer(30, metals.wells()[6], rxn_plate.rows()[7][0:6], new_tip='never', 
                    mix_before=(3,100))
    p300m.drop_tip()

    # add EDTA to control wells
    pickup_tips(1, p300m, protocol)
    p300m.transfer(30, metals.wells()[7], rxn_plate.rows()[7][6:9], new_tip='never', 
                    mix_before=(3,100))
    p300m.drop_tip()

def add_buff(protocol):
    # add buff to top 6 rows
    pickup_tips(6, p300m, protocol)
    p300m.transfer(135, buff, rxn_plate.rows()[5][0].bottom(10), new_tip='never')
    for col in range(1,12):
        p300m.transfer(120, buff, rxn_plate.rows()[5][col].bottom(10), new_tip='never')
    p300m.drop_tip()
   
    # add buff to controls
    pickup_tips(1, p300m, protocol)
    for col in range(12): 
        p300m.transfer(120, buff, rxn_plate.rows()[6][col].bottom(10), new_tip='never')
    
    # add buff to bottom row
    for col in range(3): 
        p300m.transfer(120, buff, rxn_plate.rows()[7][col].bottom(10), new_tip='never')
    for col in range(3,9):     
        p300m.transfer(116.25, buff, rxn_plate.rows()[7][col].bottom(10), new_tip='never')
    for col in range(9,12): 
        p300m.transfer(146.25, buff, rxn_plate.rows()[7][col].bottom(10), new_tip='never')
    p300m.drop_tip()

def titrate_protein(protocol):
    # put protein in top 6 rows
    for metal in range(6): 
        pickup_tips(1, p300m, protocol)
        p300m.transfer(225, protein, rxn_plate.rows()[metal][0], new_tip='never', mix_after=(3,100))
        p300m.drop_tip()

    # titrate protein
    pickup_tips(6, p300m, protocol)
    p300m.transfer(300, rxn_plate.rows()[5][0:11], rxn_plate.rows()[5][1:12], 
                mix_before=(5,225), new_tip='never')    
    p300m.mix(5,255, rxn_plate.rows()[0][11])
    p300m.drop_tip()

    # add protein to bottom row
    for well in range(3,12): 
        pickup_tips(1, p20m, protocol)
        p20m.transfer(3.75, protein, rxn_plate.rows()[metal][0], new_tip='never', 
                        mix_before=(3,20), mix_after=(3,20))
        p20m.drop_tip()

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
