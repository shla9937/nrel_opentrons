from opentrons import protocol_api
from opentrons.types import Point


metadata = {
    'protocolName': 'DSF - Rubic screen up to 4 proteins',
    'author': 'Shawn Laursen',
    'description': '''
    Adds 21µL of screen to the bottom of each well.
    2µL protein (62.5µM -> 5µM)
    2µL sypro (62.5x -> 5x), dispensed with one-sided upper-wall touches.
    Proteins 1-4 use interleaved sets starting at A1, B1, A2, B2.
    Uses 96 x 300µL tips and 8 x (1 + number of proteins) 20µL tips.
    Seal and centrifuge the plate to combine reagents before the assay.''',
    'apiLevel': '2.26'}

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="proteins",
        display_name="Number of proteins",
        description="Number of proteins",
        default=4,
        minimum=1,
        maximum=4,
        unit="proteins")

def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_buffer(protocol)
    add_sypro(protocol)
    add_protein(protocol)
    protocol.set_rail_lights(False)
    protocol.pause('Seal and centrifuge the plate to combine the screen, SYPRO and protein before running the assay.')

def setup(protocol):
    # equiptment
    global tips20, tips300, plate, p20m, p300m, screen, stocks
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 4)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    plate = protocol.load_labware('appliedbiosystemsmicroamp_384_wellplate_40ul', 5) 
    screen = protocol.load_labware('nest_96_wellplate_2ml_deep', 2)
    stocks = protocol.load_labware('greiner_96_wellplate_300ul', 6)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])

    # reagents     
    global proteins, sypro, protein_destinations
    sypro = stocks.columns()[0]
    proteins = stocks.columns()[1:1 + protocol.params.proteins]
    protein_destinations = [
        [plate.rows()[protein_index % 2][2 * column_index + protein_index // 2]
         for column_index in range(12)]
        for protein_index in range(protocol.params.proteins)]

def define_liquids(protocol):
    for well in screen.wells():
        screen_liquid = protocol.define_liquid(
            name=f'Rubic screen {well.well_name}',
            description=f'Screen condition {well.well_name}; load 200 uL in this well.',
            display_color='#50C878')
        well.load_liquid(liquid=screen_liquid, volume=200)

    sypro_liquid = protocol.define_liquid(
        name='SYPRO 62.5x',
        description='Load 150 uL in each well A1-H1 of the stocks plate; 5x final.',
        display_color='#FF6B6B')
    for well in sypro:
        well.load_liquid(liquid=sypro_liquid, volume=150)

    protein_colors = ['#4169E1', '#FFD700', '#8A2BE2', '#00BFFF']
    for protein_index, protein_column in enumerate(proteins):
        protein_liquid = protocol.define_liquid(
            name=f'Protein {protein_index + 1}',
            description=(f'62.5 uM stock; load 100 uL per well in stocks column '
                         f'{protein_index + 2}; 5 uM final.'),
            display_color=protein_colors[protein_index])
        for well in protein_column:
            well.load_liquid(liquid=protein_liquid, volume=100)

def add_buffer(protocol):
    for column_index, screen_column in enumerate(screen.columns()):
        p300m.pick_up_tip()
        p300m.aspirate(21 * len(proteins), screen_column[0])
        for destinations in protein_destinations:
            p300m.dispense(21, destinations[column_index])
        p300m.return_tip()

def touch_upper_wall(destination, side):
    wall_offset = Point(x=side * (destination.diameter / 2 - 0.3), y=0, z=0)
    p20m.move_to(destination.top(z=-1).move(wall_offset), speed=10)
    p20m.move_to(destination.top(z=1).move(wall_offset), speed=10)

def distribute_reagent(source, destinations, side):
    dispense_volume = 2
    disposal_volume = 2
    batch_size = 9
    for batch_start in range(0, len(destinations), batch_size):
        batch = destinations[batch_start:batch_start + batch_size]
        p20m.aspirate(dispense_volume * len(batch) + disposal_volume, source)
        for destination in batch:
            location = destination.top(z=-1).move(Point(x=side * 0.5, y=0, z=0))
            p20m.dispense(dispense_volume, location)
            touch_upper_wall(destination, side)
        p20m.blow_out(source.top(z=-2))
        p20m.touch_tip(source, v_offset=-2, speed=20)

def add_sypro(protocol):
    p20m.pick_up_tip()
    destinations = [destination for group in protein_destinations for destination in group]
    distribute_reagent(sypro[0], destinations, side=-1)
    p20m.drop_tip()

def add_protein(protocol):
    for protein_column, destinations in zip(proteins, protein_destinations):
        p20m.pick_up_tip()
        distribute_reagent(protein_column[0], destinations, side=1)
        p20m.drop_tip()
