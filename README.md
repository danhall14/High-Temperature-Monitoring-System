# High-Temperature Monitoring System

## Overview

The High-Temperature Monitoring System is a cost-effective solution designed to monitor and control high temperatures using a microcontroller-based setup. This project leverages thermocouples, an ADC, and a PID control loop to provide accurate temperature readings and maintain desired temperature levels.

## Features

- **Microcontroller-Based**: Utilises the RP2040 microcontroller for processing temperature data.
- **Thermocouple Sensors**: Employs K-type thermocouples for high-temperature measurement.
- **Analog-to-Digital Conversion**: Uses the ADS1220 ADC for precise voltage-to-temperature conversion.
- **PID Control**: Integrates a PID loop for maintaining stable temperature conditions.
- **Real-Time Display**: Features an LCD for displaying temperature readings and system status.

## Technical Specifications
- Temperature Range: -200°C to 1350°C
- Measurement Accuracy: ±0.5°C
- Sample Rate: 10 Hz
- Resolution: 0.1°C
- Response Time: <1 second
- Power Supply: 5V DC

## Thermocouple Calibration
The system uses the NIST ITS-90 thermocouple database for K-type thermocouples. This ensures accurate temperature conversion from voltage readings to temperature values.

### Lookup Table Specifications
- Type: K-type (Chromel–Alumel)
- Range: -200°C to 1350°C
- Resolution: 0.1°C
- Reference Junction: 0°C (achieved through CJC)
- Voltage Range: -5.891 to 54.886 mV

### Implementation
The lookup table is implemented as a series of polynomial coefficients for different temperature ranges:
- -200°C to 0°C
- 0°C to 500°C
- 500°C to 1350°C
  
## Hardware Requirements
- RP2040 Microcontroller (Raspberry Pi Pico)
- ADS1220 24-bit ADC
- K-type thermocouple
- LCD1602 Display Module
- Power Supply Unit (5V)
- Supporting Components:
  - Resistors x2 (330Ω)
  - Capacitors (100 µF)
  - Connection wires
  - Breadboard

## Software Requirements
- Python 3.x
- MicroPython
- Required Libraries:
  - `machine`
  - `utime`
  - `_thread`


### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/danhall14/High-Temperature-Monitoring-System.git
   cd High-Temperature-Monitoring-System
