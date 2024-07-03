import serial
import time
import random

# Configure the serial port
serial_port = '/dev/ttyUSB0'  # Change this to your actual serial port
baud_rate = 9600

# Create a serial connection with detailed configuration
ser = serial.Serial(
    port=serial_port,
    baudrate=baud_rate,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=5,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False
)

# Generate a random message of 6 bytes
random_message = bytes([random.randint(0, 255) for _ in range(6)])

try:
    # Flush any stale data in the buffers
    ser.flushInput()
    ser.flushOutput()

    # Send the random message
    ser.write(random_message)
    print("Random message sent:", random_message.hex())

    # Allow some time for the device to process and respond
    time.sleep(1)  # Adjust sleep time as needed

    # Read the response
    response = ser.read(64)  # Adjust the number of bytes to read as necessary

    if response:
        print("Response received:", response.hex())
    else:
        print("No response received.")

finally:
    # Close the serial connection
    ser.close()
