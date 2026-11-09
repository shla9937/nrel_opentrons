from opentrons import protocol_api


metadata = {
    'protocolName': 'Auto-TB volume screen - replicate Omega 24-well plates',
    'author': 'Shawn Laursen',
    'description': (
        'Replicates selected by num_plates at runtime: GFP/RFP pairs at 2, 4, ..., 20 mL Auto-TB; column 6 empty. '
        'Bulk-aspirate each strain once with one tip, then dispense 10 uL per well using glycerol_50. '
        'Dispense 5 mm below the tracked surface; reused tips carry medium between same-strain wells. '
        'C1: 1.5 mL Eppendorf tubes, A1 GFP/B1 RFP; 100 uL per plate + 50 uL allowance each; 4 C without waiting. '
        'Auto-TB: 220 mL per plate + 60 mL reserve; current reservoir supports up to two plates. '
        'Omega geometry is estimated in the custom labware definition; confirm coordinates and clearance. '
        'NEST 1.5 mL snapcap aluminium-block geometry; verify Eppendorf tube seating and liquid heights.')}

requirements = {'robotType': 'Flex', 'apiLevel': '2.28'}


def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name='num_plates',
        display_name='Number of replicate plates',
        description='One plate in C2, or two plates in C2 and D2.',
        default=2,
        minimum=1,
        maximum=2,
        unit='plates')


def run(protocol):
    protocol.set_rail_lights(True)
    setup(protocol)
    define_liquids(protocol)
    add_media(protocol)
    inoculate(protocol)
    protocol.set_rail_lights(False)


def setup(protocol):
    global trash, pipette, tips1000, plates, media, temp_mod, stocks, destinations
    global inoculum_vol, media_start_vol, media_aspiration_height, stock_volumes, glycerol
    plate_load_name = 'omega_24_wellplate_25000ul'
    stock_block_load_name = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap'
    plate_slots = ('C2', 'D2')[:protocol.params.num_plates]
    inoculum_vol = 10
    stock_volumes = {strain: 10 * len(plate_slots) * inoculum_vol + 50 for strain in ('GFP', 'RFP')}
    media_start_vol = 220000 * len(plate_slots) + 60000
    media_aspiration_height = 3

    trash = protocol.load_trash_bin('D1')
    tips1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D3')
    temp_mod = protocol.load_module('temperature module gen2', 'C1')
    temp_block = temp_mod.load_labware(stock_block_load_name)
    stocks = {'GFP': temp_block['A1'], 'RFP': temp_block['B1']}
    plates = [protocol.load_labware(plate_load_name, slot) for slot in plate_slots]
    media = protocol.load_labware('omega_1_reservoir_600ml', 'C3')
    pipette = protocol.load_instrument('flex_96channel_1000')
    pipette.configure_nozzle_layout(style=protocol_api.SINGLE, start='H12', tip_racks=[tips1000])
    glycerol = protocol.get_liquid_class('glycerol_50')
    glycerol_settings = glycerol.get_for(pipette, tips1000)
    glycerol_settings.aspirate.aspirate_position.position_reference = 'liquid-meniscus'
    glycerol_settings.aspirate.aspirate_position.offset = (0, 0, -1)
    glycerol_settings.multi_dispense.dispense_position.position_reference = 'liquid-meniscus'
    glycerol_settings.multi_dispense.dispense_position.offset = (0, 0, -5)

    destinations = []
    for plate in plates:
        for pair_index, volume in enumerate(range(2000, 20001, 2000)):
            column = pair_index // 2 + 1
            rows = ('A', 'B') if pair_index % 2 == 0 else ('C', 'D')
            for strain, row in zip(('GFP', 'RFP'), rows):
                well = plate[f'{row}{column}']
                destinations.append((well, volume, strain))

    temp_mod.start_set_temperature(4)


def define_liquids(protocol):
    auto_tb = protocol.define_liquid(name='Auto-TB', description='Prepared Auto-TB medium', display_color='#D4AD32')
    media['A1'].load_liquid(liquid=auto_tb, volume=media_start_vol)
    for plate in plates:
        for well in plate.wells():
            well.load_liquid(liquid=auto_tb, volume=0)
    for strain, colour in (('GFP', '#35A853'), ('RFP', '#D94545')):
        liquid = protocol.define_liquid(name=strain, description=f'{strain} glycerol stock', display_color=colour)
        stocks[strain].load_liquid(liquid=liquid, volume=stock_volumes[strain])


def add_media(protocol):
    pipette.pick_up_tip()
    source = media['A1']
    for destination, volume, strain in destinations:
        for aliquot in range(volume // 1000):
            pipette.aspirate(1000, source.bottom(media_aspiration_height))
            pipette.dispense(1000, destination.top(z=2))
    pipette.drop_tip()


def inoculate(protocol):
    for strain in ('GFP', 'RFP'):
        wells = [destination for destination, volume, label in destinations if label == strain]
        pipette.distribute_with_liquid_class(glycerol, inoculum_vol, stocks[strain], wells, new_tip='once')