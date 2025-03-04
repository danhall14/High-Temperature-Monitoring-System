from micropython import const
from machine import Pin, SPI  
from time import sleep, sleep_ms
from ads1220 import ADC
import math
from RGB1602 import RGB1602


class Thermocouple_Reading(object):
    """SPI interface for ADS1220 24 bit analog to digital converter."""

    # ADS1220 command constants
    POWER_DOWN = const(0x02)
    RESET = const(0x06)
    START = const(0x08)
    RREG = const(0x20)
    WREG = const(0x40)

    SPI_MASTER_DUMMY = const(0xFF)

    # Configuration register constants
    REG0_ADDRESS = const(0x00)
    REG1_ADDRESS = const(0x01)
    REG2_ADDRESS = const(0x02)
    REG3_ADDRESS = const(0x03)

    # Configuration register mask constants
    BURN_OUT_MASK = const(0x01)
    CONVERSION_MODE_MASK = const(0x04)
    DATA_RATE_MASK = const(0xE0)
    DRDY_MODE_MASK = const(0x02)
    FIR_FILTER_MASK = const(0x30)
    IDAC_CURRENT_MASK = const(0x07)
    IDAC1_ROUTING_MASK = const(0xE0)
    IDAC2_ROUTING_MASK = const(0x1C)
    LOW_SIDE_POWER_SWITCH_MASK = const(0x08)
    OPERATING_MODE_MASK = const(0x18)
    PGA_BYPASS_MASK = const(0x01)
    PGA_GAIN_MASK = const(0X0E)
    MUX_MASK = const(0xF0)
    TEMPERATURE_MODE_MASK = const(0x2)
    VREF_MASK = const(0xC0)

    # Multiplexer constants
    MUX_SE_CH0 = const(0x8)
    MUX_SE_CH1 = const(0x9)
    MUX_SE_CH2 = const(0xA)
    MUX_SE_CH3 = const(0xB)
    CHANNELS = {
        0: MUX_SE_CH0,
        1: MUX_SE_CH1,
        2: MUX_SE_CH2,
        3: MUX_SE_CH3
    }

    def __init__(self):
        """Constructor for ADC.

        Args:
            spi (Class Spi):  SPI interface for ADS1220
            cs (int):  Chip select pin
            drdy (int):  Data ready pin
            reg0 (byte): Configuration Register 0, Default=0:
                         (AINP=AIN0, AINN=AIN1, Gain=1, PGA enabled)
            reg1 (byte): Configuration Register 1, Default=4:
                         (DR=20 SPS, Mode=Normal, Conv mode=continuous,
                         Temperature Sensor disabled, Current Source off)
            reg2 (byte): Configuration Register 2, Default=16:
                         (Vref internal, 50/60Hz rejection, power open,
                         IDAC off)
            reg3 (byte): Configuration Register 3, Default=0:
                         (IDAC1 disabled, IDAC2 disabled, DRDY pin only)
        """

        self.spi = SPI(0, baudrate=10000000,
                       sck=Pin(2), mosi=Pin(3),
                       miso=Pin(4), phase=1)
        self.cs = Pin(5, Pin.OUT)
        self.drdy = Pin(27, Pin.IN, Pin.PULL_UP)
        self.reset()
        sleep_ms(100)
        # Set configuration registers
        self.reg0 = 0
        self.reg1 = 4
        self.reg2 = 16
        self.reg3 = 0
        self.write_register(self.REG0_ADDRESS, self.reg0)
        self.write_register(self.REG1_ADDRESS, self.reg1)
        self.write_register(self.REG2_ADDRESS, self.reg2)
        self.write_register(self.REG3_ADDRESS, self.reg3)
        self.adc = ADC(self.spi, self.cs, self.drdy)
        self.offset_voltage = 5.8208391663e-06
        self.vref = 3.3171
        self.gain = 2
        self.ADC_cal_m_param = 1.3184495221108328
        self.ADC_cal_b_param = 7.566447582489127
        self.display = RGB1602()

        
        # Inverse coefficients for type K
        self.coeffs_minus_200_to_0_inverse = [0.0000000E+00, 2.5173462E+01,
                                              -1.1662878E+00, -1.0833638E+00,
                                              -8.9773540E-01, -3.7342377E-01,
                                              -8.6632643E-02, -1.0450598E-02,
                                              -5.1920577E-04, 0.0000000E+00]
        
        self.coeffs_0_to_500_inverse = [0.000000E+00, 2.508355E+01,
                                        7.860106E-02, -2.503131E-01,
                                        8.315270E-02, -1.228034E-02,
                                        9.804036E-04, -4.413030E-05,
                                        1.057734E-06, -1.052755E-08]

        self.coeffs_500_to_1372_direct = [-1.318058E+02, 4.830222E+01,
                                          -1.646031E+00, 5.464731E-02,
                                          -9.650715E-04, 8.802193E-06,
                                          -3.110810E-08, 0.000000E+00,
                                          0.000000E+00, 0.000000E+00]
        
        # Direct coefficients for type K
        self.coeffs_0_to_1372_direct = [-0.176004136860E-01, 0.389212049750E-01,
                                        0.185587700320E-04, -0.994575928740E-07,
                                       0.318409457190E-09, -0.560728448890E-12,
                                       0.560750590590E-15, -0.320207200030E-18,
                                       0.971511471520E-22,-0.121047212750E-25]

        self.exp_coeffs_0_to_1372_direct = [0.118597600000E+00,
                                           -0.118343200000E-03,
                                           0.126968600000E+03]
        
    def burn_out(self, enable=False):
        """Set Burn-out current sources.

        Args:
            enable (bool): True=Current sources on, False (Default)=Off
        Notes:
            Controls the 10-μA, burn-out current sources.
            The burn-out current sources can be used to detect sensor faults
            such as wirebreaks and shorted sensors.
        """
        if enable:
            self.reg1 |= self.BURN_OUT_MASK
        else:
            self.reg1 &= ~(self.BURN_OUT_MASK)
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def conversion_continuous(self):
        """Set continuous conersion mode."""
        self.reg1 |= 1 << 2
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def conversion_single_shot(self):
        """Set single shot conersion mode."""
        self.reg1 &= ~(1 << 2)
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def data_rate(self, rate):
        """Set data rate.

        Args:
            rate (int): 0=20SPS Normal, 5SPS Duty, 40SPS Turbo
                        1=45SPS Normal, 11.25SPS Duty, 90SPS Turbo
                        2=90SPS Normal, 22.5SPS Duty, 180SPS Turbo
                        3=175SPS Normal, 44SPS Duty, 350SPS Turbo
                        4=330SPS Normal, 82.5SPS Duty, 660SPS Turbo
                        5=600SPS Normal, 150SPS Duty, 1200SPS Turbo
                        6=1000SPS Normal, 250SPS Duty, 2000SPS Turbo
        Notes:
            Controls data rate setting depending on selected operating mode.
            See datasheet table 18.
        """
        if not 0 <= rate <= 6:
            raise ValueError("Invalid data rate value.")
        self.reg1 &= ~self.DATA_RATE_MASK
        self.reg1 |= (rate << 5)
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def drdy_mode(self, drdy=0):
        """Set Data Ready mode

        Args:
            psw (int): 0=Only dedicated DRDY pin indicates data ready (Default)
                       1=DOUT/DRDY & DRDY pins both indicate data ready
        Notes:
            Controls behavior of DOUT/DRDY pin when new data ready.
        """
        if not 0 <= drdy <= 1:
            raise ValueError("Invalid Data Ready mode value.")

        self.reg3 = (self.reg3 & ~self.DRDY_MODE_MASK) | (drdy << 1)
        self.write_register(self.REG3_ADDRESS, self.reg3)

    def fir_filter(self, fir=0):
        """Set FIR filter.

        Args:
            fir (int): 0=No 50-Hz or 60-Hz rejection (default)
                       1=Simultaneous 50-Hz & 60-Hz rejection
                       2=50-Hz rejection only
                       3=60-Hz rejection only
        Notes:
            Only use these bits together with the 20-SPS setting in normal mode
            and the 5-SPS setting in duty-cycle mode.
            Set to 00 for all other data rates.
        """
        if not 0 <= fir <= 3:
            raise ValueError("Invalid FIR filter value.")

        self.reg2 = (self.reg2 & ~self.FIR_FILTER_MASK) | (fir << 4)
        self.write_register(self.REG2_ADDRESS, self.reg2)

    def get_config(self):
        """Retrieve configuration registers."""
        cr0 = int.from_bytes(self.read_register(self.REG0_ADDRESS), 'little')
        cr1 = int.from_bytes(self.read_register(self.REG1_ADDRESS), 'little')
        cr2 = int.from_bytes(self.read_register(self.REG2_ADDRESS), 'little')
        cr3 = int.from_bytes(self.read_register(self.REG3_ADDRESS), 'little')
        return [cr0, cr1, cr2, cr3]

    def get_config_dict(self):
        """Retrieve configuration registers in a formatted dict."""
        reg0, reg1, reg2, reg3 = self.get_config()

        # Register 0
        pga_bypass = reg0 & self.PGA_BYPASS_MASK
        gain = (reg0 & self.PGA_GAIN_MASK) >> 1
        mux = (reg0 & self.MUX_MASK) >> 4

        # Register 1
        burn_out_current_sources = reg1 & self.BURN_OUT_MASK
        temperature_sensor_mode = (reg1 & self.TEMPERATURE_MODE_MASK) >> 1
        conversion_mode = (reg1 & self.CONVERSION_MODE_MASK) >> 2
        operating_mode = (reg1 & self.OPERATING_MODE_MASK) >> 3
        data_rate = (reg1 & self.DATA_RATE_MASK) >> 5

        # Register 2
        idac_current = reg2 & self.IDAC_CURRENT_MASK
        low_side_power_switch = (reg2 & self.LOW_SIDE_POWER_SWITCH_MASK) >> 3
        fir_filter = (reg2 & self.FIR_FILTER_MASK) >> 4
        vref = (reg2 & self.VREF_MASK) >> 6

        # Register 3
        data_ready_mode = (reg3 & self.DRDY_MODE_MASK) >> 1
        idac2_routing = (reg3 & self.IDAC2_ROUTING_MASK) >> 2
        idac1_routing = (reg3 & self.IDAC1_ROUTING_MASK) >> 5

        return {
            "Burn Out Current Source": burn_out_current_sources,
            "Conversion Mode": conversion_mode,
            "Data Rate": data_rate,
            "Data Ready Mode": data_ready_mode,
            "FIR Filter": fir_filter,
            "Gain": gain,
            "IDAC Current": idac_current,
            "IDAC1 Routing": idac1_routing,
            "IDAC2 Routing": idac2_routing,
            "Low Side Power Switch": low_side_power_switch,
            "Multiplexer": mux,
            "Operating Mode": operating_mode,
            "PGA Bypass": pga_bypass,
            "Temperature Sensor Mode": temperature_sensor_mode,
            "Voltage Reference": vref
        }

    def idac1_routing(self, idac1=0):
        """Set IDAC1 routing configuration

        Args:
            psw (int): 0=IDAC1 disabled (Default)
                       1=IDAC1 connected to AIN0/REFP1
                       2=IDAC1 connected to AIN1
                       3=IDAC1 connected to AIN2
                       4=IDAC1 connected to AIN3/REFN1
                       5=IDAC1 connected ot REFP0
                       6=IDAC1 connected to REFN0
        Notes:
            These bits select the channel where IDAC1 is routed.
        """
        if not 0 <= idac1 <= 6:
            raise ValueError("Invalid IDAC1 routing value.")

        self.reg3 = (self.reg3 & ~self.IDAC1_ROUTING_MASK) | (idac1 << 5)
        self.write_register(self.REG3_ADDRESS, self.reg3)

    def idac2_routing(self, idac2=0):
        """Set IDAC2 routing configuration

        Args:
            psw (int): 0=IDAC2 disabled (Default)
                       1=IDAC2 connected to AIN0/REFP1
                       2=IDAC2 connected to AIN1
                       3=IDAC2 connected to AIN2
                       4=IDAC2 connected to AIN3/REFN1
                       5=IDAC2 connected ot REFP0
                       6=IDAC2 connected to REFN0
        Notes:
            These bits select the channel where IDAC2 is routed.
        """
        if not 0 <= idac2 <= 6:
            raise ValueError("Invalid IDAC2 routing value.")

        self.reg3 = (self.reg3 & ~self.IDAC2_ROUTING_MASK) | (idac2 << 2)
        self.write_register(self.REG3_ADDRESS, self.reg3)

    def idac_current(self, idac=0):
        """Sets IDAC current settings.

        Args:
            psw (int): 0=Off (Default)
                       1=10uA
                       2=50uA
                       3=100uA
                       4=250uA
                       5=500uuA
                       6=1000uA
                       7=1500uA
        Notes:
            These bits set the current for both IDAC1 & IDAC2
            excitation current sources.
        """
        if not 0 <= idac <= 7:
            raise ValueError("Invalid IDAC value.")

        self.reg2 = (self.reg2 & ~self.IDAC_CURRENT_MASK) | idac
        self.write_register(self.REG2_ADDRESS, self.reg2)

    def lowside_power_switch(self, psw=0):
        """Sets low-side power switch configuration

        Args:
            psw (int): 0=Switch is always open (default)
                       1=Switch automatically closes with START/SYNC command
                         and opens with POWERDOWN command
        Notes:
            This bit configures the behavior of the low-side switch connected
            between AIN3/REFN1 and AVSS.
        """
        if not 0 <= psw <= 1:
            raise ValueError("Invalid low-side power switch value.")

        self.reg2 = (self.reg2 & ~self.LOW_SIDE_POWER_SWITCH_MASK) | (psw << 3)
        self.write_register(self.REG2_ADDRESS, self.reg2)

    def mux_config(self, mux):
        """Set input multiplexer configuration.
        Args:
            mux(byte): 0 : AINP = AIN0, AINN = AIN1 (default)
                       1 : AINP = AIN0, AINN = AIN2
                       2 : AINP = AIN0, AINN = AIN3
                       3 : AINP = AIN1, AINN = AIN2
                       4 : AINP = AIN1, AINN = AIN3
                       5 : AINP = AIN2, AINN = AIN3
                       6 : AINP = AIN1, AINN = AIN0
                       7 : AINP = AIN3, AINN = AIN2
                       8 : AINP = AIN0, AINN = AVSS
                       9 : AINP = AIN1, AINN = AVSS
                       10 : AINP = AIN2, AINN = AVSS
                       11 : AINP = AIN3, AINN = AVSS
                       12 : (V(REFPx) – V(REFNx)) / 4 monitor (PGA bypassed)
                       13 : (AVDD – AVSS) / 4 monitor (PGA bypassed)
                       14 : AINP and AINN shorted to (AVDD + AVSS) / 2
        Note:
            For single ended inputs just use select_channel method.
            See datasheet table 16 for more information.
        """
        if not 0 <= mux <= 14:
            raise ValueError("Invalid mux value.")
        self.reg0 &= ~self.MUX_MASK
        self.reg0 |= (mux << 4)
        self.write_register(self.REG0_ADDRESS, self.reg0)

    def operating_mode(self, mode=0):
        """Sets the operating mode.
        Args:
            mode(int): 0=Normal mode - 256 kHz modulator clock (Default)
                       1=Duty-cycle mode - Internal duty cycle of 1:4
                       2=Turbo mode - 512 kHz modulator clock
        """
        if not 0 <= mode <= 2:
            raise ValueError("Invalid mode value.")

        self.reg1 = (self.reg1 & ~self.OPERATING_MODE_MASK) | (mode << 3)
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def pga_gain(self, gain=0):
        """Set programmable gain amplifier gain.

        Args:
            gain (int): 0=Gain 1 (default)
                        1=Gain 2
                        2=Gain 4
                        3=Gain 8
                        4=Gain 16
                        5=Gain 32
                        6=Gain 64
                        7=Gain 128
        Notes:
            Gains 1, 2, and 4 can be used without the PGA.
            In this case, gain is obtained by a switched-capacitor structure.
            For mux settings where AINN = AVSS, the PGA must be disabled
            and only gains 1, 2, and 4 can be used.
        """
        if not 0 <= gain <= 7:
            raise ValueError("Invalid gain value.")
        self.reg0 &= ~self.PGA_GAIN_MASK
        self.reg0 |= (gain << 1)
        self.write_register(self.REG0_ADDRESS, self.reg0)

    def pga_on(self):
        """Turn on programmable gain amplifier."""
        self.reg0 &= ~self.PGA_BYPASS_MASK
        self.write_register(self.REG0_ADDRESS, self.reg0)

    def pga_off(self):
        """Turn off programmable gain amplifier."""
        self.reg0 |= self.PGA_BYPASS_MASK
        self.write_register(self.REG0_ADDRESS, self.reg0)

    def power_down(self):
        """Activate power-down mode.

        Notes: This command shuts down all internal analog components,
               opens the low-side switch, turns off both IDACs, but holds
               all register values.  Any current conversion will complete.
               START/SYNC returns all analog components to previous states."""
        self.write_command(self.POWER_DOWN)

    def read_no_wait(self):
        """Reads currently selected ADC channel without waiting for data ready.

        Note: Reads a single conversion (assuming continuous mode)"""
        data = self.read_spi(3)
        if data[0] & 0b10000000:
            # Negative voltage
            return 0 - (~(int.from_bytes(data, 'big') - 1) & 0xFFFFFF)
        else:
            # Positive voltage
            return int.from_bytes(data, 'big')

    def read_temperature(self):
        """Returns temperature in Celsius.

        Note: Assumes temperature mode enabled"""
        data = self.read_spi(2)
        bits = data[0]  # Convert 2 bytes to int
        bits = (bits << 8) | data[1]
        bits = bits >> 2  # Result is 14 bits
        # Check for negative temperatures indicated by MSB
        if data[0] & 0b10000000:
            # Negative temperature (see datasheet 8.3.13.1.2)
            return -.03125 * (~(bits - 1) & 0b11111111111111)
        else:
            # Positive temperature
            return bits * .03125

    def read_register(self, address, bytes=1):
        """Read SPI register.

        Args:
            address (byte): Register address.
            bytes (byte): Number of bytes to read (default= 1)
        """
        self.cs(0)
        sleep_ms(2)
        opcode = (address << 2) | self.RREG
        self.spi.write(bytearray([opcode]))
        data = self.spi.read(bytes, self.SPI_MASTER_DUMMY)
        sleep_ms(2)
        self.cs(1)
        return data

    def read_spi(self, bytes=1):
        """Read SPI bus (assumes prior write to return data).

        Args:
            bytes (byte): Number of bytes to read (default= 1)
        """
        self.cs(0)
        sleep_ms(2)
        data = self.spi.read(bytes, self.SPI_MASTER_DUMMY)
        sleep_ms(2)
        self.cs(1)
        return data

    def read_wait_temperature(self):
        """Returns temperature in Celsius., waits for the data ready pin.

        Note: This will work on all 4 modes."""
        while self.drdy.value() != 0:  # Wait for data ready pin to go low
            pass
        data = self.read_spi(2)
        bits = data[0]  # Convert 2 bytes to int
        bits = (bits << 8) | data[1]
        bits = bits >> 2  # Result is 14 bits
        # Check for negative temperatures indicated by MSB
        if data[0] & 0b10000000:
            # Negative temperature (see datasheet 8.3.13.1.2)
            return -.03125 * (~(bits - 1) & 0b11111111111111)
        else:
            # Positive temperature
            return bits * .03125
        
    def read_wait(self):
        """Reads currently selected ADC channel, waits for the data ready pin.

        Note: This will work on all 4 modes."""
        while self.drdy.value() != 0:  # Wait for data ready pin to go low
            pass
        data = self.read_spi(3)
        if data[0] & 0b10000000:
            # Negative voltage
            return 0 - (~(int.from_bytes(data, 'big') - 1) & 0xFFFFFF)
        else:
            # Positive voltage
            return int.from_bytes(data, 'big')

    def read_wait_negative(self, timeout=1000):
        """Monitor currently selected ADC channel until voltage negative.
           Args:
                timeout(int): Number of reads before timeout (default=1000)
            Returns:
                True if negative acquired otherwise false if timeout
           """
        counter = 0
        while counter <= timeout:
            while self.drdy.value() != 0:  # Wait for data ready pin to go low
                pass
            data = self.read_spi(3)
            if data[0] & 0b10000000:
                # Negative voltage
                return True

            counter += 1
        return False

    def read_wait_target(self, target, timeout=1000, greater=True,
                         vref=2.048, resolution=23):
        """Monitor currently selected ADC channel for target or timeout.
           Args:
                target(float): Target voltage
                timeout(int): Number of reads before timeout (default=1000)
                greater(bool): True (Default)=target threshold greater or equal
                               False=target threshold less or equal
                vref (float): Voltage reference (default internal 2.048 V)
                resolution: Bit resolution (default 23 bit)
            Returns:
                True if target reached otherwise false if timeout
           """
        raw_target = target / (vref / (2 ** resolution))
        counter = 0
        while True:
            while self.drdy.value() != 0:  # Wait for data ready pin to go low
                pass
            data = self.read_spi(3)
            if data[0] & 0b10000000:
                # Negative voltage
                raw = 0 - (~(int.from_bytes(data, 'big') - 1) & 0xFFFFFF)
            else:
                # Positive voltage
                raw = int.from_bytes(data, 'big')
            if greater:
                if raw >= raw_target:
                    return True
            else:
                if raw <= raw_target:
                    return True
            counter += 1
            if counter >= timeout:
                return False

    def reset(self):
        """Reset ADS1220."""
        self.write_command(self.RESET)

    def select_channel(self, channel):
        """Select singled ended mux channel.

        Args:
            channel (int): 0-3
        Notes:
            For differential or combination signals use mux_config method.
        """
        if not 0 <= channel <= 3:
            raise ValueError("Invalid channel value.")
        self.mux_config(self.CHANNELS[channel])

    def start_conversion(self):
        """Start conversion."""
        self.write_command(self.START)

    def temperature_mode(self, enable=True):
        """Set continuous conersion mode.

        Args:
            enable (bool): True(default)=enable temperature mode, false=disable
        """
        if enable:
            self.reg1 |= 1 << 1
        else:
            self.reg1 &= ~(1 << 1)
        self.write_register(self.REG1_ADDRESS, self.reg1)

    def vref(self, vref):
        """Set voltage reference used for conversion.

        Args:
            vref (int): 0=Internal 2.048V reference selected (default)
                        1=External reference using REFP0 & REFN0
                        2=External reference using AIN0/REFP1 & AIN3/REFN1
                        3=Analog supply (AVDD, AVSS) used as reference
        """
        if not 0 <= vref <= 3:
            raise ValueError("Invalid voltage reference value.")

        self.reg2 = (self.reg2 & ~self.VREF_MASK) | (vref << 6)
        self.write_register(self.REG2_ADDRESS, self.reg2)

    def write_command(self, command):
        """Write SPI command.

        Args:
            command (byte): Command byte.
        """
        self.cs(0)
        sleep_ms(2)
        self.spi.write(bytearray([command]))
        sleep_ms(2)
        self.cs(1)

    def write_register(self, address, value):
        """Write SPI register.

        Args:
            address (byte): Register address.
            value (byte): Value to set register.
        """
        self.cs(0)
        sleep_ms(2)
        opcode = (address << 2) | self.WREG
        self.spi.write(bytearray([opcode, value]))
        sleep_ms(2)
        self.cs(1)
   
    def voltage_to_temp(self, voltage):
        if voltage < 0:
            coeffs = self.coeffs_minus_200_to_0_inverse
        elif voltage < 20.644:
            coeffs = self.coeffs_0_to_500_inverse
        else:
            coeffs = self.coeffs_500_to_1372_direct

        return sum(coeff * ((voltage * 1000) ** n) for n, coeff in enumerate(coeffs))
        
    def t_to_v_exp_part(self, temp):
        return self.exp_coeffs_0_to_1372_direct[0] * math.exp(self.exp_coeffs_0_to_1372_direct[1] * (temp - self.exp_coeffs_0_to_1372_direct[2])**2)
    
    def temp_to_voltage(self, temp):
        return 0.001 * (sum([(coeff * temp ** n)
                            for n, coeff in enumerate(self.coeffs_0_to_1372_direct)]) + self.t_to_v_exp_part(temp))

    def cj_temperature(self):
        self.adc.conversion_continuous()
        self.adc.start_conversion()
        self.adc.temperature_mode(enable=True)
        sleep(0.1)
        cj_temp_non_cal = self.adc.read_temperature()
        self.adc.temperature_mode(enable=False)
        return cj_temp_non_cal
    
    def calibrated_cj_temp(self, cj_temp_non_cal):

        return (self.ADC_cal_m_param * cj_temp_non_cal) + self.ADC_cal_b_param
            
    def voltage_reading(self):
        
        res = (2**23 - 1)
        self.adc.conversion_continuous()
        self.adc.mux_config(0)
        sleep(0.1)
        
        self.adc.vref(1) # If external 9V battery used as input of 3.3V to REFN0 and REFP0
       
        self.adc.start_conversion()
        self.adc.operating_mode(1)
        self.adc.data_rate(0)
        self.adc.pga_gain(1)
        data = self.adc.read_wait()
        voltage = data * self.vref / (res * self.gain)
        return voltage
    
    def interpolate_temperature(self, measured_voltage):
        
        if measured_voltage < 0:
            file_path = 'Thermocouple_true_calibration_values_-270to0.txt'
        elif 0 <= measured_voltage <= 20.644:
            file_path = 'Thermocouple_true_calibration_values_0to500.txt'
        elif 20.644 < measured_voltage <= 54.886:
            file_path = 'Thermocouple_true_calibration_values_500to1372.txt'
        else:
            return "Error: Measured Voltage out of calibration range"

        with open(file_path, 'r') as file:
            lines = file.readlines()
            calibration_temperature = []
            calibration_voltage = []

            for line in lines:
                temp, voltage = map(float, line.split())
                calibration_temperature.append(temp)
                calibration_voltage.append(voltage)

            for i in range(len(calibration_voltage) - 1):
                if calibration_voltage[i] <= measured_voltage <= calibration_voltage[i + 1]:
                    temp = calibration_temperature[i] + (measured_voltage - calibration_voltage[i]) * (calibration_temperature[i + 1] - calibration_temperature[i]) / (calibration_voltage[i + 1] - calibration_voltage[i])
                    return temp

        return "Error: Voltage out of calibration range"


    def calc_temp(self):
        
        cj_temp_non_cal = self.cj_temperature()
        cj_temp = self.calibrated_cj_temp(cj_temp_non_cal)
        voltage = self.voltage_reading()
        cj_voltage = self.temp_to_voltage(cj_temp)
        cj_voltage_calibrated = (cj_voltage - self.offset_voltage)
        thermocouple_temp = self.voltage_to_temp(voltage)
        final_temperature = self.voltage_to_temp(voltage + cj_voltage_calibrated)
            
        return cj_temp, cj_voltage_calibrated, voltage, thermocouple_temp, final_temperature

    def calibrated_final_temp(self):
        
        cj_temp_non_cal = self.cj_temperature()
        cj_temp = self.calibrated_cj_temp(cj_temp_non_cal)
        thermocouple_v = self.voltage_reading()
        thermocouple_mV = thermocouple_v * 1000
        cj_voltage = self.temp_to_voltage(cj_temp)
        cj_voltage_calibrated = (cj_voltage - self.offset_voltage)
        cj_calibrated_temp = self.voltage_to_temp(cj_voltage_calibrated)
        calibrated_thermocouple_temp = self.interpolate_temperature(thermocouple_mV)
        Temperature = calibrated_thermocouple_temp + cj_calibrated_temp

        return Temperature, calibrated_thermocouple_temp
    
    def displayLCD(self, Temperature, Time):
        self.display.clear()
        self.display.printout("Temp: ")
        self.display.write(f"{Temperature:.2f}")
        self.display.character_write(0b11011111)
        self.display.printout("C")
        self.display.setCursor(0, 1)
        self.display.printout("Time: ")
        self.display.write(f"{Time[3]}:{Time[4]}:{Time[5]}")

    def cleardisplayLCD(self):
        self.display.clear()
        
    def clearRGBdisplayLCD(self):
        self.display.setRGB(0, 0, 0)





