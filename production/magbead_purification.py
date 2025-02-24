from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Magnetic purification',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 6well plate using StrepXT mag beads.''',
    'apiLevel': '2.20'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    # lyse(protocol)
    global sample_well
    for sample_well in range(0,24):
        find_offset(protocol)
        wash_beads(protocol)
        add_sample(protocol)
        wash(protocol)
        elute(protocol)
        recharge(protocol)
        collect(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equipment
    global tips1000, p1000, mag_mod, hs_mod, reservoir1, reservoir2, reservoir3, tips300, p300, tubes, deep_well, well24, conicals
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips300])
    tips1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', 3)
    p1000 = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tips1000])

    mag_mod = protocol.load_module('magnetic module gen2', 1)
    deep_well = mag_mod.load_labware('nest_96_wellplate_2ml_deep')

    hs_mod = protocol.load_module('heaterShakerModuleV1', 7)
    well24 = hs_mod.load_labware('thomsoninstrument_24_wellplate_10400ul')
    hs_mod.close_labware_latch()
    
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', 4)
    
    conicals = protocol.load_labware('opentrons_6_tuberack_nest_50ml_conical', 2)
    reservoir1 = protocol.load_labware('nest_1_reservoir_195ml', 5)
    reservoir2 = protocol.load_labware('nest_1_reservoir_195ml', 8)
    reservoir3 = protocol.load_labware('nest_1_reservoir_195ml', 11)

    # reagents
    global beads, buff, elution, naoh, water, waste, lysis
    beads = deep_well.wells()[95]
    lysis = conicals.wells()[0]
    buff = reservoir1.wells()[0]
    water = reservoir2.wells()[0]
    waste = reservoir3.wells()[0]
    elution = conicals.wells()[1]
    naoh = conicals.wells()[2]

    global mag_time, mag_height, elute_time, naoh_time, z, x_offset, y_offset
    mag_time = 20 # seconds
    mag_height = 4 # mm
    elute_time = 5 # minutes
    naoh_time = 2 # minutes
    z = 1.5 
    x_offset = 1.5 
    y_offset = 1.5

def find_offset(protocol):
        global x, y, pickup_pos
        if sample_well in [8,9,10,11,12,13,14,15]:
            x = abs(x_offset) #if odd move to the right    
        else:
            x = -abs(x_offset) #if even move to the left 
        
        if sample_well % 2 == 0:
            y = abs(y_offset)
        else:
            y = -abs(y_offset)
        pickup_pos = deep_well.wells()[sample_well].bottom().move(Point(x,y,z))

def lyse(protocol):
    p1000.pick_up_tip()
    for well in range(0,24):
        p1000.transfer(1500, lysis.bottom(3*(24-well)), well24.wells()[well].top(), new_tip="never")
    p1000.drop_tip()
    hs_mod.set_and_wait_for_shake_speed(400)
    protocol.delay(minutes=120)
    hs_mod.deactivate_shaker()

def wash_beads(protocol):
    p1000.pick_up_tip()
    p1000.transfer(360, beads.bottom(5), deep_well.wells()[sample_well], new_tip="never", mix_before=(3,500))
    mag_mod.engage(height_from_base=mag_height)
    clean_tips(p1000, 500, protocol)
    
    for i in range(0,3):
        p1000.transfer(1000, buff, deep_well.wells()[sample_well].top(), new_tip="never")
        p1000.move_to(deep_well.wells()[sample_well].top(10))
        protocol.delay(seconds=mag_time)
        if i == 0:
            vol = 1360
        else:
            vol = 1000
        p1000.transfer(vol, pickup_pos, waste.top(), new_tip="never")
        if i != 2:
            clean_tips(p1000, 1000, protocol)
    mag_mod.disengage()

def add_sample(protocol):
    p1000.transfer(1500, well24.wells()[sample_well].bottom(4), deep_well.wells()[sample_well], new_tip="never", mix_after=(3,500))
    p1000.transfer(1500, deep_well.wells()[sample_well], well24.wells()[sample_well].bottom(4), new_tip="never")
    hs_mod.set_and_wait_for_shake_speed(400)
    protocol.delay(minutes=elute_time/2)
    hs_mod.deactivate_shaker()

def wash(protocol):
    # remove supernatant 
    p1000.transfer(1500, well24.wells()[sample_well].bottom(4), deep_well.wells()[sample_well], new_tip="never", mix_before=(3,500))
    p1000.move_to(deep_well.wells()[sample_well].top(10))
    mag_mod.engage(height_from_base=mag_height)
    protocol.delay(seconds=mag_time)
    p1000.transfer(1500, pickup_pos, well24.wells()[sample_well].bottom(4), new_tip="never")
    p1000.drop_tip()

    # wash beads
    p1000.pick_up_tip()
    for i in range(0,3):
        p1000.transfer(1500, buff, deep_well.wells()[sample_well].top(), new_tip="never")
        p1000.transfer(1500, pickup_pos, waste.top(), new_tip="never")
        if i != 2:
            clean_tips(p1000, 750, protocol)
    p1000.drop_tip()
    mag_mod.disengage()
    
def elute(protocol):
    for i in [0,1]:
        p300.pick_up_tip()
        p300.transfer(100, elution, deep_well.wells()[sample_well], mix_after=(3,50), new_tip='never')
        p300.move_to(deep_well.wells()[sample_well].top(10))
        protocol.delay(minutes=elute_time)
        mag_mod.engage(height_from_base=mag_height)
        protocol.delay(seconds=mag_time)
        p300.transfer(100, pickup_pos, tubes.wells()[sample_well], new_tip='never')
        p300.drop_tip()
        mag_mod.disengage()

def recharge(protocol):
    # add NaOH to used beads
    p1000.pick_up_tip()
    p1000.transfer(1500, naoh, deep_well.wells()[sample_well], mix_after=(3,500), new_tip='never')
    p1000.move_to(deep_well.wells()[sample_well].top(10))
    protocol.delay(minutes=naoh_time)
    mag_mod.engage(height_from_base=mag_height)
    protocol.delay(seconds=mag_time)
    
    # remove NaOH from beads
    p1000.transfer(1500, pickup_pos, waste.top(), new_tip='never')
    clean_tips(p1000, 750, protocol)

    # equilibrate with buff
    for i in range(0,3):
        p1000.transfer(1500, buff, deep_well.wells()[sample_well].top(), new_tip='never')
        p1000.move_to(deep_well.wells()[sample_well].top(10))
        protocol.delay(mag_time)
        p1000.transfer(1500, pickup_pos, waste.top(), new_tip='never')
        clean_tips(p1000, 900, protocol)
    mag_mod.disengage()

def collect(protocol):
    p300.pick_up_tip()
    for i in [0,1]:
        p300.transfer(180, buff, deep_well.wells()[sample_well].top(), new_tip='never')
        p1000.transfer(190, deep_well.wells()[sample_well], beads, new_tip='never', mix_before=(3,180))
    p300.drop_tip()
    p1000.drop_tip()

def clean_tips(pipette, clean_vol, protocol):
    if pipette == p1000:
        p1000.aspirate(clean_vol, water)
        p1000.dispense(clean_vol, waste.top())
        # p1000.aspirate(clean_vol, water)
        # p1000.dispense(clean_vol, waste.top())
        # p1000.aspirate(clean_vol, water)
        # p1000.dispense(clean_vol, waste.top())
