import serial
import json
from serial.tools import list_ports
import time

ser = serial.Serial(list_ports.comports()[0].device, 
                    16_000_000
                    )  # Open the serial port with the correct port name and baud rate

print('connected to arduino, waiting for data')

last_err = ""

_t = 0
looptime = time.time()
while True:
    # Read a line of text from the serial port and remove the newline character
    line = ser.readline().decode('utf-8').rstrip()

    # Parse the JSON object into a Python dictionary
    try:
        data = json.loads(line)
        dt = (data['us'] - _t) / 1e6
        _t = data['us'] 
        # Print the values of the three parameters
        if (time.time() - looptime) >= 1:
            print(data, f"dt: {dt:.6f} sec., {1/dt:.1f} Hz")
            looptime = time.time()


    except:
        if line != last_err:
            print(line)
            last_err = line

