from opentrons import protocol_api
from opentrons.motion_planning.waypoints import MINIMUM_Z_MARGIN
from opentrons.types import Mount
import time

metadata = {
    'protocolName': 'Omega 24-well OD Test',
    'author': 'Shawn Laursen',
    'description': '''Incubate 5ml and 15ml over 48 hours, taking samples every hour and mixing them into lysis buffer. 
    Measure the appearance of sfGFP signal at the end to see when each inoculation went to expression.
    Have to use cutoff tip, just wash in between. Lying about 10ml 24 well plate and 300µL 96 well for height (use 25 and 2ml plates).''',
    'apiLevel': '2.26'}


def run(protocol: protocol_api.ProtocolContext):
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips300])
    hs_mod = protocol.load_module('heaterShakerModuleV1', 1)
    plate24 = hs_mod.load_labware('thomsoninstrument_24_wellplate_10400ul')
    plate96 = protocol.load_labware('greiner_96_wellplate_300ul', 8)
    res = protocol.load_labware('nest_1_reservoir_195ml', 7)
    
    protocol.set_rail_lights(True)
    hs_mod.close_labware_latch()
    hs_mod.set_target_temperature(celsius=37)
    
    p300.pick_up_tip()

    start_time = time.time()

    for hour in range(0,48):
        # if not protocol.is_simulating():
        #     while time.time() - start_time < hour*3600:
        #         protocol.delay(60)
        if not protocol.is_simulating():
            while time.time() - start_time < hour*60:
                protocol.delay(1)
        hs_mod.deactivate_shaker()

        # pull from 5ml 
        p300.move_to(plate24['A1'].top(35))
        p300.aspirate(40, plate24['A1'].bottom(-15))
        p300.move_to(plate24['A1'].top(35))

        # put into 96 well
        p300.move_to(plate96.wells()[hour].top(35))
        p300.dispense(40, plate96.wells()[hour].bottom(-20))
        p300.mix(3,100, plate96.wells()[hour])

        # wash tip off
        p300.mix(5,100, res['A1'].bottom(-15))

        # pull from 15ml 
        p300.move_to(plate24['A2'].top(35))
        p300.aspirate(40, plate24['A2'].bottom(10))
        p300.move_to(plate24['A2'].top(35))

        # put into 96 well
        p300.move_to(plate96.wells()[hour+48].top(35))
        p300.dispense(40, plate96.wells()[hour+48].bottom(-15))
        p300.mix(3,100, plate96.wells()[hour+48])

        # wash tip off
        p300.mix(5,100, res['A1'].bottom(-15))
        p300.move_to(res['A1'].top(35))

        hs_mod.set_and_wait_for_shake_speed(900)

    hs_mod.deactivate_heater() 
    hs_mod.deactivate_shaker() 
    protocol.set_rail_lights(False)
