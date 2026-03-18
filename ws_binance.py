import asyncio
import websockets
import json
import ssl

class BinanceWS:
    URL = "wss://stream.binance.com:9443/ws"

    def __init__(self, symbols):
        self.streams = [f"{s.lower()}usdt@trade" for s in symbols]

    async def connect(self, callback):
        url = f"{self.URL}/{'/'.join(self.streams)}"
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        while True:
            try:
                async with websockets.connect(url, ssl=ssl_ctx, ping_interval=20) as ws:
                    print("Binance WS connected")
                    async for raw in ws:
                        data = json.loads(raw)
                        if "s" in data and "p" in data:
                            callback("Binance", data["s"], float(data["p"]))
            except Exception as e:
                print(f"Binance error: {e}")
                await asyncio.sleep(2)