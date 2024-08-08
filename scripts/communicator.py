import serial
import threading

def read_from_serial(ser):
    """Read incoming data from the serial port and print it."""
    while True:
        if ser.in_waiting > 0:
            incoming_data = ser.read(ser.in_waiting).hex()  # Read incoming data and convert to hex
            print(f"Received: {incoming_data}")

def write_to_serial(ser):
    """Read input from the user, convert it to bytes, and send it to the serial port."""
    while True:
        user_input = input("Enter hex data to send (e.g., 'a1b2c3'): ")
        try:
            data = bytes.fromhex(user_input)  # Convert hex string to bytes
            ser.write(data)
            print(f"Sent: {user_input}")
        except ValueError:
            print("Invalid hex input. Please try again.")

def main():
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Open the serial port
        print("Serial port opened.")

        # Start a thread to read from the serial port
        read_thread = threading.Thread(target=read_from_serial, args=(ser,))
        read_thread.daemon = True
        read_thread.start()

        # Run the write loop in the main thread
        write_to_serial(ser)

    except serial.SerialException as e:
        print(f"Serial exception: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
