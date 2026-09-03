"""Default GPIO button assignment per camera (BCM numbering)."""

# camera_index -> (bcm_signal, header_signal, bcm_gnd_or_none, header_gnd)
# Camera 2 uses header 13+15: pin 15 = GPIO22 (input), pin 13 = GPIO27 driven LOW as GND.
CAMERA_GPIO: dict[int, tuple[int, int, int | None, int | None]] = {
    1: (17, 11, None, 9),
    2: (22, 15, 27, 13),
    3: (23, 16, None, 14),
    4: (24, 18, None, 20),
    5: (25, 22, None, 20),
    6: (5, 29, None, 30),
}


def camera_gpio_pin(camera_index: int) -> int:
    if camera_index not in CAMERA_GPIO:
        raise ValueError(f"No default GPIO for camera {camera_index}")
    return CAMERA_GPIO[camera_index][0]


def camera_button_yaml(camera_index: int, *, enabled: bool = True) -> str:
    if not enabled:
        return "    button:\n      type: none"
    pin, physical, gnd_bcm, gnd_phys = CAMERA_GPIO[camera_index]
    lines = [
        "    button:",
        "      type: gpio",
        f"      pin: {pin}  # header pin {physical}",
    ]
    if gnd_bcm is not None:
        lines.append(f"      gnd_pin: {gnd_bcm}  # header pin {gnd_phys} driven LOW")
    return "\n".join(lines)
