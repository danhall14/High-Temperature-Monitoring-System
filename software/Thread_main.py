import _thread
from utime import sleep, localtime, time
from Thermocouple_library import Thermocouple_Reading
from RGB1602 import RGB1602

LCD = RGB1602()
temp_sensor = Thermocouple_Reading()

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
        print(f"Temperature: {self.temperature}°C, Date: {formatted_time[0]}-{formatted_time[1]}-{formatted_time[2]}, Time: {formatted_time[3]}:{formatted_time[4]}:{formatted_time[5]}")

def temp_worker(temp_monitor):
    while True:
        temp_monitor.read_temp()
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