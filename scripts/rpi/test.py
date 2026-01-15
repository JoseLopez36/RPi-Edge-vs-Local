import socket
import struct
import time

GIMBAL_IP = "192.168.144.25"
GIMBAL_PORT = 37260
TIMEOUT_S = 0.35

# Rangos A8 mini (grados)
YAW_MIN, YAW_MAX = -135.0, 135.0
PITCH_MIN, PITCH_MAX = -90.0, 45.0    # (realidad no coincide con el dataset)

STX = b"\x55\x66"

def crc16_xmodem(data: bytes, init: int = 0x0000) -> int:
    crc = init & 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) & 0xFFFF) ^ 0x1021
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF

def build_packet(cmd_id: int, data: bytes, seq: int, need_ack: bool) -> bytes:
    # CTRL bit0=need_ack, bit1=ack_pack
    ctrl = 0x01 if need_ack else 0x00
    header = STX + struct.pack("<BHHB", ctrl, len(data), seq, cmd_id)
    body = header + data
    crc = crc16_xmodem(body)
    return body + struct.pack("<H", crc)

def parse_packet(raw: bytes):
    if len(raw) < 10 or raw[0:2] != STX:
        return None
    recv_crc = struct.unpack("<H", raw[-2:])[0]
    calc_crc = crc16_xmodem(raw[:-2])
    if recv_crc != calc_crc:
        return None

    ctrl = raw[2]
    data_len = struct.unpack("<H", raw[3:5])[0]
    seq = struct.unpack("<H", raw[5:7])[0]
    cmd_id = raw[7]
    data = raw[8:8 + data_len]
    return ctrl, seq, cmd_id, data

def ask_float(prompt: str):
    s = input(prompt).strip()
    if s.lower() in ("q", "quit", "exit"):
        return None
    return float(s)

def clamp(v, a, b):
    return max(a, min(b, v))

def request_attitude(sock, seq):
    # CMD 0x0D
    pkt = build_packet(0x0D, b"", seq, need_ack=True)
    sock.sendto(pkt, (GIMBAL_IP, GIMBAL_PORT))

    t0 = time.time()
    while time.time() - t0 < TIMEOUT_S:
        try:
            raw, _ = sock.recvfrom(2048)
        except socket.timeout:
            break
        p = parse_packet(raw)
        if not p:
            continue
        ctrl, rseq, cmd_id, data = p
        # a veces llega como stream o ack, nos da igual: queremos el payload
        if cmd_id == 0x0D and len(data) >= 12:
            yaw_i, pitch_i, roll_i, _, _, _ = struct.unpack("<hhhhhh", data[:12])
            return (yaw_i/10.0, pitch_i/10.0, roll_i/10.0)
    return None

def set_angles_with_ack(sock, seq, yaw_deg, pitch_deg):
    # Safety: recorta a rango (A8 mini)
    yaw_deg = clamp(yaw_deg, YAW_MIN, YAW_MAX)
    pitch_deg = clamp(pitch_deg, PITCH_MIN, PITCH_MAX)

    data = struct.pack("<hh", int(round(yaw_deg * 10.0)), int(round(pitch_deg * 10.0)))
    pkt = build_packet(0x0E, data, seq, need_ack=True)
    sock.sendto(pkt, (GIMBAL_IP, GIMBAL_PORT))

    t0 = time.time()
    while time.time() - t0 < TIMEOUT_S:
        try:
            raw, _ = sock.recvfrom(2048)
        except socket.timeout:
            break
        p = parse_packet(raw)
        if not p:
            continue
        ctrl, rseq, cmd_id, rdata = p
        is_ack = (ctrl & 0x02) != 0
        if cmd_id == 0x0E and is_ack and len(rdata) >= 6:
            cy, cp, cr = struct.unpack("<hhh", rdata[:6])
            return True, (cy/10.0, cp/10.0, cr/10.0), (yaw_deg, pitch_deg)
    return False, None, (yaw_deg, pitch_deg)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_S)
    seq = 0

    print("A8 mini control yaw/pitch (q para salir)")
    print(f"Rango A8 mini: yaw [{YAW_MIN},{YAW_MAX}] pitch [{PITCH_MIN},{PITCH_MAX}]")
    print("Pediré yaw, luego pitch, enviaré y confirmaré.\n")

    try:
        while True:
            try:
                yaw = ask_float("Yaw (deg): ")
                if yaw is None:
                    break
                pitch = ask_float("Pitch (deg): ")
                if pitch is None:
                    break
            except ValueError:
                print("[ERR] mete un número válido.\n")
                continue

            before = request_attitude(sock, seq)
            seq = (seq + 1) & 0xFFFF

            ok, ack_angles, sent = set_angles_with_ack(sock, seq, yaw, pitch)
            seq = (seq + 1) & 0xFFFF

            after = request_attitude(sock, seq)
            seq = (seq + 1) & 0xFFFF

            print(f"Objetivo (clipped): yaw={sent[0]:+.1f} pitch={sent[1]:+.1f}")
            if before:
                print(f"Antes:  yaw={before[0]:+.1f} pitch={before[1]:+.1f} roll={before[2]:+.1f}")
            else:
                print("Antes:  (no leído)")

            if ok:
                cy, cp, cr = ack_angles
                print(f"ACK:    yaw={cy:+.1f} pitch={cp:+.1f} roll={cr:+.1f}")
            else:
                print("[WARN] No llegó ACK del comando 0x0E")

            if after:
                print(f"Después:yaw={after[0]:+.1f} pitch={after[1]:+.1f} roll={after[2]:+.1f}")
            else:
                print("Después:(no leído)")

            if after and before:
                dy = after[0] - before[0]
                dp = after[1] - before[1]
                print(f"Delta:  dy={dy:+.2f} dp={dp:+.2f}\n")
            else:
                print()

    finally:
        sock.close()

if __name__ == "__main__":
    main()