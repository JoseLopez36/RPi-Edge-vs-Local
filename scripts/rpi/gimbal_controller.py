"""
Gimbal Control Module (SIYI A8 Mini)
"""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass
from typing import Optional, Tuple

STX = b"\x55\x66"

# Default A8 Mini safety limits (degrees). Adjust if your gimbal is configured differently.
DEFAULT_YAW_MIN, DEFAULT_YAW_MAX = -135.0, 135.0
DEFAULT_PITCH_MIN, DEFAULT_PITCH_MAX = -90.0, 45.0

@dataclass(frozen=True)
class Attitude:
    yaw_deg: float
    pitch_deg: float
    roll_deg: float

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def _crc16_xmodem(data: bytes, init: int = 0x0000) -> int:
    crc = init & 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) & 0xFFFF) ^ 0x1021
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF

def _build_packet(cmd_id: int, data: bytes, seq: int, *, need_ack: bool) -> bytes:
    # CTRL bit0=need_ack, bit1=ack_pack
    ctrl = 0x01 if need_ack else 0x00
    header = STX + struct.pack("<BHHB", ctrl, len(data), seq & 0xFFFF, cmd_id & 0xFF)
    body = header + data
    crc = _crc16_xmodem(body)
    return body + struct.pack("<H", crc)

def _parse_packet(raw: bytes) -> Optional[Tuple[int, int, int, bytes]]:
    # STX(2) + ctrl(1) + len(2) + seq(2) + cmd(1) + crc(2) = 10 bytes min
    if len(raw) < 10 or raw[0:2] != STX:
        return None

    recv_crc = struct.unpack("<H", raw[-2:])[0]
    calc_crc = _crc16_xmodem(raw[:-2])
    if recv_crc != calc_crc:
        return None

    ctrl = raw[2]
    data_len = struct.unpack("<H", raw[3:5])[0]
    seq = struct.unpack("<H", raw[5:7])[0]
    cmd_id = raw[7]
    data = raw[8 : 8 + data_len]
    return ctrl, seq, cmd_id, data

class GimbalController:
    CMD_GET_ATTITUDE = 0x0D
    CMD_SET_ANGLES = 0x0E

    def __init__(
        self,
        gimbal_ip: str = "192.168.144.25",
        gimbal_port: int = 37260,
        timeout_s: float = 0.35,
        yaw_min: float = DEFAULT_YAW_MIN,
        yaw_max: float = DEFAULT_YAW_MAX,
        pitch_min: float = DEFAULT_PITCH_MIN,
        pitch_max: float = DEFAULT_PITCH_MAX
    ):
        self.gimbal_ip = gimbal_ip
        self.gimbal_port = int(gimbal_port)
        self.timeout_s = float(timeout_s)
        self.yaw_min = float(yaw_min)
        self.yaw_max = float(yaw_max)
        self.pitch_min = float(pitch_min)
        self.pitch_max = float(pitch_max)

        self._sock: Optional[socket.socket] = None
        self._seq: int = 0
        self.connected: bool = False

        print(f"Initializing SIYI Gimbal Controller (IP: {self.gimbal_ip}, Port: {self.gimbal_port})")

    def connect(self):
        """Create UDP socket"""
        if self.connected:
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(self.timeout_s)
        self.connected = True
        print("Gimbal connected (UDP socket ready)")

    def disconnect(self):
        """Close UDP socket"""
        try:
            if self._sock is not None:
                try:
                    self._sock.close()
                finally:
                    self._sock = None
        finally:
            self.connected = False
            print("Gimbal disconnected")

    def _next_seq(self) -> int:
        seq = self._seq & 0xFFFF
        self._seq = (self._seq + 1) & 0xFFFF
        return seq

    def _ensure_connected(self) -> socket.socket:
        if not self.connected or self._sock is None:
            print("Warning: gimbal not connected, connecting now...")
            self.connect()
        assert self._sock is not None
        return self._sock

    def request_attitude(self) -> Optional[Attitude]:
        """Request current gimbal attitude (yaw/pitch/roll)"""
        sock = self._ensure_connected()
        seq = self._next_seq()

        pkt = _build_packet(self.CMD_GET_ATTITUDE, b"", seq, need_ack=True)
        sock.sendto(pkt, (self.gimbal_ip, self.gimbal_port))

        deadline = time.time() + self.timeout_s
        while time.time() < deadline:
            try:
                raw, _ = sock.recvfrom(2048)
            except socket.timeout:
                break
            p = _parse_packet(raw)
            if not p:
                continue
            _ctrl, _rseq, cmd_id, data = p
            if cmd_id != self.CMD_GET_ATTITUDE or len(data) < 12:
                continue
            yaw_i, pitch_i, roll_i, _, _, _ = struct.unpack("<hhhhhh", data[:12])
            return Attitude(yaw_i / 10.0, pitch_i / 10.0, roll_i / 10.0)

        return None

    def set_pan_tilt(self, pan_angle: float, tilt_angle: float):
        """
        Set yaw/pitch angles (pan=yaw, tilt=pitch)

        Args:
            pan_angle: yaw degrees
            tilt_angle: pitch degrees
        """
        sock = self._ensure_connected()
        seq = self._next_seq()

        yaw_deg = _clamp(float(pan_angle), self.yaw_min, self.yaw_max)
        pitch_deg = _clamp(float(tilt_angle), self.pitch_min, self.pitch_max)

        data = struct.pack(
            "<hh", int(round(yaw_deg * 10.0)), int(round(pitch_deg * 10.0))
        )
        pkt = _build_packet(self.CMD_SET_ANGLES, data, seq, need_ack=False)
        sock.sendto(pkt, (self.gimbal_ip, self.gimbal_port))

    def reset_position(self):
        """Convenience: center yaw/pitch at 0°"""
        self.set_pan_tilt(0.0, 0.0)

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()

    def __del__(self):
        try:
            if self.connected:
                self.disconnect()
        except Exception:
            pass