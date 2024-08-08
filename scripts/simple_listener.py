import serial

def read_from_serial(port='/dev/ttyUSB0', baud_rate=9600):
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Listening on {port} at {baud_rate} baud rate...")
            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    hex_data = data.hex()
                    print(f"Received Data: {hex_data}")
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopped listening.")

if __name__ == "__main__":
    read_from_serial()
