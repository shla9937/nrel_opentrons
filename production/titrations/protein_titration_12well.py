from opentrons import protocol_api
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Protein titration - 12 well',
    'author': 'Shawn Laursen',
    'description': '''Put mixes (50ul of protein+dna) and 250ul of (dna) next to
                      each other in 96 well plate
                      Titrates protein in 384well. ''',
    'apiLevel': '2.11'
    }

def run(protocol):

    well_96start = 0 #index from 0
    strobe(12, 8, True, protocol)
    setup(4, well_96start, protocol)
    for buff in buffs:
        protein_titration(buff, protocol)
    strobe(12, 8, False, protocol)

def strobe(blinks, hz, leave_on, protocol):
    i = 0
    while i < blinks:
        protocol.set_rail_lights(True)
        time.sleep(1/hz)
        protocol.set_rail_lights(False)
        time.sleep(1/hz)
        i += 1
    protocol.set_rail_lights(leave_on)

def setup(num_buffs, well_96start, protocol):
    #equiptment
    global tips300, plate96, plate384, p300m, tempdeck
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    plate96 = protocol.load_labware('costar_96_wellplate_200ul', 6)
    plate384 = protocol.load_labware('corning3575_384well_alt', 5)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300])

    #buffs
    global buffs, buffa, buffb, buffc, buffd
    buffa = "a"
    buffb = "b"
    buffc = "c"
    buffd = "d"
    buffs = [buffa, buffb, buffc, buffd]
    del buffs[num_buffs:]

    global start_96well
    start_96well = well_96start

def protein_titration(buff, protocol):
    prot_col = (buffs.index(buff)*2)+start_96well
    buff_col = prot_col+1
    if (buffs.index(buff) % 2) == 0:
        which_rows = 0
    else:
        which_rows = 1

    if buffs.index(buff) < 2:
        start_384well = 0
    else:
        start_384well = 12

    p300m.pick_up_tip()
    p300m.distribute(20, plate96.rows()[0][buff_col],
                     plate384.rows()[which_rows][start_384well+1:start_384well+12],
                     disposal_volume=10, new_tip='never')
    p300m.flow_rate.aspirate = 40
    p300m.transfer(40, plate96.rows()[0][prot_col],
                   plate384.rows()[which_rows][start_384well], new_tip='never')
    p300m.flow_rate.aspirate = 96
    p300m.transfer(20,
                   plate384.rows()[which_rows][start_384well:start_384well+10],
                   plate384.rows()[which_rows][start_384well+1:start_384well+11],
                   mix_after=(3, 20), new_tip='never')
    p300m.aspirate(20, plate384.rows()[which_rows][start_384well+10])
    p300m.drop_tip()
