import asyncio
import websockets
import json

class OKXWS:
    URL = "wss://ws.okx.com:8443/ws/v5/public"

    def __init__(self, symbols):
        self.subs = [{"channel":"tickers","instId":f"{s}-USDT"} for s in symbols]

    async def connect(self, callback):
    while True:
        try:
            async with websockets.connect(
                self.URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5
            ) as ws:
                print("OKX WS connected")
                await ws.send(json.dumps({"op": "subscribe", "args": self.subs}))
                while True:
                    msg = json.loads(await ws.recv())
                    if "data" in msg and msg["data"]:
                        d = msg["data"][0]
                        if "instId" in d and "last" in d:
                            callback("OKX", d["instId"].replace("-", ""), float(d["last"]))
        except Exception as e:
            print(f"OKX error: {e}")
            await asyncio.sleep(2)
