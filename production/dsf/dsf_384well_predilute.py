from opentrons import protocol_api
from opentrons.protocol_api import ALL, PARTIAL_COLUMN, SINGLE
from opentrons.types import Point
import time
import sys
import math
import random
import subprocess


metadata = {
    'protocolName': 'DSF - 384 well, predilute',
    'author': 'Shawn Laursen',
    'description': '''
    Titrates 30 metals in 12 point 1:3 (1 in 4) dilution series.
    1mM highest metal concentration (metal stocks are at 13.3mM).
    5µM final protein concentration.
    4x sypro concentration.
    100mM HEPES.''',
    'apiLevel': '2.23'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="rxn_vol",
        display_name="Reaction volume",
        description="Volume of reaction in 384well.",
        default=20,
        minimum=5,
        maximum=20,
        unit="µL")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    distribute_buff(protocol)
    titrate(protocol)
    add_protein(protocol)
    blanks(protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    # equiptment
    global tips20, trough, p20m, plate, p300m, tips300, dirty_tips20, dirty_tips300, metals
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    dirty_tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 3)
    metals = protocol.load_labware('nest_96_wellplate_2ml_deep', 4)
    plate = protocol.load_labware('corning_384_wellplate_112ul_flat', 5) 
    trough = protocol.load_labware('nest_12_reservoir_15ml', 6)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    
    # unused
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 10)
    dirty_tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 11)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
     
    global buff, protein, neg, edta, rxn_vol
    buff = trough.wells()[0]
    protein = trough.wells()[1]
    neg = metals.wells()[47]
    edta = metals.wells()[39]
    rxn_vol = protocol.params.rxn_vol

    # cleaning
    global water1, waste1, water2, waste2, water3, waste3, water
    water1 = trough.wells()[1]
    waste1 = trough.wells()[2]
    water2 = trough.wells()[3]
    waste2 = trough.wells()[4]
    water3 = trough.wells()[5]
    waste3 = trough.wells()[6]
    water = trough.wells()[7]

    global tip_20, tip_300
    tip_20 = 0
    tip_300 = 0

def pickup_tips(number, pipette, protocol):
    global last_tip20, last_tip300, tip_20, tip_300
   
    nozzle_dict = {2: "G1", 3: "F1", 4: "E1", 5: "D1", 6: "C1", 7: "B1"}
   
    if pipette == p20m: 
        last_tip20 = tip_20
        if number == 1:
            p20m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p20m.configure_nozzle_layout(style=PARTIAL_COLUMN, start="H1", end=nozzle_dict[number])
        else:
            p20m.configure_nozzle_layout(style=ALL)
        p20m.pick_up_tip(tips20)
        if number == 8: # remove if ever figure out single return
            tip_20 += number

    elif pipette == p300m:
        last_tip300 = tip_300
        if number == 1:
            p300m.configure_nozzle_layout(style=SINGLE,start="H1")
        elif number > 1 and number < 8:
            p300m.configure_nozzle_layout(style=PARTIAL_COLUMN,start="H1", end=nozzle_dict[number])
        else:
            p300m.configure_nozzle_layout(style=ALL)
        p300m.pick_up_tip(tips300)
        if number == 8: # remove if ever figure out single return
            tip_300 += number

def return_tips(pipette):
    if pipette == p20m:
        # p20m.configure_nozzle_layout(style=ALL)
        p20m.drop_tip(dirty_tips20.wells()[last_tip20])
    elif pipette == p300m:
        # p300m.configure_nozzle_layout(style=ALL)
        p300m.drop_tip(dirty_tips300.wells()[last_tip300])

