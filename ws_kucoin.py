import asyncio
import websockets
import requests
import json

class KuCoinWS:
    API = "https://api.kucoin.com/api/v1/bullet-public"

    def __init__(self, symbols):
        self.symbols = symbols
        self.topic = "/market/ticker:" + ",".join([f"{s}-USDT" for s in symbols])

    async def connect(self, callback):
        while True:
            try:
                bullet = requests.post(self.API).json()["data"]
                ws_url = f"{bullet['instanceServers'][0]['endpoint']}?token={bullet['token']}"

                async with websockets.connect(ws_url) as ws:
                    print("KuCoin WS connected")
                    await ws.send(json.dumps({
                        "id": 1,
                        "type": "subscribe",
                        "topic": self.topic,
                        "privateChannel": False,
                        "response": True
                    }))

                    async for raw in ws:
                        msg = json.loads(raw)
                        data = msg.get("data")
                        if data and "price" in data:
                            symbol = data.get("symbol", "").replace("-", "") or \
                                     msg.get("topic", "").split(":")[-1].replace("-", "")
                            if symbol:
                                callback("KuCoin", symbol, float(data["price"]))
            except Exception as e:
                print(f"KuCoin error: {e}")
                await asyncio.sleep(2)
