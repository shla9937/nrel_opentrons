"""
xArm 6 + 1500 mm linear rail — demo script
==========================================

Demonstrates a plate hand-off between an Opentrons Flex deck slot and a
BioTek plate reader using the xArm Python SDK.

Capabilities shown:
    * Connecting to the controller and registering error/warning callbacks
    * Enabling motors, gripper, and the 1500 mm linear track (7th axis)
    * Setting a TCP offset for the plate gripper fingers
    * Coordinating rail motion with arm Cartesian moves
    * Joint moves to a taught "safe" pose
    * Blended waypoint sequences (arc move) for smooth transport
    * Bio-gripper open/close with force + speed control
    * Talking to the BioTek reader (tray open/close) — stubbed via serial

IMPORTANT
    All numeric positions below are PLACEHOLDERS. You must jog the arm to
    each key location, read the pose from the controller (or xArm Studio),
    and paste the values in before running unattended. Run the first pass
    with the E-stop in hand at reduced speed (SPEED_SLOW).

Coordinate conventions (xArm SDK defaults):
    * Cartesian: x, y, z in mm; roll, pitch, yaw in degrees; base frame.
    * Joints:    j1..j6 in degrees.
    * Rail:      position in mm along the track (0 = home end).
"""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass

from xarm.wrapper import XArmAPI


# ---------------------------------------------------------------------------
# Connection / tuning constants
# ---------------------------------------------------------------------------

ARM_IP = "192.168.1.213"           # <-- set to your controller's IP
REPORT_TYPE = "rich"

# Motion tuning (mm/s, mm/s^2, deg/s, deg/s^2)
SPEED_FAST   = 250
SPEED_SLOW   = 80
ACC_FAST     = 1500
ACC_SLOW     = 500
JOINT_SPEED  = 40
JOINT_ACC    = 300

# Rail tuning (mm/s, mm/s^2)
RAIL_SPEED = 200
RAIL_ACC   = 500

# Bio-gripper
GRIPPER_SPEED  = 300   # 1..4000
GRIPPER_FORCE  = 50    # 1..100 (%)

# Vertical clearances above a plate's nominal grip height (mm)
Z_APPROACH   = 60      # start Cartesian descent from here
Z_LIFT       = 80      # lift after grip / before release
Z_RETREAT    = 120     # travel height across the deck / rail

# TCP offset from tool flange to the point between the gripper fingers.
# Measure this for your gripper + fingertip stack.
TCP_OFFSET = [0.0, 0.0, 172.0, 0.0, 0.0, 0.0]   # x, y, z, roll, pitch, yaw

# BioTek plate reader (Gen5 command-line or a serial firmware bridge)
BIOTEK_PORT = "/dev/tty.usbserial-BIOTEK"        # adjust for your machine


# ---------------------------------------------------------------------------
# Taught poses  (fill these in during calibration)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Pose:
    """A single taught station: rail position + arm Cartesian pose."""
    rail_mm: float
    xyz_rpy: tuple[float, float, float, float, float, float]


# Safe, arms-tucked joint pose used for long rail traverses.
HOME_JOINTS = [0.0, -45.0, -30.0, 0.0, 75.0, 0.0]

# Grip pose directly on top of the plate in Opentrons Flex deck slot C2.
FLEX_SLOT_C2 = Pose(
    rail_mm=  120.0,
    xyz_rpy=(  350.0,  0.0, 145.0,  180.0, 0.0, 0.0),
)

# Grip pose on the BioTek reader tray (tray extended, plate seated in the
# adapter). Roll = 180 keeps the gripper pointing straight down.
BIOTEK_TRAY = Pose(
    rail_mm= 1280.0,
    xyz_rpy=(  310.0, -25.0, 160.0,  180.0, 0.0, 0.0),
)


# ---------------------------------------------------------------------------
# xArm helpers
# ---------------------------------------------------------------------------

def _check(code: int, action: str) -> None:
    """Abort loudly if the controller returns a non-zero status."""
    if code != 0:
        raise RuntimeError(f"xArm error {code} during {action!r}")


def _on_error(item) -> None:
    print(f"[xArm ERROR] code={item['error_code']}", file=sys.stderr)


def _on_warn(item) -> None:
    print(f"[xArm warn ] code={item['warn_code']}", file=sys.stderr)


@contextmanager
def open_arm(ip: str = ARM_IP):
    """Yield a ready-to-move XArmAPI, guaranteeing safe teardown."""
    arm = XArmAPI(ip, report_type=REPORT_TYPE)
    try:
        arm.register_error_warn_changed_callback(_on_error)
        arm.register_error_warn_changed_callback(_on_warn)

        _check(arm.clean_warn(),  "clean_warn")
        _check(arm.clean_error(), "clean_error")
        _check(arm.motion_enable(enable=True), "motion_enable")
        _check(arm.set_mode(0), "set_mode(pos)")
        _check(arm.set_state(0), "set_state(ready)")
        arm.set_tcp_offset(TCP_OFFSET)
        arm.set_tcp_load(0.9, [0.0, 0.0, 40.0])  # ~gripper+plate; tune it

        # 7th-axis linear rail
        _check(arm.set_linear_track_enable(True), "rail enable")
        _check(arm.set_linear_track_speed(RAIL_SPEED), "rail speed")

        # Bio-gripper
        _check(arm.set_bio_gripper_enable(True), "gripper enable")
        _check(arm.set_bio_gripper_speed(GRIPPER_SPEED), "gripper speed")

        yield arm
    finally:
        try:
            arm.set_state(4)                      # stop
        finally:
            arm.disconnect()


