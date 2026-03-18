# Test Plan - Crypto Arbitrage Monitor

## Scope
Testing covers all modules: 5 WebSocket connectors, arbitrage logic, and GUI.

---

## 1. Unit Tests

### 1.1 `on_price()` — price ingestion

| ID | Input | Expected | Status |
|----|-------|----------|--------|
| T01 | `on_price("Binance", "xrpusdt", "0.52")` | `prices["Binance"]["XRPUSDT"] == 0.52` | ✅ Pass |
| T02 | `on_price("Binance", "XRP_USDT", "0.52")` | Stored as `"XRPUSDT"` (normalized) | ✅ Pass |
| T03 | `on_price("Binance", "XRPUSDT", "abc")` | Price not saved (ValueError caught) | ✅ Pass |
| T04 | `on_price("Binance", "XRPUSDT", "-1")` | Price not saved (value ≤ 0) | ✅ Pass |
| T05 | `on_price("Binance", "XRPUSDT", "0")` | Price not saved (value = 0) | ✅ Pass |

> **Note:** T03–T05 were failing in the current version of `on_price()` because validation was removed.  
> **Fix applied:** validation re-added (see code).

### 1.2 `calculate_arbitrage()`

| ID | Setup | Expected | Status |
|----|-------|----------|--------|
| T06 | Binance=1.00, Bybit=1.05 for XRP | Opportunity found, profit ≈ 5% | ✅ Pass |
| T07 | Only 1 exchange has price | No opportunity (need ≥ 2) | ✅ Pass |
| T08 | All exchanges same price | No opportunity (profit = 0%) | ✅ Pass |
| T09 | Profit = 0.09% | Not shown (below 0.1% threshold) | ✅ Pass |
| T10 | 15 opportunities exist | Only top 10 returned | ✅ Pass |

---

## 2. WebSocket Module Tests

| ID | Module | What is tested | Expected | Status |
|----|--------|---------------|----------|--------|
| T11 | `ws_binance.py` | Connect to Binance stream | "Binance WS connected" printed | ✅ Pass |
| T12 | `ws_bybit.py` | Connect to Bybit stream | "Bybit WS connected" printed | ✅ Pass |
| T13 | `ws_okx.py` | Connect to OKX stream | "OKX WS connected" printed | ✅ Pass |
| T14 | `ws_kucoin.py` | Connect to KuCoin stream | "KuCoin WS connected" printed | ✅ Pass |
| T15 | `ws_gateio.py` | Connect to Gate.io stream | "Gate.io WS connected" printed | ✅ Pass |
| T16 | All modules | Auto-reconnect after error | Reconnects after 2 seconds | ✅ Pass |
| T17 | `ws_bybit.py` | >10 coins (chunking) | Splits into chunks of 10 | ✅ Pass |

---

## 3. Integration Tests

| ID | What is tested | Expected | Status |
|----|---------------|----------|--------|
| T18 | All 5 WS run simultaneously | All connect, `prices` dict populated | ✅ Pass |
| T19 | Add new coin via GUI | WS restarts, new coin gets prices | ✅ Pass |
| T20 | Remove coin via GUI | WS restarts, coin removed from table | ✅ Pass |
| T21 | `ws_supervisor` restarts on event | New WS task created after cancel | ✅ Pass |

---

## 4. GUI Tests

| ID | What is tested | Expected | Status |
|----|---------------|----------|--------|
| T22 | App startup | Window opens, all coins show "Loading..." | ✅ Pass |
| T23 | Price table updates | Prices appear within 5–10 seconds | ✅ Pass |
| T24 | Arbitrage table updates | Opportunities shown with profit % | ✅ Pass |
| T25 | Open Settings | Settings window opens | ✅ Pass |
| T26 | Open Settings twice | Second click focuses existing window | ✅ Pass |
| T27 | Switch to Dark theme | All UI elements turn dark | ✅ Pass |
| T28 | Switch to Light theme | All UI elements turn light | ✅ Pass |
| T29 | Zoom to 150% | Fonts and row heights scale up | ✅ Pass |
| T30 | Zoom to 70% | Fonts and row heights scale down | ✅ Pass |
| T31 | Add coin "ETH" | Appears in both coin and price table | ✅ Pass |
| T32 | Add coin "eth" (lowercase) | Normalized to "ETH", added correctly | ✅ Pass |
| T33 | Add duplicate coin | Not added twice | ✅ Pass |
| T34 | Remove coin | Disappears from both tables | ✅ Pass |
| T35 | Remove multiple coins | All selected coins removed | ✅ Pass |
| T36 | Scroll price table | Both coin column and price table scroll in sync | ✅ Pass |
| T37 | Resize window | Table container height adjusts | ✅ Pass |

---

## 5. Bugs Found & Fixed

| Bug ID | Description | Where | Fix |
|--------|-------------|-------|-----|
| B01 | `on_price()` missing validation — zero/negative/invalid prices were stored | `main_ws.py` | Re-added `try/except` and `value <= 0` check |
| B02 | OKX module had no `while True` / reconnect loop | `ws_okx.py` | Added reconnect loop with `asyncio.sleep(2)` |
| B03 | OKX crashed if `msg["data"]` was empty list | `ws_okx.py` | Added `if msg["data"]` guard |
| B04 | Scrollbar desynced between coin list and price table | `main_ws.py` | `_sync_scroll()` syncs both trees |
