from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'Magnetic wash',
    'author': 'Shawn Laursen',
    'description': '''Purify protein from 6well plate using StrepXT mag beads.''',
    'apiLevel': '2.20'}


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    lyse(protocol)
    # global sample_well
    # for sample_well in range(0,6):
    #     wash_beads(protocol)
    #     dispense_beads(protocol)
    #     wash(protocol)
    #     elute(protocol)
    #     recharge(protocol)
    #     collect(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips1000, p1000, mag_mod, hs_mod, reservoir1, reservoir2, reservoir3, tips300, p300, tubes, deep_well, well24, conicals
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips300])
    tips1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', 3)
    p1000 = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tips1000])

    mag_mod = protocol.load_module('magnetic module gen2', 1)
    deep_well = mag_mod.load_labware('nest_96_wellplate_2ml_deep')

    hs_mod = protocol.load_module('heaterShakerModuleV1', 7)
    well24 = hs_mod.load_labware('thomsoninstrument_24_wellplate_10400ul')
    
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 4)
    
    conicals = protocol.load_labware('opentrons_6_tuberack_nest_50ml_conical', 2)
    reservoir1 = protocol.load_labware('nest_1_reservoir_195ml', 5)
    reservoir2 = protocol.load_labware('nest_1_reservoir_195ml', 8)
    reservoir3 = protocol.load_labware('nest_1_reservoir_195ml', 11)

    # reagents
    global new_beads, used_beads, buff, elution, naoh, water, waste, lysis
    new_beads = tubes.wells()[22].bottom(2)
    used_beads = deep_well.wells()[95]
    lysis = conicals.wells()[0]
    buff = reservoir1.wells()[0]
    water = reservoir2.wells()[0]
    waste = reservoir3.wells()[0]
    elution = conicals.wells()[1]
    naoh = conicals.wells()[2]

    global mag_time
    mag_time = 10

def lyse(protocol):
    hs_mod.close_labware_latch()
    p1000.pick_up_tip()
    for well in range(0,24):
        p1000.transfer(1500, lysis, well24.wells()[well].bottom(20), new_tip="never")
    p1000.drop_tip()
    hs_mod.set_and_wait_for_shake_speed(200)

# def wash_beads(protocol):
#     p1000.pick_up_tip()
#     p1000.transfer(500, new_beads, used_beads, new_tip="never")
#     mag_mod2.engage(height_from_base=5)
#     clean_tips(p1000, 500, protocol)
#     protocol.delay(seconds=mag_time-30)
#     for i in range(0,3):
#         p1000.transfer(2000, buff, used_beads, new_tip="never")
#         protocol.delay(seconds=mag_time-30)
#         p1000.transfer(2000, used_beads.bottom(2), waste, new_tip="never")
#         clean_tips(p1000, 1000, protocol)
#     mag_mod2.disengage()

# def dispense_beads(protocol):
#     # put 500µL of beads into well
#     p1000.transfer(500, buff, used_beads, new_tip="never", mix_after=(3,500))
#     p1000.transfer(500, used_beads, plate.wells()[sample_well], new_tip="never", mix_after=(3,500))
#     p1000.drop_tip()
#     protocol.pause(msg="Take out plate and shake for 10min at RT (100rpm).")

# def wash(protocol):
#     # remove supernatant 
#     mag_mod.engage(height_from_base=7)
#     protocol.delay(seconds=mag_time)
#     p1000.transfer(50000, plate.wells()[sample_well], waste)
#     mag_mod.disengage()

#     # wash beads
#     for i in range(0,3):
#         p1000.pick_up_tip()
#         p1000.transfer(5000, buff, plate.wells()[sample_well].bottom(10), new_tip="never")
#         mag_mod.engage(height_from_base=7)
#         protocol.delay(seconds=mag_time)
#         p1000.transfer(5000, plate.wells()[sample_well], waste new_tip="never")
#         p1000.drop_tip()
#         mag_mod.disengage()
    
# def elute(protocol):
#     p300.transfer(50000, plate.wells()[sample_well], waste)
#     protocol.pause(msg="Take out plate and shake for 10min at RT (400rpm).")
#     mag_mod.engage(height_from_base=5)
#     protocol.delay(seconds=mag_time)

#     # tranfser elution to end plate
#     for col in range(0, columns):
#         col_x = ((col % 2) * 2 - 1) * wash_x
#         p300m.aspirate(elution_vol, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
#         p300m.dispense(elution_vol, pcrend.wells()[col*8])
#         clean_tips(protocol)
#     p300m.drop_tip()
#     mag_mod.disengage()

# def recharge(protocol):
#     # add NaOH to used beads
#     pickup_tips(8, p300m, protocol)
#     for col in range(0, columns):
#         p300m.aspirate(100, naoh)            
#         p300m.dispense(100, mag_plate.wells()[col*8])
#         p300m.mix(3, 50)
#     protocol.delay(seconds=incubate_time)
    
#     # remove NaOH from beads
#     mag_mod.engage(height_from_base=5)
#     protocol.delay(seconds=mag_time)
#     for col in range(0, columns):
#         col_x = ((col % 2) * 2 - 1) * wash_x
#         p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
#         p300m.dispense(100, waste.wells()[0].top())
#     mag_mod.disengage()

#     # wash beads with buff
#     clean_tips(protocol)
#     for col in range(0, columns):
#         p300m.aspirate(100, buff)            
#         p300m.dispense(100, mag_plate.wells()[col*8])
#     p300m.move_to(mag_plate.wells()[0].top(25))
#     mag_mod.engage(height_from_base=5)
#     protocol.delay(seconds=mag_time)
#     for col in range(0, columns):
#         col_x = ((col % 2) * 2 - 1) * wash_x
#         p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
#         p300m.dispense(100, waste.wells()[0].top())

#     for i in range(0, 2):
#         for col in range(0, columns):
#             p300m.aspirate(100, buff)            
#             p300m.dispense(100, mag_plate.wells()[col*8])
#         for col in range(0, columns):
#             col_x = ((col % 2) * 2 - 1) * wash_x
#             p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))            
#             p300m.dispense(100, waste.wells()[0].top())

#     mag_mod.disengage()
#     clean_tips(protocol)

# def collect(protocol):
#     # add original volume of buff back to beads
#     protocol.pause(msg="Move plate from mag module to position 2 (press continue again).")
#     protocol.move_labware(labware=mag_plate, new_location=2)
#     for col in range(0, columns):
#         p300m.aspirate(20, buff)            
#         p300m.dispense(20, mag_plate.wells()[col*8])
#         p300m.mix(6, 20)
#     p300m.drop_tip()
    
#     # collect beads back into "used" tube
#     pickup_tips(1, p300m, protocol)
#     for sample in range(0, samples):
#         p300m.mix(3, 20, mag_plate.wells()[sample])
#         p300m.aspirate(20, mag_plate.wells()[sample])           
#         p300m.dispense(20, used_beads)
#     p300m.drop_tip()

def clean_tips(pipette, clean_vol, protocol):
    if pipette == p1000:
        p1000.aspirate(clean_vol, water)
        p1000.dispense(clean_vol, waste.top())
        p1000.aspirate(clean_vol, water)
        p1000.dispense(clean_vol, waste.top())
        p1000.aspirate(clean_vol, water)
        p1000.dispense(clean_vol, waste.top())
