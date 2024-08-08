import serial

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Update COM port and baud rate as needed
    ser.write(b'Hello')
    response = ser.read(10)  # Read 10 bytes
    print(response)
except serial.SerialException as e:
    print(f"Serial exception: {e}")
except Exception as e:
    print(f"General exception: {e}")
finally:
    ser.close()
