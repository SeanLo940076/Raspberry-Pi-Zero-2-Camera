from pprint import *
from picamera2 import Picamera2

picam2 = Picamera2()
pprint(picam2.sensor_modes)
