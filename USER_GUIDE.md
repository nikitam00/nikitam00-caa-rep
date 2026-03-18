# User Guide - Crypto Arbitrage Monitor

## What is this program?
A desktop application that shows **live cryptocurrency prices** from 5 exchanges simultaneously and automatically finds **arbitrage opportunities** - situations where you can buy cheap on one exchange and sell at a higher price on another.

---

## Installation

### 1. Install Python
Download Python 3.10+ from https://python.org

### 2. Install dependencies
Open terminal(cmd) and run:
```
pip install websockets aiohttp requests tkinter
```

### 3. Run the program
Open terminal(cmd), write path to folder:
```
cd path_to_nikitam00-caa-rep-main\nikitam00-caa-rep-main
```
For example: 'cd C:\Users\Nightmare\Desktop\nikitam00-caa-rep-main'

After path, write:
```
python main_ws.py
```

---

## Interface Overview

```
┌─────────────────────────────────────────────┐
│  [Settings]                                 │  ← Control bar
├──────┬──────────────────────────────────────┤
│ Coin │ Binance │ Bybit │ OKX │ KuCoin │ Gate│  ← Price table
│ XRP  │ 0.5123  │ ...   │ ... │ ...    │ ... │
│ SOL  │ 145.23  │ ...   │ ... │ ...    │ ... │
│ ...  │ ...     │ ...   │ ... │ ...    │ ... │
├──────┴──────────────────────────────────────┤
│  Arbitrage Opportunities                    │
│  Coin │ Buy    │ Sell  │ Buy$ │ Sell$ │  %  │  ← Arbitrage table
│  XRP  │ KuCoin │ Bybit │ 0.51 │ 0.53  │1.2% │
└─────────────────────────────────────────────┘
```

---

## Price Table

| Column | Description |
|--------|-------------|
| **Coin** | Cryptocurrency symbol (XRP, SOL, etc.) |
| **Binance / Bybit / OKX / KuCoin / Gate** | Current live price in USDT |
| *Loading...* | Waiting for data from exchange |

Prices update every **400ms** automatically.

---

## Arbitrage Table

Shows top 10 best arbitrage opportunities:

| Column | Description |
|--------|-------------|
| **Coin** | Cryptocurrency |
| **Buy Exchange** | Exchange with lowest price - buy here |
| **Sell Exchange** | Exchange with highest price - sell here |
| **Buy Price** | Price to buy at |
| **Sell Price** | Price to sell at |
| **Profit %** | Estimated profit percentage |

> ⚠️ Only opportunities with profit ≥ **0.1%** are shown.  
> ⚠️ This does not account for exchange fees - always check fees before trading.

---

## Settings

Click the **[Settings]** button to open the settings panel.

### Theme
- **Light** - white background (default)
- **Dark** - black background

### View (Zoom)
- Adjust UI scale from **70%** to **200%**
- Default: **100%**

### Add Coin
1. Type a coin symbol (e.g. `BTC`, `ETH`, `BNB`)
2. Click **Add**
3. The coin appears in the price table immediately
4. WebSocket connections restart to include the new coin

> ℹ️ Symbols are case-insensitive - `btc` and `BTC` are the same.

### Remove Coin
1. Select one or more coins from the list (hold Ctrl for multiple)
2. Click **Remove**
3. Selected coins are removed from the table

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| All prices show "Loading..." | Wait 5–10 seconds for WS to connect |
| One exchange shows "Loading..." | That exchange may be temporarily unavailable - auto-retry is active |
| Program doesn't start | Make sure all dependencies are installed: `pip install websockets aiohttp requests` |
| No arbitrage opportunities shown | Normal if prices are equal across exchanges at that moment |
