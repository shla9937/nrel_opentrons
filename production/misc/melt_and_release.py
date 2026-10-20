import time


metadata = {
    'protocolName': 'Melt and release with ICP-MS',
    'author': 'Shawn Laursen',
    'description': '''
    Columns 1-6: one protein plus metal mixture. Columns 7-12: metal-only controls.
    Temperature pairs: 1/7, 2/8, 3/9, 4/10, 5/11, 6/12.
    100µL reactions in a Bio-Rad 200µL PCR plate on the Temperature Module
    with the matching Opentrons 96-well aluminium block.
    10µM protein and each metal in protein reactions; 10µM each metal in controls.
    Stock metals: 25µM each in proper pH buffer, trough A1 (5mL).
    Protein: 25µM in proper pH buffer, trough A2 (at least 1.92mL plus dead volume).
    3.89% ppt nitric acid (125mL).
    Buff (150mL in the 195mL reservoir).
    6 temps (25, 39, 53, 67, 81, 95°C), held for 1 minute after the module
    reaches each setpoint. Samples remaining on the module also stay at that
    temperature during manual desalting. Module temperature is not sample temperature.
    Steps:
    -   Add buff
    -   Add metal
    -   Add protein
    -   Start covered incubation at 25°C (at least 15 min)
    -   Prep desalt plate and add acid to final plate during incubation
    -   Wait for any remaining incubation time before the ramp
    -   Temp ramp loop:
        -   Uncover and transfer the full 100µL from one protein/control pair
            into matching unused columns of the same desalt plate
        -   Cover remaining reactions and centrifuge into matching acid wells
        -   Return desalt and collection plates before the next temperature
    900µL acid + nominal 100µL eluate = 1000µL per collection well.
    Actual volume depends on evaporation and desalting recovery.
    Use Nunc deep-well collection plates. Existing NEST definitions for the
    desalt and collection positions MUST be verified/replaced for the actual
    plates and supports before running; they are not verified Nunc definitions.''',
    'apiLevel': '2.28'}

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    add_buff(protocol)
    add_metal(protocol)    
    add_protein(protocol)
    incubate(protocol) 
    prep_desalt(protocol)
    add_acid(protocol)
    temp_ramp(protocol)
    temp_mod.deactivate()
    protocol.set_rail_lights(False)

def setup(protocol):
    global p300m, tips300, tips300_1, tips300_2, desalt_plate, res1, rxn_plate, icp_plate, res2, trough, temp_mod
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tips300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    tips300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 9)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300, tips300_1, tips300_2])
    desalt_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 1)
    res1 = protocol.load_labware('nest_1_reservoir_195ml', 2)
    temp_mod = protocol.load_module('temperature module gen2', 4)
    rxn_plate = temp_mod.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')
    icp_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 11)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 7)
    res2 = protocol.load_labware('nest_1_reservoir_195ml', 8)

    global buff, acid, metal_mix, protein, rxn_vol, protein_vol, metal_vol, acid_vol, temps
    buff = res1.wells()[0]
    acid = res2.wells()[0]
    metal_mix = trough.wells()[0]
    protein = trough.wells()[1]
    rxn_vol = 100
    protein_vol = rxn_vol * 10 / 25
    metal_vol = rxn_vol * 10 / 25
    acid_vol = 1000 - rxn_vol
    temps = [25 + index * (95 - 25) / 5 for index in range(6)]
    protocol.pause("Before proceeding, verify or replace the NEST labware definitions in slots 1 and 11 "
                   "for the actual desalt/support and Nunc collection plates. Confirm the PCR plate "
                   "and aluminium block in slot 4, and load three full 300uL tip racks.")
    temp_mod.set_temperature(25)

def add_buff(protocol):
    p300m.pick_up_tip()
    p300m.transfer(rxn_vol - protein_vol - metal_vol, buff,[well.top() for well in rxn_plate.rows()[0][:6]], new_tip='never')
    p300m.transfer(rxn_vol - metal_vol, buff,[well.top() for well in rxn_plate.rows()[0][6:]], new_tip='never')
    p300m.drop_tip()

def add_metal(protocol):
    p300m.transfer(metal_vol, metal_mix, rxn_plate.rows()[0],new_tip='always', mix_after=(3, rxn_vol / 2))

def add_protein(protocol):
    p300m.transfer(protein_vol, protein, rxn_plate.rows()[0][:6],new_tip='always', mix_after=(3, rxn_vol / 2))

def incubate(protocol):
    global start_time
    start_time = time.monotonic()

def prep_desalt(protocol):
    protocol.pause("Start prepping desalt plate by removing bottom foil, placing on wash plate, removing top seal. Centrifuge 2 min at 1000rcf.")
    protocol.pause("Place desalt plate back in slot 1.")

    destinations = [well.top() for well in desalt_plate.rows()[0]]
    for wash in range(4):
        p300m.pick_up_tip()
        p300m.transfer(250, buff, destinations, new_tip='never')
        p300m.drop_tip()
        protocol.pause("Centrifuge desalt plate 2 min at 1000rcf, set on wash plate again, and return to slot 1.")
    protocol.pause("Ready to resume protocol.")

def add_acid(protocol):
    p300m.pick_up_tip()
    p300m.transfer(acid_vol, acid, [well.top() for well in icp_plate.rows()[0]], new_tip='never')
    p300m.drop_tip()

def temp_ramp(protocol):
    if not protocol.is_simulating():
        while time.monotonic() - start_time < 15 * 60:
            protocol.delay(seconds=1, msg="Waiting for at least 15 minutes of protein-metal binding at 25C.")
    for index, temp in enumerate(temps):
        temp_mod.set_temperature(temp)
        protocol.delay(minutes=1, msg=f"Hold at {temp:g}C before sampling.")
        protocol.pause(f"Remove the reaction plate cover for sampling at {temp:g}C. "
                       "Leave the reaction plate on the Temperature Module.")
        desalt(protocol, index, temp)

def desalt(protocol, index, temp):
    columns = [index, index + 6]
    sources = [rxn_plate.rows()[0][column] for column in columns]
    destinations = [desalt_plate.rows()[0][column].top() for column in columns]
    p300m.transfer(rxn_vol, sources, destinations, new_tip='always')
    protocol.pause(f"{temp:g}C samples are in desalt columns {index + 1} and {index + 7}. "
                   "Cover the remaining reactions on the Temperature Module. "
                   "Place the desalt plate on the acid collection plate with A1 aligned to A1; "
                   "centrifuge 2 min at 1000rcf. Return the desalt plate on its wash support to "
                   "slot 1 and the same acid collection plate to slot 11, preserving orientation. "
                   "Do not replace either plate: the next samples use unused columns.")