def distribute_buff(protocol):
    pickup_tips(8, p20m, protocol)
    p20m.transfer(((rxn_vol*1.33)/2)-(rxn_vol/10), buff, plate.rows()[0][0], new_tip='never')
    p20m.transfer(((rxn_vol*1.33)/2)-(rxn_vol/10), buff, plate.rows()[0][12], new_tip='never')
    p20m.transfer(((rxn_vol*1.33)/2)-(rxn_vol/10), buff, plate.rows()[1][0], new_tip='never')
    
    p20m.distribute(rxn_vol/2, buff, plate.rows()[0][1:12], new_tip='never')
    p20m.distribute(rxn_vol/2, buff, plate.rows()[0][13:24], new_tip='never')
    p20m.distribute(rxn_vol/2, buff, plate.rows()[1][1:12], new_tip='never')
    return_tips(p20m)

    # different because of blanks
    pickup_tips(7, p20m, protocol)
    p20m.transfer(((rxn_vol*1.33)/2)-(rxn_vol/10), buff, plate.rows()[13][12], new_tip='never')
    p20m.distribute(rxn_vol/2, buff, plate.rows()[13][13:24], new_tip='never')
    p20m.drop_tip()

def titrate(protocol):
    rows = [0,0,1,13]
    cols = [0,12,0,12]
    metal_col = 0
    metal_row = 0
    for row, col in zip(rows,cols):
        if metal_col == 3:
            pickup_tips(7, p20m, protocol)
            metal_row = 7
        else:
            pickup_tips(8, p20m, protocol)
        p20m.transfer(rxn_vol/10, metals.rows()[metal_row][metal_col], plate.rows()[0+row][0+col], new_tip='never')
        p20m.transfer(rxn_vol/6, plate.rows()[0+row][0+col:11+col], plate.rows()[0+row][1+col:12+col], 
                    mix_before=(5, rxn_vol/4), new_tip='never')
        p20m.mix(5, rxn_vol/4)
        p20m.aspirate(rxn_vol/6, plate.rows()[0+row][11+col])
        if metal_col == 3:
            p20m.drop_tip()
        else:
            return_tips(p20m)
        metal_col += 1

def add_protein(protocol):
    pickup_tips(8, p20m, protocol)
    for col in range(0, 24):
        p20m.transfer(rxn_vol/2, protein, plate.rows()[0][col], new_tip='never')
        clean_tips(p20m, rxn_vol, protocol)
    for col in range(0, 20):
        p20m.transfer(rxn_vol/2, protein, plate.rows()[1][col], new_tip='never')
        clean_tips(p20m, rxn_vol, protocol)
    return_tips(p20m)

    # different because of blanks
    pickup_tips(7, p20m, protocol)
    for col in range(20, 24):
        p20m.transfer(rxn_vol/2, protein, plate.rows()[13][col], new_tip='never')
        clean_tips(p20m, rxn_vol, protocol)
    p20m.drop_tip()
    
def blanks(protocol):
    # add buff
    pickup_tips(1, p20m, protocol)
    p20m.distribute(rxn_vol, buff, plate.rows()[15][20:24], new_tip='never')
    p20m.distribute(rxn_vol/2, buff, plate.rows()[15][12:20], new_tip='never')
    p20m.drop_tip()

    # add edta
    for i in range(4):
        pickup_tips(1, p20m, protocol)
        p20m.transfer(rxn_vol/10, edta, plate.rows()[15][12+i], new_tip='never', mix_after=(3, rxn_vol/2))
        p20m.drop_tip()

def clean_tips(pipette, clean_vol, protocol):
    if pipette == p20m:
        p20m.aspirate(clean_vol, water1)
        p20m.dispense(clean_vol, waste1.top().move(Point(3,0,-10)))
        p20m.move_to(waste1.top().move(Point(3,0,0)))
        p20m.aspirate(clean_vol, water2)
        p20m.dispense(clean_vol, waste2.top().move(Point(3,0,-10)))
        p20m.move_to(waste2.top().move(Point(3,0,0)))
        p20m.aspirate(clean_vol, water3)
        p20m.dispense(clean_vol, waste3.top().move(Point(3,0,-10)))
        p20m.move_to(waste3.top().move(Point(3,0,0)))