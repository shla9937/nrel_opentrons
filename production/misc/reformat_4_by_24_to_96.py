from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Reformat 4 x 24 wells into 96 well.',
    'author': 'Shawn Laursen',
    'description': '''
    Reformat 4 x 24 wells into 96 well.''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="volume",
        display_name="Volume to transfer",
        description="Volume to transfer from each well to 96 well plate.",
        default=1000,
        minimum=100,
        maximum=2000,)

def run(protocol):
    protocol.set_rail_lights(False)
    setup(protocol)
    reformat(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips1000, p1000, plate96, well24_1, well24_2, well24_3, well24_4, wells24
    tips1000 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)
    p1000 = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tips1000])
    plate96 = protocol.load_labware('nest_96_wellplate_2ml_deep', 5)  
    well24_1 = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 10)
    well24_2 = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 7)
    well24_3 = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 4)
    well24_4 = protocol.load_labware('thomsoninstrument_24_wellplate_10400ul', 1)
    wells24 = [well24_1, well24_2, well24_3, well24_4]

def reformat(protocol):
    volume = protocol.params.volume
    for i in range(24):
        for j in range(4):
            p1000.transfer(volume, wells24[j].wells()[i], plate96.wells()[i*4 + j], new_tip='always')
