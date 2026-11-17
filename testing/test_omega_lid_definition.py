"""Simulation-only regression checks; these do not qualify the printed lid."""

import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import jsonschema
from opentrons import simulate
from opentrons.motion_planning import get_gripper_labware_movement_waypoints
from opentrons.protocol_api.core.engine import ProtocolCore
from opentrons.protocol_engine.errors import ProtocolCommandFailedError
from opentrons.protocol_engine.state.geometry import GeometryView
from opentrons.protocol_engine.types import GripperMoveType, OnLabwareLocation
from opentrons.types import Point
from opentrons_shared_data import load_shared_data
from opentrons_shared_data.labware.labware_definition import LabwareDefinition
from pydantic import TypeAdapter


ROOT = Path(__file__).resolve().parents[1]
PLATE = "omega_24_wellplate_25000ul"
LID = "omega_24well_gripper_lid"


def definition(name):
    return json.loads((ROOT / "custom_labware" / f"{name}.json").read_text())


class OmegaLidDefinitionTests(unittest.TestCase):
    def test_definitions_validate(self):
        for name in (PLATE, LID):
            with self.subTest(name=name):
                data = definition(name)
                schema = json.loads(
                    load_shared_data(f"labware/schemas/{data['schemaVersion']}.json")
                )
                jsonschema.validate(data, schema)
                TypeAdapter(LabwareDefinition).validate_python(data)
        lid = definition(LID)
        self.assertEqual(lid["ordering"], [])
        self.assertEqual(lid["wells"], {})
        self.assertEqual(lid["allowedRoles"], ["labware", "lid"])

    def test_seated_geometry_and_closed_latch_round_trip(self):
        for api in ("2.28", "2.31"):
            with self.subTest(api=api):
                self.check_round_trip(api)

    def check_round_trip(self, api):
        ctx = simulate.get_protocol_api(
            api, robot_type="Flex",
            extra_labware={name: definition(name) for name in (PLATE, LID)},
        )
        hs = ctx.load_module("heaterShakerModuleV1", "B1")
        adapter = hs.load_adapter("opentrons_universal_flat_adapter")
        plate = adapter.load_labware(
            PLATE, namespace="custom_beta", version=1,
            lid=LID, lid_namespace="custom_beta", lid_version=1,
        )
        parking = ctx.load_labware(PLATE, "D2", namespace="custom_beta", version=1)
        self.assertIsInstance(ctx._core, ProtocolCore)
        state = ctx._core._engine_client.state
        lid_id = state.labware.get_lid_id_by_labware_id(plate._core.labware_id)
        self.assertIsNotNone(lid_id)
        lid_def = state.labware.get_definition(lid_id)
        hs.close_labware_latch()
        hs.set_and_wait_for_shake_speed(900)
        hs.deactivate_shaker()

        def check_seated(parent):
            parent_id = parent._core.labware_id
            base = state.geometry.get_labware_position(parent_id)
            self.assertPointAlmostEqual(
                base, Point(0, 214, 25.375) if parent is plate else Point(164, 0, 0)
            )
            origin = state.geometry.get_labware_position(lid_id)
            self.assertPointAlmostEqual(origin - base, Point(5.5, 86.5, 67.55))
            bbox = lid_def.extents.total
            back_left = origin + Point.from_xyz_attrs(bbox.backLeftBottom)
            front_right = origin + Point.from_xyz_attrs(bbox.frontRightTop)
            self.assertPointAlmostEqual(back_left - base, Point(5.5, 86.5, 67.55))
            self.assertPointAlmostEqual(front_right - base, Point(121.9, -1.5, 90.7))
            self.assertAlmostEqual(
                state.geometry.get_labware_highest_z(lid_id) - base.z, 90.7
            )
            for move_type in (
                GripperMoveType.PICK_UP_LABWARE, GripperMoveType.DROP_LABWARE
            ):
                grip = state.geometry.get_labware_grip_point(
                    lid_def, OnLabwareLocation(labwareId=parent_id), move_type, None
                )
                # SDK 10.1 applies a deck drop bias even when the target is a plate.
                expected_z = (
                    87.05 if parent is parking and move_type == GripperMoveType.DROP_LABWARE
                    else 87.8
                )
                self.assertPointAlmostEqual(grip - base, Point(63.7, 42.5, expected_z))
            return base + Point(63.7, 42.5, 87.8)

        module_grip = check_seated(plate)
        parking_grip = (
            state.geometry.get_labware_position(parking._core.labware_id)
            + Point(63.7, 42.5, 87.8)
        )
        requested_grips = []
        original = GeometryView.get_labware_grip_point

        def record_grip(view, *args, **kwargs):
            result = original(view, *args, **kwargs)
            requested_grips.append(result)
            return result

        # Observe the real execution helper; do not replace its geometry or checks.
        with patch.object(GeometryView, "get_labware_grip_point", record_grip):
            ctx.move_lid(
                plate, parking, use_gripper=True,
                drop_offset={"x": 0, "y": 0, "z": 0.75},
            )
            ctx.move_lid(parking, plate, use_gripper=True)
        self.assertEqual(len(requested_grips), 4)
        for actual, expected in zip(
            requested_grips, (module_grip, parking_grip, parking_grip, module_grip)
        ):
            self.assertPointAlmostEqual(actual, expected)
        # Analysis has a virtual gripper; exercise the same waypoint builder used
        # by physical execution, including its final position before jaw release.
        for start, end in ((module_grip, parking_grip), (parking_grip, module_grip)):
            waypoints = get_gripper_labware_movement_waypoints(start, end, 300, None)
            self.assertPointAlmostEqual(waypoints[1].position, start)
            release = next(i for i, waypoint in enumerate(waypoints) if waypoint.dropping)
            self.assertPointAlmostEqual(waypoints[release - 1].position, end)
        check_seated(plate)
        ctx.move_lid(
            plate, parking, use_gripper=True,
            drop_offset={"x": 0, "y": 0, "z": 0.75},
        )
        check_seated(parking)

    def test_cad_mesh_envelope(self):
        mesh = (ROOT / "3d_parts" / LID / f"{LID}.stl").read_bytes()
        count = struct.unpack_from("<I", mesh, 80)[0]
        self.assertEqual(len(mesh), 84 + 50 * count)
        vertices = [
            struct.unpack_from("<3f", mesh, 84 + 50 * facet + 12 + 12 * vertex)
            for facet in range(count) for vertex in range(3)
        ]
        minimum = Point(*(min(v[axis] for v in vertices) for axis in range(3)))
        maximum = Point(*(max(v[axis] for v in vertices) for axis in range(3)))
        self.assertPointAlmostEqual(minimum, Point(-58.2, -44, -23.15))
        self.assertPointAlmostEqual(maximum, Point(58.2, 44, 0))
        extents = definition(LID)["extents"]["total"]
        back = Point(**extents["backLeftBottom"])
        front = Point(**extents["frontRightTop"])
        self.assertPointAlmostEqual(
            maximum - minimum, Point(front.x - back.x, back.y - front.y, front.z - back.z)
        )

    def test_rejected_access_and_destinations(self):
        ctx = simulate.get_protocol_api(
            "2.28", robot_type="Flex",
            extra_labware={name: definition(name) for name in (PLATE, LID)},
        )
        plate = ctx.load_labware(
            PLATE, "D2", namespace="custom_beta", version=1,
            lid=LID, lid_namespace="custom_beta", lid_version=1,
        )
        wrong = ctx.load_labware("corning_96_wellplate_360ul_flat", "D3")
        pipette = ctx.load_instrument("flex_1channel_1000", "left")
        cases = (
            ("covered by a lid", lambda: pipette.move_to(plate["A1"].top())),
            ("Cannot move labware.*with gripper",
             lambda: ctx.move_labware(plate, "D1", use_gripper=True)),
            ("may not be loaded on parent labware Corning",
             lambda: ctx.move_lid(plate, wrong, use_gripper=True)),
            ("may not be loaded on parent labware Lid Stack",
             lambda: ctx.move_lid(plate, "C2", use_gripper=True)),
        )
        for message, action in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ProtocolCommandFailedError, message):
                    action()
        state = ctx._core._engine_client.state
        lid_id = state.labware.get_lid_id_by_labware_id(plate._core.labware_id)
        with self.assertRaisesRegex(ValueError, "may not be loaded on parent labware"):
            state.labware.raise_if_labware_cannot_be_stacked(
                state.labware.get_definition(lid_id), lid_id
            )
        with self.assertRaisesRegex(ProtocolCommandFailedError, "not compatible.*deck|cannot.*deck"):
            ctx.load_labware(LID, "C3", namespace="custom_beta", version=1)

    def test_bare_plate_ot2_loading_preserves_geometry(self):
        ctx = simulate.get_protocol_api(
            "2.28", robot_type="OT-2", extra_labware={PLATE: definition(PLATE)}
        )
        hs = ctx.load_module("heaterShakerModuleV1", "1")
        plate = hs.load_adapter("opentrons_universal_flat_adapter").load_labware(
            PLATE, namespace="custom_beta", version=1
        )
        self.assertEqual(len(plate.wells()), 24)
        state = ctx._core._engine_client.state
        base = state.geometry.get_labware_position(plate._core.labware_id)
        for column in range(6):
            for row, letter in enumerate("ABCD"):
                well = plate[f"{letter}{column + 1}"]
                self.assertEqual(well.max_volume, 24000)
                self.assertAlmostEqual(well.depth, 87.3)
                self.assertAlmostEqual(well.top().point.z, 163)
                self.assertPointAlmostEqual(
                    well.bottom().point - base,
                    Point(16.95 + 18.7 * column, 70.55 - 18.7 * row, 1),
                )

    def assertPointAlmostEqual(self, actual, expected):
        for value, target in zip(actual, expected):
            self.assertAlmostEqual(value, target, places=5)


if __name__ == "__main__":
    unittest.main()
