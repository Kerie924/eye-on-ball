"""Default GPIO button assignment per camera (BCM numbering)."""

# camera_index -> (bcm_gpio, physical_pin_on_40pin_header)
# Camera 2: button wired on physical pins 13 and 15 (signal = GPIO 22 on pin 15).
CAMERA_GPIO: dict[int, tuple[int, int]] = {
    1: (17, 11),
    2: (22, 15),
    3: (27, 13),
    4: (23, 16),
    5: (24, 18),
    6: (25, 22),
}


def camera_gpio_pin(camera_index: int) -> int:
    if camera_index not in CAMERA_GPIO:
        raise ValueError(f"No default GPIO for camera {camera_index}")
    return CAMERA_GPIO[camera_index][0]


def camera_button_yaml(camera_index: int, *, enabled: bool = True) -> str:
    if not enabled:
        return "    button:\n      type: none"
    pin = camera_gpio_pin(camera_index)
    physical = CAMERA_GPIO[camera_index][1]
    return (
        f"    button:\n"
        f"      type: gpio\n"
        f"      pin: {pin}  # camera {camera_index} — BCM GPIO {pin}, header pin {physical}"
    )
