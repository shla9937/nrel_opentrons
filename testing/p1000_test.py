from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
import time
import sys
import math
import random
import subprocess

metadata = {
    'protocolName': 'p1000 height test',
    'author': 'Shawn Laursen',
    'description': '''foo''',
    'apiLevel': '2.20'
    }

def run(protocol):
    setup(protocol)
    new_targeting(protocol)

def setup(protocol):
    # equiptment
    global tips1000, p1000, plate
    tips1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', 2)
    p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tips1000])
    mag_mod = protocol.load_module('magnetic module gen2', 1)
    plate = mag_mod.load_labware('shawn_6_well_50ml')

def new_targeting(protocol):
    p1000.pick_up_tip(tips1000)
    for well in plate.wells_by_name():
        p1000.aspirate(100, plate.wells_by_name()[well])
        p1000.dispense(100, plate.wells_by_name()[well])
    p1000.drop_tip()   