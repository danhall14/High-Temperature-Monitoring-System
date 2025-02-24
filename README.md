# High-Temperature Monitoring System

## Overview

The High-Temperature Monitoring System is a cost-effective solution designed to monitor and control high temperatures using a microcontroller-based setup. This project leverages thermocouples, an ADC, and a PID control loop to provide accurate temperature readings and maintain desired temperature levels.

## Features

- **Microcontroller-Based**: Utilises the RP2040 microcontroller for processing temperature data.
- **Thermocouple Sensors**: Employs K-type thermocouples for high-temperature measurement.
- **Analog-to-Digital Conversion**: Uses the ADS1220 ADC for precise voltage-to-temperature conversion.
- **PID Control**: Integrates a PID loop for maintaining stable temperature conditions.
- **Real-Time Display**: Features an LCD for displaying temperature readings and system status.

## Installation

### Prerequisites

- Python 3.x
- MicroPython
- Required Python libraries: `machine`, `utime`, `_thread`

### Hardware Requirements

- RP2040 microcontroller (e.g., Raspberry Pi Pico)
- ADS1220 ADC
- K-type thermocouple
- LCD1602 display
- Additional components: resistors, capacitors, power supply

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/danhall14/High-Temperature-Monitoring-System.git
   cd High-Temperature-Monitoring-System
