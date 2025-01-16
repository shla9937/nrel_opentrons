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
    'description': '''This preps a single 96 well plate using step mag beads.
    Doesn't add mag beads, but does collect them.''',
    'apiLevel': '2.20'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="samples",
        display_name="Number of samples",
        description="Number of samples.",
        default=96,
        minimum=1,
        maximum=96,
        unit="samples")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    dispense_beads(protocol)
    add_protein(protocol)
    wash(protocol)
    elute(protocol)
    recharge(protocol)
    collect(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips300, tips300_1, tips300_2, p300m, mag_mod, mag_plate, pcrstart, pcrend, trough, reservoir, waste, tubes   
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 7)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1, tips300_2])
    mag_mod = protocol.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware('biorad_96_wellplate_200ul_pcr')
    pcrstart = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 5)
    pcrend = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 6)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 4)
    reservoir = protocol.load_labware('nest_1_reservoir_195ml', 11)
    waste = protocol.load_labware('nest_1_reservoir_195ml', 10)
    tubes = protocol.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', 8)

    # reagents
    global new_beads, used_beads, buff, elution, naoh
    new_beads = tubes.wells()[0]
    used_beads = tubes.wells()[1]
    buff = reservoir.wells()[0]
    elution = trough.wells()[0]
    naoh = trough.wells()[1]

    # samples
    global samples, columns
    samples = protocol.params.samples
    columns = math.ceil(samples/8)

    # time
    global mag_time, incubate_time
    mag_time = 5
    incubate_time = 2

def pickup_tips(number, pipette, protocol):
    # nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
    # if pipette == p20m:
    #     if number == 1:
    #         p20m.configure_nozzle_layout(style=SINGLE,start="H1")
    #     elif number > 1 and number < 8:
    #         p20m.configure_nozzle_layout(style=PARTIAL_COLUMN, start="H1", end=nozzle_dict[number])
    #     else:
    #         p20m.configure_nozzle_layout(style=ALL)
    #     p20m.pick_up_tip()

    # elif pipette == p300m:
    if pipette == p300m:
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300, tips300_1, tips300_2])
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300, tips300_1, tips300_2])
        else:
            p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300, tips300_1, tips300_2])
        p300m.pick_up_tip()

def dispense_beads(protocol):
    # put 20µL of bead solution (1µL of actual beads) into each well
    pickup_tips(1, p300m, protocol)
    for sample in range(0, samples):
        p300m.aspirate(20, new_beads)            
        p300m.dispense(20, mag_plate.wells()[sample])
    p300m.drop_tip()

    # wash beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, buff)            
        p300m.dispense(100, mag_plate.wells()[col*8].top())
    p300m.move_to(mag_plate.wells()[0].top(25))
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)
    for col in range(0, columns):
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8].top()) 
        for col in range(0, columns):
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    p300m.drop_tip()

def add_protein(protocol):
    # add 100µL assay (protein + metal) from starting plate to beads
    for col in range(0, columns):
        pickup_tips(8, p300m, protocol)
        p300m.aspirate(100, pcrstart.wells()[col*8])            
        p300m.dispense(100, mag_plate.wells()[col*8])
        p300m.mix(3, 50)
        p300m.drop_tip()
    protocol.pause(msg="Take out plate and shake for 10min at RT (700rpm).")

def wash(protocol):   
    # remove supernatant 
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, mag_plate.wells()[col*8])            
        p300m.dispense(100, waste.wells()[0].top())
    p300m.drop_tip()
    mag_mod.disengage()

    # wash beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, buff)            
        p300m.dispense(100, mag_plate.wells()[col*8].top())
    p300m.move_to(mag_plate.wells()[0].top(25))
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)
    for col in range(0, columns):
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8].top())
        for col in range(0, columns):
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    p300m.drop_tip()

def elute(protocol):
    # add elution buff (50mM biotin)
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, elution)            
        p300m.dispense(100, mag_plate.wells()[col*8].top())
    p300m.drop_tip()
    protocol.pause(msg="Take out plate and shake for 10min at RT (400rpm).")
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)

    # tranfser elution to end plate
    for col in range(0, columns):
        pickup_tips(8, p300m, protocol)
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
        p300m.dispense(100, pcrend.wells()[col*8])
        p300m.drop_tip()

    mag_mod.disengage()

def recharge(protocol):
    # add NaOH to used beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, naoh)            
        p300m.dispense(100, mag_plate.wells()[col*8])
        p300m.mix(3, 50)
    p300m.drop_tip()
    protocol.delay(minutes=incubate_time)
    
    # remove NaOH from beads
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
        p300m.dispense(100, waste.wells()[0].top())
    p300m.drop_tip()
    mag_mod.disengage()

    # wash beads with buff
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, buff)            
        p300m.dispense(100, mag_plate.wells()[col*8])
    p300m.move_to(mag_plate.wells()[0].top(25))
    mag_mod.engage(height_from_base=5)
    protocol.delay(minutes=mag_time)
    for col in range(0, columns):
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8])
        for col in range(0, columns):
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom(2))            
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    p300m.drop_tip()

def collect(protocol):
    # add original volume of buff back to beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(20, buff)            
        p300m.dispense(20, mag_plate.wells()[col*8])
        p300m.mix(3, 20)
    p300m.drop_tip()
    
    # collect beads back into "used" tube
    pickup_tips(1, p300m, protocol)
    for sample in range(0, samples):
        p300m.aspirate(20, mag_plate.wells()[sample])            
        p300m.dispense(20, used_beads)
    p300m.drop_tip()







