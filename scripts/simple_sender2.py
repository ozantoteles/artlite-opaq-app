import serial
import time

def send_data_via_serial(port='/dev/ttyUSB0', baud_rate=9600):
    try:
        # Open the serial port
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud rate...")
            
            # Define the start and end delimiters
            start_delimiter = b'\x00\x00'
            end_delimiter = b'\x44'
            
            # Example data to send
            data_payload = b'\x11\x22\x33'
            
            # Create the full message
            full_message = start_delimiter + data_payload + end_delimiter
            
            # Send the message
            while True:
                ser.write(full_message)
                print(f"Sent Data: {full_message.hex()}")
                time.sleep(1)  # Send data every second for testing purposes
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopped sending.")

if __name__ == "__main__":
    send_data_via_serial()
