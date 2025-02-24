import utime
import math

class PID:
    def __init__(self, kP=0.0, kI=0.0, kD=0.0, target=0.0):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.target = target
        self.eps_list = []
        self.lastError = 0.0
        self.lastTime= utime.time()

    def update(self, current_temp):
        now = utime.time()     

        # Calculate the current error
        epsilon = self.target - current_temp
        
        # Append the error to the list
        self.eps_list.append(epsilon)
        error_sum = sum(self.eps_list)
        # Ensure the list doesn't keep growing
        if len(self.eps_list) > 10:
            self.eps_list.pop(0) # removes first value when eps_list is bigger than 10
        
        dt = now - self.lastTime
        
        de = 0 
        for new, last in zip(self.eps_list[1:],self.eps_list[:-1]):
            de = new - last 

        self.correctionProportional = self.kP * epsilon
        self.errorIntegration = error_sum
        self.correctionIntegral = self.kI * error_sum
        self.correctionDerivative = self.kD * (de / dt) if dt > 0 else 0
        
        self.lastTime = now
        self.lastError = epsilon
        
        # Calculate total correction (output)
        output = self.correctionProportional + self.correctionIntegral + self.correctionDerivative

        # Ensure the output is within the voltage range (0 to 3.3V)
        return min(3.3171, max(0, output))

