import py_qmc5883l
import time

sensor = py_qmc5883l.QMC5883L()
sensor.declination = 2.4
sensor.calibration = [[1.002512314340853, -0.01399115733068099, 286.0013506188195], [-0.013991157330680999, 1.0779171938275072, 3518.6421152032353], [0.0, 0.0, 1.0]]

running = True
try:
    while running:
        
        m = sensor.get_magnet()
        print(sensor.get_bearing())
        sensor.mode_standby
        time.sleep(0.5)
except KeyboardInterrupt:
    running = False
    


