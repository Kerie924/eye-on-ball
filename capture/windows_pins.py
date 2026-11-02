"""Fixed Windows button wiring (Arduino / USB serial board).

Each camera uses one digital pair: signal pin + GND pin.
Wire the NO push button between the two pins of the pair.

CAM 1 → D2 (signal), D3 (GND)
CAM 2 → D4 (signal), D5 (GND)
CAM 3 → D6 (signal), D7 (GND)
CAM 4 → D8 (signal), D9 (GND)
CAM 5 → D10 (signal), D11 (GND)
CAM 6 → D12 (signal), D13 (GND)

Copy the capture software as-is; these pairs never change.
"""

from __future__ import annotations

# camera_index -> (arduino_signal_pin, arduino_gnd_pin)
CAMERA_ARDUINO_PAIRS: dict[int, tuple[int, int]] = {
    1: (2, 3),
    2: (4, 5),
    3: (6, 7),
    4: (8, 9),
    5: (10, 11),
    6: (12, 13),
}

DEFAULT_BAUD = 115200
HUB_READY_TOKEN = "LANCEON_BUTTONS_READY"


def camera_signal_pin(camera_index: int) -> int:
    if camera_index not in CAMERA_ARDUINO_PAIRS:
        raise ValueError(f"No Windows pin pair for camera {camera_index}")
    return CAMERA_ARDUINO_PAIRS[camera_index][0]


def camera_gnd_pin(camera_index: int) -> int:
    if camera_index not in CAMERA_ARDUINO_PAIRS:
        raise ValueError(f"No Windows pin pair for camera {camera_index}")
    return CAMERA_ARDUINO_PAIRS[camera_index][1]


def camera_button_yaml(camera_index: int, *, enabled: bool = True) -> str:
    """YAML snippet: camera listens to the shared serial hub (message = camera index)."""
    if not enabled:
        return "    button:\n      type: none"
    signal, gnd = CAMERA_ARDUINO_PAIRS[camera_index]
    return "\n".join(
        [
            "    button:",
            "      type: serial_hub",
            f"      trigger_on: \"{camera_index}\"  # Arduino D{signal}+D{gnd}",
        ]
    )


def button_hub_yaml(*, port: str = "auto", baudrate: int = DEFAULT_BAUD) -> str:
    return "\n".join(
        [
            "button_hub:",
            "  type: serial",
            f"  port: {port}  # auto = first Arduino/CH340/CP210x COM port",
            f"  baudrate: {baudrate}",
        ]
    )


def wiring_table() -> str:
    lines = ["Camera | Signal | GND", "-------|--------|----"]
    for index in sorted(CAMERA_ARDUINO_PAIRS):
        signal, gnd = CAMERA_ARDUINO_PAIRS[index]
        lines.append(f"CAM {index}  | D{signal}     | D{gnd}")
    return "\n".join(lines)
