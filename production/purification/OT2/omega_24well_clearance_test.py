from opentrons import protocol_api

metadata = {
    'protocolName': 'Omega 24-well Clearance Test',
    'author': 'Shawn Laursen',
    'description': 'Dry rim-access test with an empty plate; does not validate deep sampling.',
    'apiLevel': '2.26'}


def run(protocol: protocol_api.ProtocolContext):
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tips300])
    hs_mod = protocol.load_module('heaterShakerModuleV1', 1)
    adapter = hs_mod.load_adapter('opentrons_universal_flat_adapter')
    plate24 = adapter.load_labware(
        'omega_24_wellplate_25000ul', namespace='custom_beta', version=1)

    protocol.set_rail_lights(True)
    hs_mod.deactivate_heater()
    hs_mod.close_labware_latch()
    hs_mod.deactivate_shaker()

    for name in ('A1', 'D1', 'A6', 'D6', 'B3', 'C4'):
        well = plate24[name]
        for offset in (5, 0, -2):
            p300.move_to(well.top(offset), speed=10, force_direct=offset != 5)
        p300.move_to(well.top(5), speed=10, force_direct=True)
        
    protocol.set_rail_lights(False)
