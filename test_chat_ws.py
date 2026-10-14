
import asyncio
import json
import websockets


async def main():
    shopkeeper_url = (
        "ws://127.0.0.1:8000/ws/conversations/1?user_id=100"
    )
    vendor_url = (
        "ws://127.0.0.1:8000/ws/conversations/1?user_id=1"
    )

    async with websockets.connect(shopkeeper_url) as shopkeeper:
        async with websockets.connect(vendor_url) as vendor:

            await shopkeeper.send(json.dumps({
                "content": "Real-time test from StockTalk!"
            }))

            shopkeeper_message = json.loads(
                await shopkeeper.recv()
            )
            vendor_message = json.loads(
                await vendor.recv()
            )

            print("Shopkeeper received:")
            print(json.dumps(shopkeeper_message, indent=2))

            print("\nVendor received:")
            print(json.dumps(vendor_message, indent=2))

            assert shopkeeper_message["id"] == vendor_message["id"]
            assert shopkeeper_message["content"] == (
                "Real-time test from StockTalk!"
            )
            assert vendor_message["sender_id"] == 100

            print("\nSUCCESS: Both participants received the same message!")


asyncio.run(main())
