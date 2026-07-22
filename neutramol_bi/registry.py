"""
Registry of all ThingsBoard devices and their telemetry keys,
extracted from the dashboard JSON configurations.

Calibration uses linear interpolation (same formula as ThingsBoard postFuncBody):
  y = y0 + ((y1 - y0) / (x1 - x0)) * (raw - x0), clamped to [y0, y1]

Key types:
  AI  = Analog Input  (4–20 mA sensor, calibrated via x0/x1 → y0/y1)
  DI  = Digital Input (0 or 1, no calibration)
  MI  = Modbus Input  (already engineering value)
  MB  = Modbus Bit    (0 or 1)
"""

# (device_id, key) -> (x0, x1, y0, y1)
CALIBRATIONS: dict[tuple[str, str], tuple[float, float, float, float]] = {
    # ── SISTEMA DE TRANSFERÊNCIA (RPBC / Usina Colorado) ──────────────────
    ("2a2202e0-4170-11f0-b75e-6957383adb97", "AI1"): (739, 3710, 0, 72000),
    ("2a2202e0-4170-11f0-b75e-6957383adb97", "AI2"): (739, 3710, 0, 72000),
    ("2a2202e0-4170-11f0-b75e-6957383adb97", "AI3"): (739, 3710, 0, 45.6),

    # ── Keeper RPBC / REVAP ────────────────────────────────────────────────
    ("c80b3ec0-5b8a-11f0-b75e-6957383adb97", "AI1"): (739, 3710, 0, 72000),
    ("c80b3ec0-5b8a-11f0-b75e-6957383adb97", "AI2"): (739, 3710, 0, 70000),
    ("c80b3ec0-5b8a-11f0-b75e-6957383adb97", "AI3"): (739, 3710, 0, 110),
    ("c80b3ec0-5b8a-11f0-b75e-6957383adb97", "AI4"): (739, 3710, 0, 110),
    ("c80b3ec0-5b8a-11f0-b75e-6957383adb97", "AI5"): (739, 3710, 0, 110),

    # ── Keeper Petrobrás REVAP ────────────────────────────────────────────
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI1"): (739, 3710, 0, 60000),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI2"): (739, 3710, 0, 60),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI3"): (739, 3710, 0, 60),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI4"): (739, 3710, 0, 60),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI5"): (739, 3710, 0, 60),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "AI6"): (739, 3710, 0, 60),
    ("abad0020-5db9-11f0-b75e-6957383adb97", "mi1"): (739, 3710, 0, 60),

    # ── Keeper Petrobrás REGAP ────────────────────────────────────────────
    ("55935550-5db8-11f0-b75e-6957383adb97", "AI1"): (739, 3710, 0, 24000),
    ("55935550-5db8-11f0-b75e-6957383adb97", "AI2"): (739, 3710, 0, 60),
    ("55935550-5db8-11f0-b75e-6957383adb97", "AI3"): (739, 3710, 0, 60),

    # ── Keeper Petrobrás RECAP ────────────────────────────────────────────
    ("a35f4c70-5db9-11f0-b75e-6957383adb97", "AI1"): (739, 3710, 0, 41900),
    ("a35f4c70-5db9-11f0-b75e-6957383adb97", "AI2"): (739, 3710, 0, 60),
    ("a35f4c70-5db9-11f0-b75e-6957383adb97", "AI3"): (739, 3710, 0, 60),

    # ── Keeper Gelita Mococa ──────────────────────────────────────────────
    ("2bc7b6f0-4525-11ef-b710-99594f319f7e", "AI1"): (739, 3710, 0, 24282),
}

# All devices with their client name, alias, and telemetry keys
DEVICES: list[dict] = [
    {
        "id": "2a2202e0-4170-11f0-b75e-6957383adb97",
        "name": "Sistema de Transferência RPBC / Usina Colorado",
        "client": "Petrobrás RPBC / Usina Colorado - Guaíra",
        "keys": ["AI1", "AI2", "AI3", "DI1", "DI2", "DI3", "DI4", "DI5", "DI6", "DI7", "DI8",
                 "MI1", "MB21", "MB23", "MB25", "MB27", "sys_boot_total"],
    },
    {
        "id": "c80b3ec0-5b8a-11f0-b75e-6957383adb97",
        "name": "Keeper RPBC",
        "client": "Petrobrás RPBC",
        "keys": ["AI1", "AI2", "AI3", "AI4", "AI5",
                 "DI1", "DI2", "DI3", "DI4", "DI5", "DI6", "DI7", "DI8"],
    },
    {
        "id": "abad0020-5db9-11f0-b75e-6957383adb97",
        "name": "Keeper Petrobrás REVAP",
        "client": "Petrobrás REVAP",
        "keys": ["AI1", "AI2", "AI3", "AI4", "AI5", "AI6", "DI8", "mi1"],
    },
    {
        "id": "55935550-5db8-11f0-b75e-6957383adb97",
        "name": "Keeper Petrobrás REGAP",
        "client": "Petrobrás REGAP",
        "keys": ["AI1", "AI2", "AI3", "DI3", "DI4", "DI6", "DI7"],
    },
    {
        "id": "a35f4c70-5db9-11f0-b75e-6957383adb97",
        "name": "Keeper Petrobrás RECAP",
        "client": "Petrobrás RECAP",
        "keys": ["AI1", "AI2", "AI3", "DI3", "DI4", "DI5", "DI6"],
    },
    {
        "id": "3c0433b0-6241-11f0-b75e-6957383adb97",
        "name": "Keeper Citrosuco Araras",
        "client": "Citrosuco - Araras",
        "keys": ["MI1", "MI3", "MI5", "MI6", "MI7", "MI8", "MI9-DeltaPos", "MI10",
                 "MB21", "MB27", "MB29", "MB30", "MB31", "MB32"],
    },
    {
        "id": "2bc7b6f0-4525-11ef-b710-99594f319f7e",
        "name": "Keeper Gelita Mococa",
        "client": "Gelita - Mococa",
        "keys": ["AI1"],
    },
    {
        "id": "4a4b4d60-5db8-11f0-b75e-6957383adb97",
        "name": "Keeper Ternium RJ",
        "client": "Ternium - RJ",
        "keys": ["MI1", "MI3", "MI4", "MI5", "MI6", "MI7", "MI8",
                 "MI9-DeltaPos", "MI10", "MI10-DeltaPos", "MI11",
                 "MB21", "MB27", "MB29", "MB30", "MB31", "MB32"],
    },
]


def calibrate(raw: float, device_id: str, key: str) -> float | None:
    """Apply linear interpolation calibration if defined, otherwise return raw value."""
    cal = CALIBRATIONS.get((device_id, key))
    if cal is None:
        return None  # no calibration defined for this key
    x0, x1, y0, y1 = cal
    y = y0 + ((y1 - y0) / (x1 - x0)) * (raw - x0)
    return max(y0, min(y1, y))
