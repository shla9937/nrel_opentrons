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
    parameters.add_float(
        variable_name="sample_vol",
        display_name="Sample volume",
        description="Volume of samples.",
        default=100,
        minimum=20,
        maximum=200,
        unit="µL")
    parameters.add_float(
        variable_name="elution_vol",
        display_name="Elution volume",
        description="Volume of elution.",
        default=100,
        minimum=20,
        maximum=200,
        unit="µL")
    parameters.add_float(
        variable_name="mag_time",
        display_name="seconds on magnet",
        description="seconds on magnet",
        default=10,
        minimum=1,
        maximum=600,
        unit="seconds")
    parameters.add_float(
        variable_name="incubate_time",
        display_name="seconds to incubate NaOH",
        description="seconds to incubate NaOH",
        default=120,
        minimum=10,
        maximum=3600,
        unit="seconds")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    # dispense_beads(protocol)
    # add_protein(protocol)
    wash(protocol)
    elute(protocol)
    recharge(protocol)
    collect(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips300, p300m, mag_mod, mag_plate, pcrstart, pcrend, trough, reservoir, waste, tubes   
    mag_mod = protocol.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware('greiner_96_wellplate_300ul')
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    trough = protocol.load_labware('nest_12_reservoir_15ml', 4)
    pcrstart = protocol.load_labware('greiner_96_wellplate_300ul', 5)
    pcrend = protocol.load_labware('greiner_96_wellplate_300ul', 6)
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 7)
    reservoir = protocol.load_labware('nest_1_reservoir_195ml', 11)
    waste = protocol.load_labware('nest_1_reservoir_195ml', 10)

    # reagents
    global new_beads, used_beads, buff, elution, naoh, water1, waste1, water2, waste2, water3, waste3
    new_beads = tubes.wells()[0].bottom(2)
    used_beads = tubes.wells()[1]
    buff = reservoir.wells()[0]
    elution = trough.wells()[0]
    naoh = trough.wells()[1]
    water1 = trough.wells()[2]
    waste1 = trough.wells()[3]
    water2 = trough.wells()[4]
    waste2 = trough.wells()[5]
    water3 = trough.wells()[6]
    waste3 = trough.wells()[7]

    # samples
    global samples, sample_vol, elution_vol, columns
    samples = protocol.params.samples
    sample_vol = protocol.params.sample_vol
    elution_vol = protocol.params.elution_vol
    columns = math.ceil(samples/8)

    # time (in seconds)
    global mag_time, incubate_time
    mag_time = protocol.params.mag_time
    incubate_time = protocol.params.incubate_time

    # washing offsets 
    global wash_z, wash_x
    wash_z = 3 #height above the well to remove supernatant and not mag beads
    wash_x = 2 #shift in well (right or left) to remove supernatant and not mag beads -- note value is positive


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
            p300m.configure_nozzle_layout(style=SINGLE,start="H1", tip_racks=[tips300])
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number], tip_racks=[tips300])
        else:
            p300m.configure_nozzle_layout(style=ALL, tip_racks=[tips300])
        p300m.pick_up_tip()

def dispense_beads(protocol):
    # put 20µL of bead solution (1µL of actual beads) into each well
    pickup_tips(1, p300m, protocol)
    for sample in range(0, samples):
        p300m.mix(3, 200, new_beads) 
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
    protocol.delay(seconds=mag_time)
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8].top()) 
        for col in range(0, columns):
            col_x = ((col % 2) * 2 - 1) * wash_x
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))            
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    p300m.drop_tip()

def add_protein(protocol):
    # add 100µL assay (protein + metal) from starting plate to beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(sample_vol, pcrstart.wells()[col*8])            
        p300m.dispense(sample_vol, mag_plate.wells()[col*8])
        p300m.mix(3, sample_vol/2)
        clean_tips(protocol)
    p300m.drop_tip()
    protocol.pause(msg="Take out plate and shake for 10min at RT (700rpm).")

