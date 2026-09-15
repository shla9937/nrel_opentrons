from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Innoculation - 24well',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 24 well plate using StrepXT mag beads'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="constructs",
        display_name="Number of constructs",
        description="Number of constructs to test",
        default=24,
        minimum=1,
        maximum=24,
        unit="constructs")
    parameters.add_int(
        variable_name="twist_start_well",
        display_name="Twist start well",
        description="Well of first DNA to transform in Twist plate",
        default=1,
        minimum=1,
        maximum=96,
        unit="well")
    parameters.add_bool(
        variable_name="recon_dna",
        display_name="Reconstitute DNA?",
        description="On = add water to DNA, Off = DNA already has water",
        default=True)

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_cells(protocol) 
    add_dna(protocol)
    add_media(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global trash, pipette, tips1000, empty_tiprack, tips1000_24well, tips24_adapter, expression_plate, twist_plate, tubes, media, temp_mod, temp_block, twist_start_well, twist_end_well, constructs
    # A row
    tips1000_24well = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips24_adapter = protocol.load_adapter('opentrons_flex_96_tiprack_adapter', 'A3')

    # B row
    empty_tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B1')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'B2')

    # C row
    temp_mod = protocol.load_module('temperature module gen2', 'C1')
    temp_mod.start_set_temperature(4)
    temp_block = temp_mod.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    twist_plate = protocol.load_labware('greiner_96_wellplate_300ul', 'C2')
    tubes = protocol.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', 'C3')

    # D row
    trash = protocol.load_trash_bin ('D1') 
    
    expression_plate = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 'D2')
    media = protocol.load_labware('omega_1_reservoir_600ml', 'D3')
   
    pipette = protocol.load_instrument('flex_96channel_1000')

    constructs = protocol.params.constructs
    twist_start_well = protocol.params.twist_start_well - 1
    twist_end_well = twist_start_well + protocol.params.constructs - 1

def define_liquids(protocol):
    water = protocol.define_liquid(
        name="DEPC water",
        description="water",
        display_color="#4054B9")
    tubes.wells()[0].load_liquid(liquid=water,volume=1500)

    cells = protocol.define_liquid(
        name="Isothermal comp cells",
        description="comp cells",
        display_color="#D59227")
    temp_block.wells()[0].load_liquid(liquid=cells,volume=1500)

    auto_tb = protocol.define_liquid(
        name="Auto TB",
        description="Auto TB + metals + glycerol + AMP",
        display_color="#DFEB36")
    media.wells()[0].load_liquid(liquid=auto_tb, volume=600000)

    start_well = protocol.define_liquid(
        name="Start well",
        description="Where in twist plate to start picking from",
        display_color="#27D435")
    twist_plate.wells()[twist_start_well].load_liquid(liquid=start_well, volume=1)

    end_well = protocol.define_liquid(
        name="End well",
        description="Where in twist plate to start picking from",
        display_color="#D42727")
    twist_plate.wells()[twist_end_well].load_liquid(liquid=end_well, volume=1)

def pickup_24(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.ROW,start="H1",tip_racks=[tips1000])
    for row in range(4):
        pipette.pick_up_tip()
        pipette.drop_tip(empty_tiprack.rows()[row*2][0])

    pipette.configure_nozzle_layout(style=protocol_api.COLUMN,start="A12")
    for col in range(6):
        pipette.pick_up_tip(empty_tiprack.rows()[0][col])
        pipette.drop_tip(tips1000_24well.rows()[0][col*2])

    protocol.move_labware(tips1000_24well, tips24_adapter, use_gripper=True)
    pipette.configure_nozzle_layout(style=protocol_api.ALL)
    pipette.pick_up_tip(tips1000_24well.rows()[0][0])

def add_cells(protocol):
    # distribute from first tube in block
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start="A1", tip_racks=[tips1000])
    cells_lc = protocol.get_liquid_class("glycerol_50")
    pipette.pick_up_tip(tips1000.wells()[-1])
    pipette.distribute_with_liquid_class(cells_lc, 50, temp_block.wells()[0], temp_block.wells()[1:constructs], new_tip="never")
    pipette.drop_tip()

def add_dna(protocol):
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start="A1", tip_racks=[tips1000])
    # tips walked bottom-right → left, then up a row: H12, H11, ..., H1, G12, G11, ...
    tip_order = [w for row in reversed(tips1000.rows()) for w in reversed(row)]
    if protocol.params.recon_dna is True: 
        for i, well in enumerate(range(twist_start_well, twist_end_well + 1)):
            pipette.pick_up_tip(tip_order[i+1])
            pipette.transfer(50, tubes.columns()[0], twist_plate.wells()[well], new_tip="never", mix_after=(3, 25))
            pipette.transfer(10, twist_plate.wells()[well], temp_block.wells()[well%24], new_tip='never', mix_after=(3, 25))
            pipette.drop_tip()
    else:
        for i, well in enumerate(range(twist_start_well, twist_end_well + 1)):
            pipette.pick_up_tip(tip_order[i+1])
            pipette.transfer(10, twist_plate.wells()[well], temp_block.wells()[well%24], new_tip='never', mix_after=(3, 25))
            pipette.drop_tip()

def add_media(protocol):
    pickup_24(protocol)
    pipette.transfer(5000, media.wells()[0], expression_plate.wells()[0], new_tip='never')
    pipette.transfer(50, temp_block.wells()[0], expression_plate.wells()[0], mix_after=(3, 100), new_tip='never')
    pipette.drop_tip()