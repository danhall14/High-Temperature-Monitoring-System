import _thread
from utime import sleep, localtime, time
from machine import Pin, PWM
from Thermocouple_library import Thermocouple_Reading
from RGB1602 import RGB1602
from PID import PID

pwm = PWM(Pin(15))
pwm.freq(1000)

LCD = RGB1602()
temp_sensor = Thermocouple_Reading()
target_temp = 18
pid = PID(kP=1.0, kI=0.1, kD=0.05, target = target_temp)
adc_voltage = temp_sensor.vref

class Thermocouple:
    
    def __init__(self):
        self.temperature = 0
        self.time = 0
        self.read_lock = _thread.allocate_lock()
        
    def read_temp(self):
        with self.read_lock:
            self.temperature = temp_sensor.calibrated_final_temp()[0]
            self.time = time()
        
    def display_temp(self):
        formatted_time = localtime(self.time)
        temp_sensor.displayLCD(self.temperature, formatted_time)
        
    def print_temp(self):
        formatted_time = localtime(self.time)
        print(f"Widget Temperature: {self.temperature}°C, Date: {formatted_time[0]}-{formatted_time[1]}-{formatted_time[2]}, Time: {formatted_time[3]}:{formatted_time[4]}:{formatted_time[5]}")

def temp_worker(temp_monitor):
    while True:
        temp_monitor.read_temp()
        current_temp = temp_monitor.temperature

        # Update PID controller and get new output
        pid_output = pid.update(current_temp)

        # Convert PID output to duty cycle (0-1023 range, assuming 3.3V max)
        duty_cycle = int((pid_output / adc_voltage) * 65536)
        pwm.duty_u16(duty_cycle)
        adc_value = temp_sensor.read_wait()
    
        # Convert ADC value to voltage
        pwm_voltage = (adc_value / 8388607) * adc_voltage  # Assuming a 24-bit ADC (2^23 - 1)
    
        print(f"PID Output:", pid_output,"Duty Cycle:", duty_cycle, "Voltage:", pwm_voltage, "V", "Temperature:", current_temp, "°C")

        sleep(.25)

def user_input_worker():
    while True:
        user_command = input("Enter a command ('read' to read temperature, 'exit' to exit): ").lower()
        if user_command == 'read':
            display_temp = input("Do you want to display the temperature: ").lower()
            if display_temp == "yes":
                if LCD.lcd_connected:
                    temp_sensor.cleardisplayLCD()
                    temp_monitor.display_temp()
                else:
                    if not LCD.lcd_connected:
                        print("LCD not connected. Displaying on console instead.")
                        temp_monitor.print_temp()
            else:
                temp_sensor.cleardisplayLCD()
                temp_monitor.print_temp()
        elif user_command == 'exit':
            if LCD.lcd_connected:
                temp_sensor.cleardisplayLCD()
                temp_sensor.clearRGBdisplayLCD()
                break
            else:
                break
        else:
            print("Invalid command. Try again.")

temp_monitor = Thermocouple()

# Create threads with a more descriptive name
_thread.start_new_thread(temp_worker, (temp_monitor,))
user_input_worker()
