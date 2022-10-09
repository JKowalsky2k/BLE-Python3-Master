ADDRESS = "B66D3D28-8E6F-A25F-157B-181E7D3E2729"
UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

import sys
import platform
import asyncio
import logging
from time import sleep

from bleak import BleakClient, BleakScanner

logger = logging.getLogger(__name__)

async def main(address):
    devices = await BleakScanner.discover()
    for d in devices:
        print(d.details)

    async with BleakClient(address) as client:
        logger.info(f"Connected: {client.is_connected}")

        for service in client.services:
            logger.info(f"[Service] {service}")
            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))
                        logger.info(
                            f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                        )
                    except Exception as e:
                        logger.error(
                            f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {e}"
                        )

                else:
                    value = None
                    logger.info(
                        f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                    )

                for descriptor in char.descriptors:
                    try:
                        value = bytes(
                            await client.read_gatt_descriptor(descriptor.handle)
                        )
                        logger.info(f"\t\t[Descriptor] {descriptor}) | Value: {value}")
                    except Exception as e:
                        logger.error(f"\t\t[Descriptor] {descriptor}) | Value: {e}")

        for idx in range(10):
            print(f"it: {idx}")
            await client.write_gatt_char(UUID, b'N')
            sleep(1)
            await client.write_gatt_char(UUID, b'F')
            sleep(1)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(sys.argv[1] if len(sys.argv) == 2 else ADDRESS))