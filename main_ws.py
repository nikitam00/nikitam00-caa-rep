import asyncio
import threading
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from ws_binance import BinanceWS
from ws_bybit import BybitWS
from ws_okx import OKXWS
from ws_kucoin import KuCoinWS
from ws_gateio import GateWS


COINS = ["XRP", "SOL", "DOGE", "TRX", "ADA", "LINK", "AVAX", "SUI", "LTC", "TON", "DOT"]
EXCHANGES = ["Binance", "Bybit", "OKX", "KuCoin", "Gate"]

UPDATE_INTERVAL = 400
ZOOM_RANGE = range(70, 201, 10)
ZOOM_STEP = 10
DEFAULT_ZOOM = 100

COLOR_BG_LIGHT = "#ffffff"
COLOR_FG_LIGHT = "#000000"
COLOR_HEADING_BG_LIGHT = "#e0e0e0"
COLOR_BTN_BG_LIGHT = "#e0e0e0"

COLOR_BG_DARK = "#000000"
COLOR_FG_DARK = "#ffffff"
COLOR_HEADING_BG_DARK = "#1a1a1a"
COLOR_BTN_BG_DARK = "#1a1a1a"
COLOR_SELECT_BG_DARK = "#ffffff"
COLOR_SELECT_FG_DARK = "#000000"

COLOR_SELECT_BG_LIGHT = "#cceeff"
COLOR_SELECT_FG_LIGHT = "#000000"

TABLE_COIN_WIDTH = 50
TABLE_EXCHANGE_WIDTH = 73
TABLE_PADDING = 6
TABLE_MIN_ROWHEIGHT = 2

WINDOW_WIDTH_RATIO = 2
WINDOW_HEIGHT_RATIO = 2
SETTINGS_WIDTH_RATIO = 2
SETTINGS_HEIGHT_RATIO = 2
SETTINGS_MIN_WIDTH = 200
SETTINGS_MIN_HEIGHT = 150

SETTINGS_OPTIONS = ["Theme", "View", "Add", "Remove"]

PRICE_DECIMAL_PLACES = 5
LOADING_TEXT = "Loading..."

ARBITRAGE_MIN_PROFIT = 0.1

prices = {ex: {} for ex in EXCHANGES}
arbitrage_opportunities = []

ws_loop = None
ws_restart_event = None
ws_ready_event = threading.Event()


def on_price(exchange, symbol, price):
    symbol = symbol.upper().replace("_", "").strip()
    try:
        value = float(price)
    except (TypeError, ValueError):
        return
    if value <= 0:
        return
    prices[exchange][symbol] = value


def calculate_arbitrage():
    global arbitrage_opportunities
    opportunities = []
    
    for coin in COINS:
        coin_prices = {}
        for ex in EXCHANGES:
            price = prices[ex].get(coin + "USDT") or prices[ex].get(coin)
            if price is not None:
                coin_prices[ex] = float(price)
        
        if len(coin_prices) >= 2:
            min_ex = min(coin_prices, key=coin_prices.get)
            max_ex = max(coin_prices, key=coin_prices.get)
            min_price = coin_prices[min_ex]
            max_price = coin_prices[max_ex]
            
            profit_percent = ((max_price - min_price) / min_price) * 100
            
            if profit_percent >= ARBITRAGE_MIN_PROFIT:
                opportunities.append({
                    "coin": coin,
                    "buy_exchange": min_ex,
                    "sell_exchange": max_ex,
                    "buy_price": min_price,
                    "sell_price": max_price,
                    "profit_percent": profit_percent
                })
    
    opportunities.sort(key=lambda x: x["profit_percent"], reverse=True)
    arbitrage_opportunities = opportunities[:10]


