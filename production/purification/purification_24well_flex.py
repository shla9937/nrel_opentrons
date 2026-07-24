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
    bind(protocol)
    wash(protocol)
    elute(protocol)
    collect(protocol)
    # cleanup(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, tips1000_1, empty_tiprack, tips1000_24well, tips24_adapter, wash_buff, elution_buff, lysis_plate, mag_24well, bead_plate, collection_plate, liquid_waste
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A2')
    collection_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'A3')

    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    bead_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'B2')
    elution_buff = protocol.load_labware('nest_1_reservoir_195ml', 'B3')

    liquid_waste = protocol.load_labware('nest_1_reservoir_195ml', 'C1')
    mag_24well = protocol.load_adapter('shawn_24well_magnet_adapter', 'C2')
    wash_buff = protocol.load_labware('nest_1_reservoir_195ml', 'C3')

    trash = protocol.load_trash_bin ('D1')
    lysis_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D2')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
    tips1000_1 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D4')
    
    pipette = protocol.load_instrument('flex_96channel_1000')

    global half_filled
    half_filled = False

def define_liquids(protocol):
    wash_liquid = protocol.define_liquid(
        name="wash_buff",
        description="Wash buff",
        display_color="#405DBC")
    wash_buff['A1'].load_liquid(liquid=wash_liquid,volume=195000)

    lysate_liquid = protocol.define_liquid(
        name="Lysate",
        description="Lysed cells",
        display_color="#FFB347")
    for well in lysis_plate.wells():
        well.load_liquid(liquid=lysate_liquid, volume=2000)

    elution_liquid = protocol.define_liquid(
        name="Elution buff",
        description="Buff for elution (biotin)",
        display_color="#38B55D")
    for well in elution_buff.wells():
        well.load_liquid(liquid=elution_liquid, volume=2000)

def pickup_24(protocol):
    global half_filled
    try:
        protocol.move_labware(tips1000_24well, "A1", use_gripper=True)
    except:
        None

    if half_filled is False:
        pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000, tips1000_1])
        for row in range(4):
            try:
                pipette.pick_up_tip()
            except:
                # active rack ran out; swap the staging-area rack into D1
                protocol.move_labware(tips1000, "C4", use_gripper=True)
                protocol.move_labware(tips1000_1, "D3", use_gripper=True)
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

def bind(protocol):
    pickup_24(protocol)
    pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0], new_tip='never') # likely suspended in buff
    pipette.transfer(2000, lysis_plate.wells()[0].bottom(3), bead_plate.wells()[0], new_tip='never')
    pipette.drop_tip()
    protocol.move_labware(labware=lysis_plate,new_location='A4',use_gripper=True)
    protocol.move_labware(labware=bead_plate,new_location='D2',use_gripper=True)
    protocol.pause("Bind beads by shaking in cold room for 10 min. Replace to D2.")

def wash(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    protocol.delay(minutes=1)
    pickup_24(protocol)
    pipette.transfer(2000, bead_plate.wells()[0], liquid_waste.wells()[0], new_tip='never')
    pipette.drop_tip()

    for rep in range(3):
        pickup_24(protocol)
        pipette.transfer(1000, wash_buff.wells()[0], bead_plate.wells()[0], new_tip='never', mix_after=(5, 500))
        protocol.delay(minutes=0.5)
        pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0], new_tip='never')
        pipette.drop_tip()

def elute(protocol):
    protocol.move_labware(labware=bead_plate,new_location='D2',use_gripper=True)
    pickup_24(protocol)
    pipette.transfer(200, elution_buff.wells()[0], bead_plate.wells()[0], new_tip='never', mix_after=(5, 100))
    pipette.drop_tip()
    protocol.pause("Elute proteins by shaking in cold room for 10 min. Replace to D2.")

def collect(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    protocol.move_labware(labware=empty_tiprack,new_location='A1',use_gripper=True)
    protocol.move_labware(labware=collection_plate,new_location='D2',use_gripper=True)
    protocol.delay(minutes=0.5)
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE,start="H12",tip_racks=[tips1000, tips1000_1])
    for well in range(24):
        pipette.transfer(200, bead_plate.wells()[well], collection_plate.wells()[well], new_tip='always')
