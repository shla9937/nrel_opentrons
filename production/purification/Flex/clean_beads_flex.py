from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Magnetic purification - 24well',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 24 well plate using StrepXT mag beads'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_naoh(protocol)
    wash_beads(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, empty_tiprack, tips1000_24well, tips24_adapter, wash_buff, naoh, mag_24well, bead_plate, liquid_waste
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A2')

    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    naoh = protocol.load_labware('nest_1_reservoir_195ml', 'B2')

    liquid_waste = protocol.load_labware('nest_1_reservoir_195ml', 'C1')
    mag_24well = protocol.load_adapter('shawn_24well_magnet_adapter', 'C2')
    wash_buff = protocol.load_labware('nest_1_reservoir_195ml', 'C3')

    trash = protocol.load_trash_bin ('D1')
    bead_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D2')    
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
    
    pipette = protocol.load_instrument('flex_96channel_1000')

    global half_filled
    half_filled = False

def define_liquids(protocol):
    wash_liquid = protocol.define_liquid(
        name="wash_buff",
        description="Wash buff",
        display_color="#405DBC")
    wash_buff['A1'].load_liquid(liquid=wash_liquid,volume=195000)

    naoh_liquid = protocol.define_liquid(
        name="100mM NaOH",
        description="NaOH for regeneration",
        display_color="#F62A18")
    for well in naoh.wells():
        well.load_liquid(liquid=naoh_liquid, volume=195000)

def pickup_24(protocol):
    global half_filled
    try:
        protocol.move_labware(tips1000_24well, "A1", use_gripper=True)
    except:
        None

    if half_filled is False:
        pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000])
        for row in range(4):
            pipette.pick_up_tip()
            pipette.drop_tip(empty_tiprack.rows()[row*2][0])
        half_filled = True
    else:    
        half_filled = False

    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col])
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])

def add_naoh(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    pickup_24(protocol)
    pipette.transfer(1000, naoh.wells()[0], bead_plate.wells()[0], mix_after=(3,500), new_tip='never')
    protocol.delay(minutes=2)    
    pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0], new_tip='never')
    pipette.drop_tip()

def wash_beads(protocol):
    for rep in range(3):
        pickup_24(protocol)
        pipette.transfer(1000, wash_buff.wells()[0], bead_plate.wells()[0], new_tip='never', mix_after=(5, 500))
        if rep < 2:
            protocol.delay(minutes=0.5)
            pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0], new_tip='never')
        pipette.drop_tip()
    protocol.move_labware(labware=bead_plate,new_location='D2',use_gripper=True)