# Crypto Arbitrage Monitor
Real-time cryptocurrency price monitor with arbitrage opportunity detection across 5 exchanges.

## Features
- Live prices from **Binance, Bybit, OKX, KuCoin, Gate.io** via WebSocket
- **Arbitrage detection** - finds top 10 profit opportunities (≥ 0.1%)
- Add / remove coins dynamically
- Dark / Light theme
- UI zoom 70%-200%
- Auto-reconnect on connection loss

## Requirements
```
pip install websockets aiohttp requests tkinter
```

## Run
```
python main_ws.py
```

## Project Structure
```
nikitam00-caa-rep-main/
├── main_ws.py       # Main GUI + arbitrage logic
├── ws_binance.py    # Binance WebSocket
├── ws_bybit.py      # Bybit WebSocket
├── ws_okx.py        # OKX WebSocket
├── ws_kucoin.py     # KuCoin WebSocket
├── ws_gateio.py     # Gate.io WebSocket
├── README.md
├── TEST_PLAN.md
└── USER_GUIDE.md
```

## Requirements vs Implementation

| Requirement | Implementation | File |
|-------------|---------------|------|
| Show prices from 5 exchanges | Price table with all exchanges | `main_ws.py` |
| Binance WebSocket | `BinanceWS.connect()` | `ws_binance.py` |
| Bybit WebSocket | `BybitWS.connect()` | `ws_bybit.py` |
| OKX WebSocket | `OKXWS.connect()` | `ws_okx.py` |
| KuCoin WebSocket | `KuCoinWS.connect()` | `ws_kucoin.py` |
| Gate.io WebSocket | `GateWS.connect()` | `ws_gateio.py` |
| Arbitrage detection | `calculate_arbitrage()` | `main_ws.py` |
| Add coins | `_do_add_coin()` | `main_ws.py` |
| Remove coins | `_do_remove_coins()` | `main_ws.py` |
| Theme switching | `toggle_theme()` | `main_ws.py` |
| UI zoom | `_apply_zoom()` | `main_ws.py` |
| Auto-reconnect | `while True` + `asyncio.sleep(2)` | All WS files |
