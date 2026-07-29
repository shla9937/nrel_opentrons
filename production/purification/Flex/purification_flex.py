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

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples",
        description="Number of samples to purify",
        default=24,
        minimum=1,
        maximum=24,
        unit="samples")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    bind(protocol)
    wash(protocol)
    elute(protocol)
    collect(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, empty_tiprack, tips1000_24well, tips24_adapter, wash_buff, elution_buff, lysis_plate, mag_24well, bead_plate, collection_plate, liquid_waste, temp_mod
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A2')
    bead_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'A4')

    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    wash_buff = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'B2')
    elution_buff = protocol.load_labware('nest_1_reservoir_290ml', 'B3')
    

    temp_mod = protocol.load_module('temperature module gen2', 'C1')
    liquid_waste = protocol.load_labware('nest_1_reservoir_290ml', 'C3')
    mag_24well = protocol.load_adapter('shawn_24well_magnet_adapter', 'C2')
    collection_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C4')
    
    trash = protocol.load_trash_bin ('D1')
    lysis_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D2')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
    
    pipette = protocol.load_instrument('flex_96channel_1000')

    global half_filled
    half_filled = False

def define_liquids(protocol):
    wash_liquid = protocol.define_liquid(
        name="wash_buff",
        description="Wash buff",
        display_color="#405DBC")
    for well in wash_buff.wells():
        well.load_liquid(liquid=wash_liquid,volume=10000)

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

    bead_liquid = protocol.define_liquid(
        name="Bead suspension",
        description="StrepXT mag bead suspension",
        display_color="#B57EDC")
    for well in bead_plate.wells():
        well.load_liquid(liquid=bead_liquid, volume=1000)

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
        half = 0
    else:    
        half_filled = False
        half = 6
    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col+half])
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])

def bind(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    pickup_24(protocol)
    pipette.mix(3, 250, bead_plate.wells()[0])
    protocol.delay(minutes=0.33)
    pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0].top(), new_tip='never')
    pipette.transfer(2000, lysis_plate.wells()[0].bottom(3), bead_plate.wells()[0], new_tip='never')
    pipette.drop_tip(tips1000_24well.rows()[0][0])
    protocol.move_labware(labware=lysis_plate,new_location='A4',use_gripper=True)
    protocol.move_labware(labware=bead_plate,new_location=temp_mod,use_gripper=True)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])
    for bind in range(10):
        pipette.mix(3,500, bead_plate.wells()[0])
        protocol.delay(minutes=0.75)
    pipette.drop_tip(tips1000_24well.rows()[0][0])

def wash(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    protocol.delay(minutes=1)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])
    pipette.transfer(2000, bead_plate.wells()[0], liquid_waste.wells()[0].top(), new_tip='never')
    pipette.drop_tip()

    pickup_24(protocol)
    for rep in range(3):
        pipette.transfer(1000, wash_buff.wells()[0], bead_plate.wells()[0], new_tip='never', mix_after=(5, 500))
        protocol.delay(minutes=0.5)
        pipette.transfer(1000, bead_plate.wells()[0], liquid_waste.wells()[0].top(), new_tip='never')
    pipette.drop_tip()

def elute(protocol):
    protocol.move_labware(labware=bead_plate,new_location='D2',use_gripper=True)
    pickup_24(protocol)
    pipette.transfer(200, elution_buff.wells()[0], bead_plate.wells()[0], new_tip='never')
    for bind in range(10):
        pipette.mix(3,100, bead_plate.wells()[0])
        protocol.delay(minutes=0.75)
    pipette.drop_tip()

def collect(protocol):
    protocol.move_labware(labware=bead_plate,new_location=mag_24well,use_gripper=True)
    protocol.move_labware(labware=collection_plate,new_location=temp_mod,use_gripper=True)
    protocol.move_labware(labware=tips1000,new_location='D4',use_gripper=True)
    protocol.delay(minutes=0.5)
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE,start="A1")
    for well in range(protocol.params.samples):
        pipette.pick_up_tip(empty_tiprack.rows()[6 - 2 * (well // 6)][11 - (well % 6)])
        pipette.transfer(200, bead_plate.wells()[well], collection_plate.wells()[well], new_tip='never')
        pipette.drop_tip()
