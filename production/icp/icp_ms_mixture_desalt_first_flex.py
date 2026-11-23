from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'ICP-MS mixture - desalt first',
    'author': 'Shawn Laursen',
    'description': '''
    Plates 24 proteins in triplicate with 3 controls per row, adds mixture of metals, desalts, then adds nitric.
    5µM final protein and metal concentration.
    Stock metals should be at 25µM in proper pH buffer (5mL).
    Protein should be at 25µM in proper pH buffer (100µL).
    5.55% ppt nitric acid (125mL).
    Buff (150mL).
    Rxn vol is 150µL.
    Steps:
    -   Add buff
    -   Add metal
    -   Add protein
    -   Incubate (15 min)
    -   Prep desalt plate
    -   Desalt protein
    -   Add acid
    *use Nunc 96 well deep plates, not Nest'''}
requirements = {'robotType': 'Flex','apiLevel': '2.29'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_buff(protocol)
    add_metal(protocol)    
    add_protein(protocol)
    incubate(protocol) 
    prep_desalt(protocol)
    desalt(protocol)
    add_acid(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global tips1000,tips200, pipette, desalt_plate, rxn_plate, icp_plate, proteins, trash
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A2')
    tips200 = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A1', adapter='opentrons_flex_96_tiprack_adapter')
    pipette = protocol.load_instrument('flex_96channel_1000')
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 'C1')
    res1 = protocol.load_labware('nest_1_reservoir_195ml', 'B1')
    rxn_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C2')
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 'D2')
    proteins = protocol.load_labware('greiner_96_wellplate_300ul', 'C3')
    trough = protocol.load_labware('nest_12_reservoir_15ml', 'B2')
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 'B3')
    trash = protocol.load_trash_bin ('D1')

    global buff, acid, metal_mix, rxn_vol
    buff = res1.wells()[0]
    acid = res2.wells()[0]
    metal_mix = trough.wells()[0]
    rxn_vol = 150 # needs to be 100 for desalting plus extra to pick up effectively

def define_liquids(protocol):
    buff_liquid = protocol.define_liquid(
        name="Buff",
        description="Buff",
        display_color="#405DBC")
    buff.load_liquid(liquid=buff_liquid,volume=195000)

    acid_liquid = protocol.define_liquid(
        name="Acid",
        description="5% ppt nitric acid",
        display_color="#24D921")
    acid.load_liquid(liquid=acid_liquid,volume=125000)

    metal_liquid = protocol.define_liquid(
        name="Metal mix",
        description="Metal mix",
        display_color="#DDDA30")
    metal_mix.load_liquid(liquid=metal_liquid,volume=5000)

    protein_liquid = protocol.define_liquid(
        name="Protein",
        description="25µM proteins",
        display_color="#8C35CA")
    for row in proteins.rows()[0:8]:
        for well in row[0:3]:
            well.load_liquid(liquid=protein_liquid, volume=150)


def add_buff(protocol):
    # add buff to wells 1-9
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A1", tip_racks=[tips1000])
    pipette.pick_up_tip()
    pipette.distribute(rxn_vol*(3/5), buff, rxn_plate.rows()[0][0:9], new_tip='never', disposal_volume=30)

    # add buff to control wells 10-12
    pipette.distribute(rxn_vol*(4/5), buff, rxn_plate.rows()[0][9:12], new_tip='never', disposal_volume=30)

def add_metal(protocol):
    # add metal to all wells
    pipette.distribute(rxn_vol*(1/5), metal_mix, rxn_plate.rows()[0][0:12], new_tip='never', disposal_volume=30)
    pipette.drop_tip()

def add_protein(protocol):
    # add protein to wells 1-9
    for col in range(3):
        pipette.transfer(rxn_vol*(1/5), proteins.rows()[0][col], rxn_plate.rows()[0][col*3:(col*3)+3], 
                       new_tip='once', mix_before=(1,rxn_vol*(1/5)), mix_after=(3,rxn_vol*(1/5)))

def incubate(protocol):
    global start_time
    start_time = time.time()

def prep_desalt(protocol):
    protocol.pause("Start prepping desalt plate by removing bottom foil, \
        placing on wash plate, removing top seal. Centrifuge 2 min at 1000rcf.")
    protocol.pause("Place desalt plate back in slot 1.")

    pipette.pick_up_tip()
    destinations = [well.top() for well in desalt_plate.rows()[0]]
    for wash in range(4):
        pipette.distribute(250, buff, destinations, new_tip='never')
        pipette.move_to(buff.top())
        protocol.pause("Centrifuge desalt plate 2 min at 1000rcf, set on wash plate again, and return to slot 1.")
    pipette.drop_tip()
    protocol.pause("Ready to resume protocol.")

def desalt(protocol):
    if not protocol.is_simulating():
        while time.time() - start_time < 900:
            protocol.delay(1)
    pipette.configure_nozzle_layout(style=protocol_api.ALL, tip_racks=[tips200])
    pipette.transfer(100, rxn_plate.rows()[0][0], desalt_plate.rows()[0][0].top(), new_tip='once', touch_tip=True)
    protocol.pause("Put desalt plate on collection deep 96 well (D2), centrifuge desalt plate 2 min at 1000rcf.")
    protocol.pause("Return plate to D2 for acid addition.")

def add_acid(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A1", tip_racks=[tips1000])
    pipette.pick_up_tip()
    for well in icp_plate.rows()[0][0:12]:
        pipette.transfer(900, acid, well.top(), new_tip='never')
    pipette.drop_tip()