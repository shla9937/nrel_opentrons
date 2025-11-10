from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'X-ray slide prep',
    'author': 'Shawn Laursen',
    'description': '''Prepare slide for SLAC x-ray absorption
    experiment. Takes 2 x 96well plates and pipettes 1µL onto
    3 x 2in quartz slide.
    ''',
    'apiLevel': '2.20'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    make_slide(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, p20, pcr1, slide
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 4)
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tips20])    
    pcr1 = protocol.load_labware('greiner_96_wellplate_300ul', 2)
    slide = protocol.load_labware('shawn_96_well_slide', 5)
  
def make_slide(protocol):  
    for well in range(96):
        p20.transfer(1, pcr1.wells()[well], slide.wells()[well], new_tip='always')
