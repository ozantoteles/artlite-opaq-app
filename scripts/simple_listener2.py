import serial

def read_from_serial(port='/dev/ttyUSB0', baud_rate=9600):
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Listening on {port} at {baud_rate} baud rate...")
            buffer = bytearray()
            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    buffer.extend(data)
                    
                    # Process complete messages
                    while True:
                        start_index = buffer.find(b'\x00\x00')  # Example start delimiter
                        end_index = buffer.find(b'\x44')       # Example end delimiter
                        
                        if start_index != -1 and end_index != -1 and end_index > start_index:
                            complete_message = buffer[start_index:end_index + 1]
                            hex_data = complete_message.hex()
                            print(f"Received Data: {hex_data}")
                            # Remove processed message from buffer
                            buffer = buffer[end_index + 1:]
                        else:
                            break
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopped listening.")

if __name__ == "__main__":
    read_from_serial()