class PriceTableGUI:
    def __init__(self, root):
        self.root = root

        self.style = ttk.Style()
        self.default_theme = self.style.theme_use()
        self.style.theme_use("clam")

        self.base_btn_font = tkfont.Font(font=self.style.lookup("TButton", "font"))
        self.base_tree_font = tkfont.Font(font=self.style.lookup("Treeview", "font"))
        self.base_heading_font = tkfont.Font(font=self.style.lookup("Treeview.Heading", "font"))
        self.base_rowheight = int(self.style.lookup("Treeview", "rowheight") or 20)

        default = tkfont.nametofont("TkDefaultFont")
        self.base_default_size = default.cget("size")
        text = tkfont.nametofont("TkTextFont")
        self.base_text_size = text.cget("size")

        self.zoom_factor = 1.0
        self.dark = False
        
        self.initial_root_bg = root.cget("bg")

        self.default_btn_padding = self.style.lookup("TButton","padding") or (6,2)

        self.style.configure(
            "Custom.Treeview",
            background=COLOR_BG_LIGHT,
            foreground=COLOR_FG_LIGHT,
            fieldbackground=COLOR_BG_LIGHT,
            font=self.base_tree_font,
            rowheight=self.base_rowheight,
        )
        self.style.configure("Custom.Treeview.Heading", background=COLOR_HEADING_BG_LIGHT, foreground=COLOR_FG_LIGHT, font=self.base_heading_font)
        self.style.configure(
            "Custom.TButton",
            background=COLOR_BTN_BG_LIGHT,
            foreground=COLOR_FG_LIGHT,
            font=self.base_btn_font,
            padding=self.default_btn_padding,
        )

        self.control_frame = tk.Frame(root, bg=self.initial_root_bg)
        self.control_frame.pack(fill="x", padx=TABLE_PADDING, pady=TABLE_PADDING)

        self.settings_btn = ttk.Button(
            self.control_frame, text="Settings", command=self.open_settings, style="Custom.TButton"
        )
        self.settings_btn.pack(side="left", padx=4)

        self.table_container = tk.Frame(root, bg=self.initial_root_bg)
        self.table_container.pack(fill="x", padx=TABLE_PADDING, pady=(0, TABLE_PADDING))
        self.table_container.pack_propagate(False)

        self.tree_frame = tk.Frame(self.table_container, bd=1, relief="solid", bg=self.initial_root_bg)
        self.tree_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(root, bg=self.initial_root_bg)
        self.bottom_frame.pack(fill="both", expand=True)
        
        self.arb_label = tk.Label(self.bottom_frame, text="Arbitrage Opportunities", 
                            font=("Arial", 12, "bold"), bg=self.initial_root_bg)
        self.arb_label.pack(pady=5)
        
        arb_scroll_frame = tk.Frame(self.bottom_frame, bg=self.initial_root_bg)
        arb_scroll_frame.pack(fill="both", expand=True, padx=TABLE_PADDING, pady=(0, TABLE_PADDING))
        
        arb_v_scroll = ttk.Scrollbar(arb_scroll_frame, orient="vertical")
        arb_v_scroll.pack(side="right", fill="y")
        
        self.arb_tree = ttk.Treeview(
            arb_scroll_frame,
            columns=("Coin", "Buy", "Sell", "Buy Price", "Sell Price", "Profit %"),
            show="headings",
            style="Custom.Treeview",
            yscrollcommand=arb_v_scroll.set,
            height=10
        )
        self.arb_tree.pack(side="left", fill="both", expand=True)
        arb_v_scroll.config(command=self.arb_tree.yview)
        
        self.arb_tree.heading("Coin", text="Coin")
        self.arb_tree.heading("Buy", text="Buy Exchange")
        self.arb_tree.heading("Sell", text="Sell Exchange")
        self.arb_tree.heading("Buy Price", text="Buy Price")
        self.arb_tree.heading("Sell Price", text="Sell Price")
        self.arb_tree.heading("Profit %", text="Profit %")
        
        self.arb_tree.column("Coin", width=60, anchor="center")
        self.arb_tree.column("Buy", width=100, anchor="center")
        self.arb_tree.column("Sell", width=100, anchor="center")
        self.arb_tree.column("Buy Price", width=100, anchor="e")
        self.arb_tree.column("Sell Price", width=100, anchor="e")
        self.arb_tree.column("Profit %", width=80, anchor="e")
        
        self.coin_frame = tk.Frame(self.tree_frame, bg=self.initial_root_bg)
        self.coin_frame.pack(side="left", fill="y")
        
        self.table_frame = tk.Frame(self.tree_frame, bg=self.initial_root_bg)
        self.table_frame.pack(side="left", fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        self.coin_tree = ttk.Treeview(
            self.coin_frame,
            columns=("Coin",),
            show="headings",
            style="Custom.Treeview"
        )
        self.coin_tree.pack(side="left", fill="y", expand=False)
        self.coin_tree.heading("Coin", text="Coin", anchor="center")
        self.coin_tree.column("Coin", width=TABLE_COIN_WIDTH, minwidth=TABLE_COIN_WIDTH, anchor="w", stretch=tk.NO)
        self.coin_tree.bind("<Button-1>", self._prevent_column_resize)
        
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=EXCHANGES,
            show="headings",
            yscrollcommand=v_scrollbar.set,
            style="Custom.Treeview"
        )
        self.tree.pack(fill="both", expand=True)
        v_scrollbar.config(command=self._on_vscroll)
        self.coin_tree.configure(yscrollcommand=self._sync_scroll)
        self.tree.configure(yscrollcommand=self._sync_scroll)
        
        for ex in EXCHANGES:
            self.tree.heading(ex, text=ex)
            self.tree.column(ex, width=TABLE_EXCHANGE_WIDTH, anchor="e", stretch=tk.YES)

        self.tree.bind("<Button-1>", self._prevent_column_resize)

        self._populate_initial()
        self.update_interval = UPDATE_INTERVAL

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw//WINDOW_WIDTH_RATIO}x{sh//WINDOW_HEIGHT_RATIO}")
        root.after(0, lambda: self._center(root))
        root.bind("<Configure>", self._on_root_resize)
        root.after(50, self._on_root_resize)

    def _center(self, win, w=None, h=None):
        win.update_idletasks()
        if w is None:
            w = win.winfo_width()
        if h is None:
            h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _on_root_resize(self, event=None):
        h = self.root.winfo_height()
        self.table_container.configure(height=max(240, int(h * 0.6)))

    def _sync_scroll(self, *args):
        self.tree.yview_moveto(args[0])
        self.coin_tree.yview_moveto(args[0])
        v_scrollbar = self.tree_frame.winfo_children()[-1]
        v_scrollbar.set(*args)

    def _on_vscroll(self, *args):
        self.tree.yview(*args)
        self.coin_tree.yview(*args)

    def _prevent_column_resize(self, event):
        widget = event.widget
        if widget.identify_region(event.x, event.y) == "separator":
            return "break"

    def _populate_initial(self):
        for coin in COINS:
            if not self.coin_tree.exists(coin):
                self.coin_tree.insert("", "end", iid=coin, values=(coin,))
            
            values = [LOADING_TEXT for _ in EXCHANGES]
            if not self.tree.exists(coin):
                self.tree.insert("", "end", iid=coin, values=values)

    def open_settings(self):
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Settings")
        
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        settings_w = max(SETTINGS_MIN_WIDTH, main_width // SETTINGS_WIDTH_RATIO)
        settings_h = max(SETTINGS_MIN_HEIGHT, main_height // SETTINGS_HEIGHT_RATIO)
        win.geometry(f"{settings_w}x{settings_h}")
        
        self.settings_window = win
        self._center(win, settings_w, settings_h)

        left = tk.Frame(win)
        left.pack(side="left", fill="y")
        right = tk.Frame(win)
        right.pack(side="left", fill="both", expand=True, padx=TABLE_PADDING, pady=TABLE_PADDING)

        listbox = tk.Listbox(left, exportselection=False)
        for o in SETTINGS_OPTIONS:
            listbox.insert("end", o)
        listbox.pack(fill="y", expand=True)
        listbox.bind("<<ListboxSelect>>", self._settings_changed)

        self.settings_frames = {}

        frm_t = tk.Frame(right)
        tk.Label(frm_t, text="Choose interface theme:").pack(anchor="w", pady=5)
        self.theme_var = tk.StringVar(value="Dark" if self.dark else "Light")
        tk.Radiobutton(
            frm_t, text="Light", variable=self.theme_var, value="Light",
            command=lambda: self._apply_theme_choice(self.theme_var.get()),
        ).pack(anchor="w")
        tk.Radiobutton(
            frm_t, text="Dark", variable=self.theme_var, value="Dark",
            command=lambda: self._apply_theme_choice(self.theme_var.get()),
        ).pack(anchor="w")
        self.settings_frames["Theme"] = frm_t

        frm_v = tk.Frame(right)
        tk.Label(frm_v, text="This setting adjusts zoom/scale of the interface:").pack(anchor="w", pady=5)
        self.zoom_var = tk.IntVar(value=int(self.zoom_factor * DEFAULT_ZOOM))
        vals = [str(i) for i in ZOOM_RANGE]
        self.zoom_combo = ttk.Combobox(frm_v, values=vals, textvariable=self.zoom_var, state="readonly", width=5)
        self.zoom_combo.pack(anchor="w")
        self.zoom_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_zoom())
        self.settings_frames["View"] = frm_v

        frm_a = tk.Frame(right)
        tk.Label(frm_a, text="Add coin (symbol):").pack(anchor="w", pady=5)
        self.add_entry = tk.Entry(frm_a)
        self.add_entry.pack(anchor="w")
        tk.Button(frm_a, text="Add", command=self._do_add_coin).pack(anchor="w", pady=4)
        self.settings_frames["Add"] = frm_a

        frm_r = tk.Frame(right)
        tk.Label(frm_r, text="Select coin(s) to remove:").pack(anchor="w", pady=5)
        self.remove_listbox = tk.Listbox(frm_r, selectmode="extended")
        self.remove_listbox.pack(fill="both", expand=True)
        tk.Button(frm_r, text="Remove", command=self._do_remove_coins).pack(anchor="w", pady=4)
        self.settings_frames["Remove"] = frm_r

        listbox.selection_set(0)
        self._settings_changed(listbox)

        self._update_settings_theme()
        self._apply_zoom()

    def _settings_changed(self, event_or_listbox):
        if isinstance(event_or_listbox, tk.Listbox):
            lb = event_or_listbox
        else:
            lb = event_or_listbox.widget
        sel = lb.curselection()
        if not sel:
            return
        choice = lb.get(sel[0])
        for f in self.settings_frames.values():
            f.pack_forget()

        frame = self.settings_frames.get(choice)
        if frame is not None:
            frame.pack(fill="both", expand=True)
        if choice == "Remove":
            self._populate_remove_list()

    def _apply_theme_choice(self, choice):
        want_dark = choice == "Dark"
        if want_dark != self.dark:
            self.toggle_theme()

    def _apply_zoom(self):
        scale = self.zoom_var.get() / DEFAULT_ZOOM
        self.zoom_factor = scale

        default = tkfont.nametofont("TkDefaultFont")
        default.configure(size=max(1, int(self.base_default_size * scale)))
        text = tkfont.nametofont("TkTextFont")
        text.configure(size=max(1, int(self.base_text_size * scale)))

        btn_family = self.base_btn_font.cget("family")
        btn_size = max(1, int(self.base_btn_font.cget("size") * scale))
        self.style.configure("Custom.TButton", font=(btn_family, btn_size))

        tree_family = self.base_tree_font.cget("family")
        tree_size = max(1, int(self.base_tree_font.cget("size") * scale))
        self.style.configure("Custom.Treeview", font=(tree_family, tree_size),
                             rowheight=max(TABLE_MIN_ROWHEIGHT, int(self.base_rowheight * scale)))

        head_family = self.base_heading_font.cget("family")
        head_size = max(1, int(self.base_heading_font.cget("size") * scale))
        self.style.configure("Custom.Treeview.Heading", font=(head_family, head_size))

        self._update_settings_theme()
        self.root.after(0, lambda: self._center(self.root))
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self._center(self.settings_window)

    def toggle_theme(self):
        self.dark = not self.dark
        if self.dark:
            bg = COLOR_BG_DARK
            fg = COLOR_FG_DARK
            fieldbg = COLOR_BG_DARK
            headbg = COLOR_HEADING_BG_DARK
            headfg = COLOR_FG_DARK
            self.style.theme_use("clam")
            self.style.configure("Custom.Treeview", background=bg, foreground=fg, fieldbackground=fieldbg)
            self.style.configure("Custom.Treeview.Heading", background=headbg, foreground=headfg)
            self.style.configure(
                "Custom.TButton",
                background=COLOR_BTN_BG_DARK,
                foreground=fg,
                font=self.base_btn_font,
                padding=self.default_btn_padding,
            )
            self.style.map("Custom.Treeview", background=[("selected", headbg)])
            self.style.map("Custom.Treeview", foreground=[("selected", fg)])
            
            self.root.configure(bg=bg)
            self.control_frame.configure(bg=bg)
            self.tree_frame.configure(bg=bg)
            self.table_container.configure(bg=bg)
            self.coin_frame.configure(bg=bg)
            self.table_frame.configure(bg=bg)
            self.bottom_frame.configure(bg=bg)
            self.arb_label.configure(bg=bg, fg=fg)
        else:
            self.style.theme_use("clam")
            self.style.configure("Custom.Treeview", background=COLOR_BG_LIGHT, foreground=COLOR_FG_LIGHT, fieldbackground=COLOR_BG_LIGHT)
            self.style.configure("Custom.Treeview.Heading", background=COLOR_HEADING_BG_LIGHT, foreground=COLOR_FG_LIGHT)
            self.style.configure(
                "Custom.TButton",
                background=COLOR_BTN_BG_LIGHT,
                foreground=COLOR_FG_LIGHT,
                font=self.base_btn_font,
                padding=self.default_btn_padding,
            )
            self.style.map("Custom.Treeview", background=[("selected", COLOR_SELECT_BG_LIGHT)])
            self.style.map("Custom.Treeview", foreground=[("selected", COLOR_SELECT_FG_LIGHT)])
            
            self.root.configure(bg=self.initial_root_bg)
            self.control_frame.configure(bg=self.initial_root_bg)
            self.tree_frame.configure(bg=self.initial_root_bg)
            self.table_container.configure(bg=self.initial_root_bg)
            self.coin_frame.configure(bg=self.initial_root_bg)
            self.table_frame.configure(bg=self.initial_root_bg)
            self.bottom_frame.configure(bg=self.initial_root_bg)
            self.arb_label.configure(bg=self.initial_root_bg, fg=COLOR_FG_LIGHT)

        if hasattr(self, "theme_var"):
            self.theme_var.set("Dark" if self.dark else "Light")
        for ex in EXCHANGES:
            self.tree.heading(ex, text=ex)

        self._update_settings_theme()

    def _update_settings_theme(self):
        if not hasattr(self, "settings_window") or not self.settings_window.winfo_exists():
            return
        win = self.settings_window
        if self.dark:
            bg = COLOR_BG_DARK
            fg = COLOR_FG_DARK
            sel_bg = COLOR_SELECT_BG_DARK
            sel_fg = COLOR_SELECT_FG_DARK
        else:
            bg = self.initial_root_bg
            fg = COLOR_FG_LIGHT
            sel_bg = COLOR_SELECT_BG_LIGHT
            sel_fg = COLOR_SELECT_FG_LIGHT

        win.configure(bg=bg)

        def recolor(widget):
            for w in widget.winfo_children():
                cls = w.__class__.__name__
                if cls in ("Frame", "LabelFrame"):
                    w.configure(bg=bg)
                elif cls == "Label":
                    w.configure(bg=bg, fg=fg)
                elif cls == "Radiobutton":
                    w.configure(bg=bg, fg=fg, selectcolor=bg)
                elif cls == "Listbox":
                    w.configure(bg=bg, fg=fg,
                                selectbackground=sel_bg,
                                selectforeground=sel_fg)
                elif cls == "Button":
                    w.configure(bg=bg, fg=fg)
                elif cls == "Entry":
                    w.configure(bg=bg, fg=fg, insertbackground=fg)
                recolor(w)
        recolor(win)

    def _do_add_coin(self):
        coin = self.add_entry.get().strip().upper()
        if coin and coin not in COINS:
            COINS.append(coin)
            self.coin_tree.insert("", "end", iid=coin, values=(coin,))
            values = [LOADING_TEXT for _ in EXCHANGES]
            self.tree.insert("", "end", iid=coin, values=values)
            request_ws_restart()
        self.add_entry.delete("0", "end")

    def _populate_remove_list(self):
        self.remove_listbox.delete(0, "end")
        for coin in COINS:
            self.remove_listbox.insert("end", coin)

    def _do_remove_coins(self):
        sel = list(self.remove_listbox.curselection())
        changed = False
        for idx in reversed(sel):
            coin = self.remove_listbox.get(idx)
            if coin in COINS:
                COINS.remove(coin)
                changed = True
            if self.tree.exists(coin):
                self.tree.delete(coin)
            if self.coin_tree.exists(coin):
                self.coin_tree.delete(coin)
        self._populate_remove_list()
        if changed:
            request_ws_restart()

    def refresh(self):
        for iid in self.tree.get_children():
            coin = iid
            row = []
            for ex in EXCHANGES:
                price = prices[ex].get(coin + "USDT") or prices[ex].get(coin)
                if price is not None:
                    row.append(f"{float(price):.{PRICE_DECIMAL_PLACES}f}")
                else:
                    row.append(LOADING_TEXT)
            self.tree.item(iid, values=row)
        
        calculate_arbitrage()
        
        for item in self.arb_tree.get_children():
            self.arb_tree.delete(item)
        
        for opp in arbitrage_opportunities:
            self.arb_tree.insert("", "end", values=(
                opp["coin"],
                opp["buy_exchange"],
                opp["sell_exchange"],
                f"{opp['buy_price']:.{PRICE_DECIMAL_PLACES}f}",
                f"{opp['sell_price']:.{PRICE_DECIMAL_PLACES}f}",
                f"{opp['profit_percent']:.2f}%"
            ))
        
        self.root.after(self.update_interval, self.refresh)


async def run_ws_for_current_coins():
    coins = COINS.copy()
    tasks = [
        asyncio.create_task(BinanceWS(coins).connect(on_price)),
        asyncio.create_task(BybitWS(coins).connect(on_price)),
        asyncio.create_task(OKXWS(coins).connect(on_price)),
        asyncio.create_task(KuCoinWS(coins).connect(on_price)),
        asyncio.create_task(GateWS(coins).connect(on_price)),
    ]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


async def ws_supervisor():
    global ws_restart_event
    ws_restart_event = asyncio.Event()
    ws_task = asyncio.create_task(run_ws_for_current_coins())

    while True:
        await ws_restart_event.wait()
        ws_restart_event.clear()

        if ws_task and not ws_task.done():
            ws_task.cancel()
            await asyncio.gather(ws_task, return_exceptions=True)

        ws_task = asyncio.create_task(run_ws_for_current_coins())


def request_ws_restart():
    if ws_loop and ws_restart_event:
        ws_loop.call_soon_threadsafe(ws_restart_event.set)


def start_ws_loop():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    ws_ready_event.set()
    ws_loop.run_until_complete(ws_supervisor())


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Crypto prices")
    gui = PriceTableGUI(root)

    threading.Thread(target=start_ws_loop, daemon=True).start()
    ws_ready_event.wait()

    gui.refresh()
    root.mainloop()
