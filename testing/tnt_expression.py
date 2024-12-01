from opentrons import protocol_api
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'TnT protein expression',
    'author': 'Shawn Laursen',
    'description': '''Protocol: 
    -   At 4°C
    -   Add mix
    -   Add Methionine
    -   Add DNA
    -   Add water
    -   Incuate at 30°C for 60-90 min
    -   Return to 4°C''',
    'apiLevel': '2.20'
    }

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="well_96start",
        display_name="96 well start",
        description="Which column of the 96 well plate to start with.",
        default=1,
        minimum=1,
        maximum=9,
        unit="column"
    )

def run(protocol):
    global well_96start
    well_96start = protocol.params.well_96start - 1
    strobe(12, 8, True, protocol)
    setup(protocol)
    fill_plate_buff(protocol)
    fill_plate_dna(protocol)    
    titrate_x(protocol)
    titrate_y(protocol)
    add_controls(protocol)
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

def setup(protocol):
    # equiptment
    global tips300, plate96, plate384, p300m, rt_24, trough
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    plate96 = protocol.load_labware('costar_96_wellplate_200ul', 4)
    plate384 = protocol.load_labware('corning3575_384well_alt', 5)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    rt_24 = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 8)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 2)

    # reagents
    global buff, buff_control, dna1, dna2, prot1, prot2, prot_control, dna3
    buff = trough.wells()[0]
    buff_control = trough.wells()[1]
    dna1 = rt_24.rows()[0][0]
    dna2 = rt_24.rows()[0][1]
    prot1 = rt_24.rows()[0][2]
    prot2 = rt_24.rows()[0][3]
    prot_control = rt_24.rows()[0][4]
    dna3 = rt_24.rows()[0][5]

    # tips
    global tip20_dict, tip300_dict
    tip20_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}
    tip300_dict = {key: ['H','G','F','E','D','C','B','A'] for key in range(1, 12 + 1)}

def pickup_tips(number, pipette, protocol):
    # if pipette == p20m:
    #     for col in tip20_dict:
    #         if len(tip20_dict[col]) >= number:
    #             p20m.pick_up_tip(tips20[str(tip20_dict[col][number-1] + str(col))])
    #             tip20_dict[col] = tip20_dict[col][number:]
    #             break

    if pipette == p300m:
        for col in tip300_dict:
            if len(tip300_dict[col]) >= number:
                p300m.pick_up_tip(tips300[str(tip300_dict[col][number-1] + str(col))])
                tip300_dict[col] = tip300_dict[col][number:]
                break

def fill_plate_buff(protocol):
    for i in range(0,2):
        pickup_tips(8, p300m, protocol)
        p300m.distribute(10, buff,
                         plate384.rows()[i][1:16], disposal_volume=10, 
                         new_tip='never')
        p300m.drop_tip()

def fill_plate_dna(protocol):
    wells = 0
    for dna in [dna1, dna2]:
        # disperse dna into wells of 96 well plate
        pickup_tips(1, p300m, protocol)
        for row in range(0, 8):
            p300m.aspirate(185, dna) 
            p300m.dispense(185, plate96.rows()[row][well_96start])
        p300m.drop_tip()
       
        # use 8 channel to distribute
        pickup_tips(8, p300m, protocol)
        p300m.aspirate(170, plate96.rows()[0][well_96start])
        p300m.dispense(20, plate384.rows()[wells][0])
        for col in range(1,16):
            p300m.dispense(10, plate384.rows()[wells][col])
        p300m.drop_tip()
        wells = 1

def titrate_x(protocol):
    # add 100µL of buff to dilution wells
    for i in [0,2]:
        pickup_tips(1, p300m, protocol)
        for row in range(1,8):
            p300m.aspirate(100, buff)
            p300m.dispense(100, plate96.rows()[row][well_96start+1+i])
        for row in range(0,8):
            p300m.aspirate(100, buff)
            p300m.dispense(100, plate96.rows()[row][well_96start+2+i])
        p300m.drop_tip()

        # add 200µL of protein to first well
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(200, prot1)
        p300m.dispense(200, plate96.rows()[0][well_96start+1+i])
        
        # grab 100µL of protein from stock and do titration
        p300m.aspirate(100, plate96.rows()[0][well_96start+1+i])
        p300m.dispense(100, plate96.rows()[0][well_96start+2+i])
        p300m.mix(3,100)  
        for row in range(1,7):
            p300m.aspirate(100, plate96.rows()[row-1][well_96start+2+i])
            p300m.dispense(100, plate96.rows()[row][well_96start+1+i])
            p300m.mix(3,100)
            p300m.aspirate(100, plate96.rows()[row][well_96start+1+i])
            p300m.dispense(100, plate96.rows()[row][well_96start+2+i])
            p300m.mix(3,100)
        p300m.aspirate(100, plate96.rows()[6][well_96start+2+i])
        p300m.dispense(100, plate96.rows()[7][well_96start+1+i])
        p300m.mix(3,100)  
        p300m.drop_tip()

    # plate titration in 384well
    for j in range(0,2):
        pickup_tips(8, p300m, protocol)
        p300m.aspirate(90, plate96.rows()[0][well_96start+3+j])
        p300m.dispense(90, plate96.rows()[0][well_96start+1+j])
        p300m.aspirate(180, plate96.rows()[0][well_96start+1+j])
        p300m.dispense(20, plate384.rows()[j][0])
        for col in range(1,16):
            p300m.dispense(10, plate384.rows()[j][col])
        p300m.drop_tip()

def titrate_y(protocol):
    # put prot2 into col 1 of 384 well plate 
    pickup_tips(1, p300m, protocol)
    for i in [0,8]:
        p300m.aspirate(170, prot2)
        for row in range(i,i+8):
            p300m.dispense(20, plate384.rows()[row][0])
    p300m.drop_tip()
    
    # titrate protein
    for i in range(0,2):
        pickup_tips(8, p300m, protocol)
        p300m.transfer(30,
                    plate384.rows()[i][0:14],
                    plate384.rows()[i][1:15],
                    mix_after=(3, 30), new_tip='never')
        p300m.aspirate(30, plate384.rows()[i][14])
        p300m.drop_tip()

def add_controls(protocol):
    # add buff and dna
    for item in [buff_control, dna3]:
        pickup_tips(1, p300m, protocol)
        for i in range(0,2):
            p300m.aspirate(20, item) 
            p300m.dispense(20, plate384.rows()[i][16])
            p300m.distribute(15, item, plate384.rows()[i][17:24], 
                            disposal_volume=10, new_tip='never')
        p300m.drop_tip()
     
     # add protein and titrate
    for i in range(0,2):
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(20, prot_control)
        p300m.dispense(20, plate384.rows()[i][16])
        p300m.mix(3,30)
        p300m.transfer(30,
                    plate384.rows()[i][16:22],
                    plate384.rows()[i][17:23],
                    mix_after=(3, 30), new_tip='never')
        p300m.aspirate(30, plate384.rows()[i][22])
        p300m.drop_tip()