def wash(protocol):
    # remove supernatant 
    mag_mod.engage(height_from_base=5)
    protocol.delay(seconds=mag_time)
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))          
        p300m.dispense(100, waste.wells()[0].top())
    clean_tips(protocol)
    mag_mod.disengage()

    # wash beads
    for col in range(0, columns):
        p300m.aspirate(100, buff)            
        p300m.dispense(100, mag_plate.wells()[col*8].top())
    p300m.move_to(mag_plate.wells()[0].top(25))
    mag_mod.engage(height_from_base=5)
    protocol.delay(seconds=mag_time)
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8].top())
        for col in range(0, columns):
            col_x = ((col % 2) * 2 - 1) * wash_x
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    p300m.drop_tip()

def elute(protocol):
    # add elution buff (50mM biotin)
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(elution_vol, elution)            
        p300m.dispense(elution_vol, mag_plate.wells()[col*8].top())
    clean_tips(protocol)
    protocol.pause(msg="Take out plate and shake for 10min at RT (400rpm).")
    mag_mod.engage(height_from_base=5)
    protocol.delay(seconds=mag_time)

    # tranfser elution to end plate
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(elution_vol, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
        p300m.dispense(elution_vol, pcrend.wells()[col*8])
        clean_tips(protocol)
    p300m.drop_tip()
    mag_mod.disengage()

def recharge(protocol):
    # add NaOH to used beads
    pickup_tips(8, p300m, protocol)
    for col in range(0, columns):
        p300m.aspirate(100, naoh)            
        p300m.dispense(100, mag_plate.wells()[col*8])
        p300m.mix(3, 50)
    protocol.delay(seconds=incubate_time)
    
    # remove NaOH from beads
    mag_mod.engage(height_from_base=5)
    protocol.delay(seconds=mag_time)
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
        p300m.dispense(100, waste.wells()[0].top())
    mag_mod.disengage()

    # wash beads with buff
    clean_tips(protocol)
    for col in range(0, columns):
        p300m.aspirate(100, buff)            
        p300m.dispense(100, mag_plate.wells()[col*8])
    p300m.move_to(mag_plate.wells()[0].top(25))
    mag_mod.engage(height_from_base=5)
    protocol.delay(seconds=mag_time)
    for col in range(0, columns):
        col_x = ((col % 2) * 2 - 1) * wash_x
        p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))           
        p300m.dispense(100, waste.wells()[0].top())

    for i in range(0, 2):
        for col in range(0, columns):
            p300m.aspirate(100, buff)            
            p300m.dispense(100, mag_plate.wells()[col*8])
        for col in range(0, columns):
            col_x = ((col % 2) * 2 - 1) * wash_x
            p300m.aspirate(100, mag_plate.wells()[col*8].bottom().move(Point(col_x,0,wash_z)))            
            p300m.dispense(100, waste.wells()[0].top())

    mag_mod.disengage()
    clean_tips(protocol)

def collect(protocol):
    # add original volume of buff back to beads
    protocol.pause(msg="Move plate from mag module to position 2 (press continue again).")
    protocol.move_labware(labware=mag_plate, new_location=2)
    for col in range(0, columns):
        p300m.aspirate(20, buff)            
        p300m.dispense(20, mag_plate.wells()[col*8])
        p300m.mix(3, 20)
    p300m.drop_tip()
    
    # collect beads back into "used" tube
    pickup_tips(1, p300m, protocol)
    for sample in range(0, samples):
        p300m.mix(3, 20, mag_plate.wells()[sample])
        p300m.aspirate(20, mag_plate.wells()[sample])           
        p300m.dispense(20, used_beads)
    p300m.drop_tip()

def clean_tips(protocol):
    p300m.aspirate(300, water1)
    p300m.dispense(300, waste1.top().move(Point(3,0,-10)))
    p300m.move_to(waste1.top().move(Point(3,0,0)))
    p300m.aspirate(300, water2)
    p300m.dispense(300, waste2.top().move(Point(3,0,-10)))
    p300m.move_to(waste2.top().move(Point(3,0,0)))
    p300m.aspirate(300, water3)
    p300m.dispense(300, waste3.top().move(Point(3,0,-10)))
    p300m.move_to(waste3.top().move(Point(3,0,0)))
