import asyncio
from pymodbus.client import AsyncModbusSerialClient
import logging

# Set up logging for debugging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

async def run_modbus_master():
    try:
        # Create an asynchronous Modbus client for serial communication
        client = AsyncModbusSerialClient(
            port='COM61',   # Adjust this to the correct COM port for the USB to RS485 adapter
            baudrate=9600,
            parity='N',
            stopbits=2,
            bytesize=8,
            timeout=3
        )

        # Connect to the Modbus slave
        connection = await client.connect()

        if not connection:
            print("Failed to connect to the Modbus slave")
            return

        # Main loop to keep reading
        for _ in range(10):  # Adjust the loop or condition as needed
            try:
                # Send Modbus request to read holding registers
                response = await client.read_holding_registers(
                    address=1,  # Start address
                    count=120,   # Number of registers to read
                    slave=2     # Slave address
                )

                # Process the response
                if response.isError():
                    print(f"Error reading registers: {response}")
                else:
                    print(f"Read Registers: {response.registers}")

                await asyncio.sleep(1)  # Delay between requests, adjust as needed

            except Exception as e:
                print(f"An error occurred during communication: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        client.close()  # Close the Modbus client connection

if __name__ == "__main__":
    asyncio.run(run_modbus_master())