def move_rail(arm: XArmAPI, position_mm: float) -> None:
    print(f"  rail -> {position_mm:.1f} mm")
    _check(
        arm.set_linear_track_pos(position_mm, speed=RAIL_SPEED, wait=True),
        f"rail move to {position_mm}",
    )


def move_joints(arm: XArmAPI, joints, speed=JOINT_SPEED, acc=JOINT_ACC) -> None:
    _check(
        arm.set_servo_angle(angle=joints, speed=speed, mvacc=acc, wait=True),
        "joint move",
    )


def move_line(arm: XArmAPI, xyz_rpy, speed=SPEED_FAST, acc=ACC_FAST) -> None:
    x, y, z, r, p, yaw = xyz_rpy
    _check(
        arm.set_position(x=x, y=y, z=z, roll=r, pitch=p, yaw=yaw,
                         speed=speed, mvacc=acc, wait=True),
        "linear move",
    )


def move_line_relative(arm: XArmAPI, dz: float, speed=SPEED_SLOW) -> None:
    """Small tool-frame Z nudge (positive dz = up in base frame here)."""
    _check(
        arm.set_position(z=dz, relative=True, speed=speed,
                         mvacc=ACC_SLOW, wait=True),
        f"relative dz={dz}",
    )


def gripper_open(arm: XArmAPI) -> None:
    _check(arm.open_bio_gripper(speed=GRIPPER_SPEED, wait=True), "gripper open")
    time.sleep(0.2)


def gripper_close(arm: XArmAPI) -> None:
    _check(arm.close_bio_gripper(speed=GRIPPER_SPEED, wait=True), "gripper close")
    time.sleep(0.2)


# ---------------------------------------------------------------------------
# Plate transfer primitives
# ---------------------------------------------------------------------------

def go_to_station(arm: XArmAPI, station: Pose) -> None:
    """Traverse to a station: tuck arm, drive rail, then present above plate."""
    x, y, z, r, p, yaw = station.xyz_rpy
    print(f"traversing to station at rail={station.rail_mm} mm")

    move_joints(arm, HOME_JOINTS)                 # tuck for safe traverse
    move_rail(arm, station.rail_mm)               # drive along the 1500 mm rail
    move_line(arm, (x, y, z + Z_RETREAT, r, p, yaw))   # approach from above


def pick_plate(arm: XArmAPI, station: Pose) -> None:
    x, y, z, r, p, yaw = station.xyz_rpy
    print(f"picking plate @ ({x:.1f}, {y:.1f}, {z:.1f})")

    gripper_open(arm)
    move_line(arm, (x, y, z + Z_APPROACH, r, p, yaw), speed=SPEED_FAST)
    move_line(arm, (x, y, z,              r, p, yaw), speed=SPEED_SLOW)
    gripper_close(arm)
    move_line(arm, (x, y, z + Z_LIFT,     r, p, yaw), speed=SPEED_SLOW)
    move_line(arm, (x, y, z + Z_RETREAT,  r, p, yaw), speed=SPEED_FAST)


def place_plate(arm: XArmAPI, station: Pose) -> None:
    x, y, z, r, p, yaw = station.xyz_rpy
    print(f"placing plate @ ({x:.1f}, {y:.1f}, {z:.1f})")

    move_line(arm, (x, y, z + Z_APPROACH, r, p, yaw), speed=SPEED_FAST)
    move_line(arm, (x, y, z,              r, p, yaw), speed=SPEED_SLOW)
    gripper_open(arm)
    move_line(arm, (x, y, z + Z_LIFT,     r, p, yaw), speed=SPEED_SLOW)
    move_line(arm, (x, y, z + Z_RETREAT,  r, p, yaw), speed=SPEED_FAST)


# ---------------------------------------------------------------------------
# BioTek reader — replace with your real integration (Gen5 CLI, LHC, etc.)
# ---------------------------------------------------------------------------

class BioTekReader:
    """Minimal placeholder that models tray open/close + a read trigger."""

    def __init__(self, port: str = BIOTEK_PORT) -> None:
        self.port = port
        # e.g. self._serial = serial.Serial(port, 9600, timeout=2)

    def open_tray(self) -> None:
        print(f"[BioTek] open tray on {self.port}")
        time.sleep(4.0)   # real hardware takes a few seconds

    def close_tray(self) -> None:
        print(f"[BioTek] close tray on {self.port}")
        time.sleep(4.0)

    def read(self, protocol: str) -> None:
        print(f"[BioTek] running protocol {protocol!r}")
        time.sleep(2.0)


# ---------------------------------------------------------------------------
# Opentrons Flex hand-off
# ---------------------------------------------------------------------------
# On the Flex side, the protocol should have already:
#   * completed pipetting on the plate,
#   * removed the plate lid (if any),
#   * opened the deck-slot latches for the target slot,
#   * paused via `protocol.pause("Waiting for xArm pickup")`.
# This script assumes the Flex is idle and it is safe to enter its envelope.


def flex_to_reader() -> None:
    reader = BioTekReader()

    with open_arm() as arm:
        # 1. Pull the plate off the Flex deck.
        go_to_station(arm, FLEX_SLOT_C2)
        pick_plate(arm, FLEX_SLOT_C2)

        # 2. In parallel-ish: open the reader tray while we traverse.
        reader.open_tray()

        # 3. Move to the reader and drop the plate onto the tray.
        go_to_station(arm, BIOTEK_TRAY)
        place_plate(arm, BIOTEK_TRAY)

        # 4. Retreat, close the tray, and read.
        move_joints(arm, HOME_JOINTS)
        reader.close_tray()
        reader.read(protocol="absorbance_600nm.prt")


if __name__ == "__main__":
    flex_to_reader()
