# Hybrid Eversion–Continuum Robot: Control Software

This repository contains the software developed for human-operated control of the hybrid eversion–continuum robotic platform as part of an MRes research project at Imperial College London.

## Repository structure

```text
hybrid-eversion-continuum-robot/
├── README.md
├── python_controller/
│   ├── README.md
│   └── xbox_control.py
└── arduino_firmware/
    ├── README.md
    └── robot_control.ino
```

## System overview

The control system consists of a Python-based operator interface and Arduino firmware communicating over a serial connection.

The Python application reads inputs from an Xbox-compatible controller and transmits movement and speed commands to the Arduino. The firmware interprets these commands and controls the stepper-motor drivers. It also includes a servo-control routine.

The Python application additionally provides CSV logging and live visualisation infrastructure for incoming telemetry.

## Requirements

### Python

- Python 3
- `pygame`
- `pyserial`
- `matplotlib`

Install the dependencies using:

```bash
pip install pygame pyserial matplotlib
```

### Arduino

- Arduino IDE
- `Servo.h` library
- Compatible Arduino board and stepper-motor drivers

The firmware uses RAMPS-style stepper-driver pin assignments.

## Configuration

Before running the software, check the following:

- Serial port: `COM8` in the supplied Python script.
- Baud rate: `115200`.
- Xbox controller axis and button mappings.
- Arduino stepper-driver pin assignments.
- Motor directions and physical wiring.

These settings may need to be adapted to the hardware and computer being used.

## Control interface

The Python application supports the following controller inputs:

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

The Arduino firmware accepts serial commands for motor movement, speed adjustment and servo operation.

## Data logging and visualisation

The Python application includes functionality for:

- Requesting telemetry from the Arduino at regular intervals.
- Recording received values to timestamped CSV files.
- Displaying selected telemetry channels in live plots.

The supplied firmware currently returns placeholder zero-valued telemetry. Consequently, the plotting and logging infrastructure is implemented, but meaningful sensor measurements require corresponding sensor acquisition and transmission in the firmware.

## Known implementation limitations

The following limitations apply to the supplied software version:

- The Arduino firmware returns placeholder zero-valued telemetry in response to `Q`. No meaningful sensor measurements are available through this implementation.
- The firmware acknowledges `T` and `Z` without performing any operation. These are inactive commands; no load cell was used in the project, and no load-cell taring or position zeroing was implemented.
- The Python speed presets include `100` microseconds, while the firmware accepts values between `150` and `5000` microseconds. The `100` microsecond preset is therefore rejected.
- The Python interface includes a servo mapping in its controller description, but the supplied Python script does not currently issue the servo command. The Arduino firmware contains the corresponding servo routine.
- The servo routine uses a blocking delay, temporarily pausing the Arduino main loop.

These limitations describe the supplied code version and should be updated if the software is subsequently modified.

## Safety

This software was developed for a research prototype and is not a safety-certified robotic controller.

Before operation, verify motor directions, mechanical travel limits, driver current settings, power-supply ratings, emergency stopping arrangements and mechanical clearances. Initial testing should be performed at low speed and with the mechanism unloaded.

## Reproducibility

The source code is provided for reference and to support reproducibility of the motorised control implementation described in the associated MRes research project.
