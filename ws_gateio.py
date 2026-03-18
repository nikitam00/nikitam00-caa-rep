import asyncio
import websockets
import json
import time

class GateWS:
    URL = "wss://api.gateio.ws/ws/v4/"

    def __init__(self, symbols):
        self.payload = [f"{s}_USDT".upper() for s in symbols]

    async def connect(self, callback):
        while True:
            try:
                async with websockets.connect(self.URL) as ws:
                    print("Gate.io WS connected")
                    await ws.send(json.dumps({
                        "time": int(time.time()),
                        "channel": "spot.tickers",
                        "event": "subscribe",
                        "payload": self.payload
                    }))

                    async for raw in ws:
                        data = json.loads(raw)
                        if "result" in data:
                            result = data["result"]
                            if isinstance(result, dict):
                                symbol = result.get("currency_pair") or result.get("s", "")
                                price_key = "last" if "last" in result else "c"
                                if symbol and price_key in result:
                                    callback("Gate", symbol.replace("_", ""), float(result[price_key]))
            except Exception as e:
                print(f"Gate.io error: {e}")
                await asyncio.sleep(2)
