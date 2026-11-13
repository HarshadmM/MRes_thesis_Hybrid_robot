# Hybrid Eversion–Continuum Robot: Control Software

This repository contains the control software developed for the hybrid eversion–continuum robotic platform as part of an MRes research project at Imperial College London.

## Repository structure

```text
MRes_thesis_Hybrid_robot/
├── README.md
├── xbox_control.py
└── Arduino_firmware.ino
```

The repository contains two main software components:

- **Python controller (`xbox_control.py`):** Xbox-controller input, serial communication, motor commands, CSV logging and live visualisation.
- **Arduino firmware (`Arduino_firmware.ino`):** Stepper-motor actuation, servo control and serial command handling.

## System overview

The Python application reads inputs from an Xbox-compatible controller and transmits movement and speed commands to the Arduino over a serial connection. The Arduino firmware interprets these commands and controls the stepper-motor drivers. It also includes a servo-control routine.

The Python application additionally provides CSV logging and live visualisation infrastructure for incoming telemetry.

## Requirements

### Python

- Python 3
- `pygame`
- `pyserial`
- `matplotlib`

Install dependencies using:

```bash
pip install pygame pyserial matplotlib
```

### Arduino

- Arduino IDE
- `Servo.h` library
- Compatible Arduino board and stepper-motor drivers

The firmware uses RAMPS-style stepper-driver pin assignments.

## Configuration

Before running the software, check:

- Serial port (`COM8` in the supplied Python script).
- Baud rate (`115200`).
- Xbox controller axis and button mappings.
- Arduino stepper-driver pin assignments.
- Motor directions and physical wiring.

Adapt these settings to the computer, controller, board and wiring in use.

## Control interface

| Controller input | Function |
|---|---|
| Left stick Y-axis | Motor X movement |
| Right stick X-axis | Motor Y movement |
| Right stick button | Motor Z activation |
| Right trigger | Motor Y speed scaling |
| LB / RB | Change speed preset |
| A | Start CSV recording |
| B | Stop CSV recording |
| Start | Exit application |

The Arduino firmware receives serial commands for motor movement, speed adjustment and servo operation.

## Data logging and visualisation

The Python application includes functionality for:

- Periodic telemetry requests to the Arduino.
- Recording received values to timestamped CSV files.
- Displaying selected telemetry channels in live plots.

The supplied firmware currently returns placeholder zero-valued telemetry. Consequently, the plotting and logging infrastructure is implemented, but meaningful sensor measurements require corresponding sensor acquisition and transmission in the firmware.

## Known implementation limitations

The following limitations apply to the supplied software version:

- The Arduino firmware returns placeholder zero-valued telemetry in response to `Q`.
- The firmware acknowledges `T` and `Z` without performing any operation. These are inactive commands; no load cell was used in the project, and no load-cell taring or position zeroing was implemented.
- The Python speed presets include `100` microseconds, while the firmware accepts values between `150` and `5000` microseconds. The `100` microsecond preset is therefore rejected.
- The Python interface includes a servo mapping in its controller description, but the supplied Python script does not currently issue the servo command. The Arduino firmware contains the corresponding servo routine.
- The servo routine uses a blocking delay, temporarily pausing the Arduino main loop.

These limitations describe the supplied code version and should be updated if the software changes.

## Safety

This software was developed for a research prototype and is not a safety-certified robotic controller.

Before operation, verify motor directions, mechanical travel limits, driver current settings, power-supply ratings, emergency stopping arrangements and mechanical clearances. Initial testing should be performed at low speed and with the mechanism unloaded.

## Reproducibility

The source code is provided for reference and to support reproducibility of the motorised control implementation described in the associated MRes research project.
