import serial
import time

# Configure the serial port
serial_port = '/dev/ttyUSB0'  # Change this to your actual serial port
baud_rate = 9600

# Define the message to be sent
message = bytes([0xc1, 0x00, 0x08])

with serial.Serial(
    port=serial_port,
    baudrate=baud_rate,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=5,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False
) as ser:
    # Flush any stale data in the buffers
    ser.flushInput()
    ser.flushOutput()

    # Send the message
    ser.write(message)
    print("Message sent:", message)

    # Allow some time for the device to process and respond
    time.sleep(1)  # Adjust sleep time as needed

    # Read the response
    response = ser.read(64)  # Adjust the number of bytes to read as necessary

    if response:
        print("Response received:", response.hex())
    else:
        print("No response received.")
