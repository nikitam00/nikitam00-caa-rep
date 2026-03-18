import asyncio
import aiohttp
import json


class BybitWS:
    URL = "wss://stream.bybit.com/v5/public/spot"
    MAX_CHANNELS = 10

    def __init__(self, symbols):
        self.chunks = [symbols[i:i + self.MAX_CHANNELS] for i in range(0, len(symbols), self.MAX_CHANNELS)]

    async def connect(self, callback):
        await asyncio.gather(*[self._run_chunk(chunk, callback) for chunk in self.chunks])

    async def _run_chunk(self, chunk, callback):
        channels = [f"publicTrade.{s.upper()}USDT" for s in chunk]

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.URL) as ws:
                        print(f"Bybit WS connected: {chunk}")
                        await ws.send_str(json.dumps({"op": "subscribe", "args": channels}))

                        async for msg in ws:
                            if msg.type != aiohttp.WSMsgType.TEXT:
                                continue
                            
                            try:
                                data = json.loads(msg.data)
                                if "topic" in data and "data" in data:
                                    trades = data["data"]
                                    if isinstance(trades, list) and trades:
                                        symbol = data["topic"].split(".", 1)[1].replace("_", "").upper()
                                        if "p" in trades[-1]:
                                            callback("Bybit", symbol, float(trades[-1]["p"]))
                            except (json.JSONDecodeError, ValueError, KeyError):
                                continue
            except Exception as e:
                print(f"Bybit error: {e}")
                await asyncio.sleep(2)
