from opentrons import protocol_api
from opentrons.protocol_api import ALL, COLUMN, ROW, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Stack/unstack 96 deep well plates',
    'author': 'Shawn Laursen',
    'description': '''Use the Flex gripper to stack 96 deep well plates
    (custom stackable variant) into a single tower, then unstack them back
    to their original deck slots.'''}

requirements = {'robotType': 'Flex','apiLevel': '2.28'}

# Custom labware definition with stackLimit > 1 and a self-stacking offset.
DEEPWELL = 'shawn_nest_96_wellplate_2ml_deep_stackable'

# Number of deep well plates to stack.
NUM_PLATES = 4

# Deck slots the plates start in. PLATE_SLOTS[0] is the base of the tower.
PLATE_SLOTS = ['C2', 'B2', 'C3', 'B3']

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    stack_plates(protocol)
    protocol.pause("Plates are stacked. Press resume to unstack.")
    unstack_plates(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global trash, plates
    trash = protocol.load_trash_bin('D1')
    plates = []
    for i in range(NUM_PLATES):
        plate = protocol.load_labware(
            DEEPWELL,
            PLATE_SLOTS[i],
            label=f'deep_well_{i}')
        plates.append(plate)

def stack_plates(protocol):
    # Leave plates[0] in place as the base of the stack; place each subsequent
    # plate on top of the previous one so the tower grows upward.
    for i in range(1, NUM_PLATES):
        protocol.move_labware(
            labware=plates[i],
            new_location=plates[i-1],
            use_gripper=True)

def unstack_plates(protocol):
    # Peel plates off the tower top-down and return each one to its original
    # deck slot.
    for i in range(NUM_PLATES - 1, 0, -1):
        protocol.move_labware(
            labware=plates[i],
            new_location=PLATE_SLOTS[i],
            use_gripper=True)
