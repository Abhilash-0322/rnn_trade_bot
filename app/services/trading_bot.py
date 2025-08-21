import threading
import time
from typing import Optional, Dict, Any


class TradingBot(threading.Thread):
    def __init__(
        self,
        binance,
        symbol: str,
        buy_threshold: float,
        sell_threshold: float,
        quantity: float,
        poll_interval: float = 2.0,
        db=None,
        portfolio=None,
        user_id: str | None = None,
    ):
        super().__init__(daemon=True)
        self.binance = binance
        self.symbol = symbol
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.quantity = quantity
        self.poll_interval = poll_interval
        self.stop_event = threading.Event()
        self.holding = False
        self.entry_price: Optional[float] = None
        self.db = db
        self.portfolio = portfolio
        self.user_id = user_id
        self.state: Dict[str, Any] = {
            "running": True,
            "symbol": symbol,
            "buy_threshold": buy_threshold,
            "sell_threshold": sell_threshold,
            "quantity": quantity,
            "last_price": None,
            "last_order": None,
            "holding": False,
            "entry_price": None,
        }

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                price = self.binance.get_price(self.symbol)
                self.state["last_price"] = price

                # Buy only if not holding and price is at/below buy threshold
                if not self.holding and price <= self.buy_threshold:
                    order = self.binance.place_market_order(self.symbol, "BUY", self.quantity)
                    self.holding = True
                    self.entry_price = price
                    self.state["holding"] = True
                    self.state["entry_price"] = price
                    self.state["last_order"] = {"type": "BUY", "price": price, "response": order}
                    # Persist trade if DB and user are available
                    if self.db and self.user_id:
                        try:
                            from ..models.trade import Trade as DbTrade
                            from ..services.portfolio import Trade as PTrade
                            trade = DbTrade(
                                user_id=self.user_id,
                                symbol=self.symbol,
                                side="BUY",
                                quantity=self.quantity,
                                price=float(order.get("price", price)),
                                timestamp=datetime.utcnow(),
                                order_id=order.get("orderId"),
                                trade_type="BOT_THRESHOLD",
                                bot_config={
                                    "buy_threshold": self.buy_threshold,
                                    "sell_threshold": self.sell_threshold,
                                    "quantity": self.quantity,
                                },
                            )
                            self.db.save_trade(trade)
                            if self.portfolio:
                                ts_ms = int(time.time() * 1000)
                                p_trade = PTrade(symbol=self.symbol, side="BUY", quantity=self.quantity, price=trade.price, timestamp=ts_ms, order_id=trade.order_id)
                                self.portfolio.add_trade(p_trade)
                        except Exception:
                            pass

                # Sell only if holding and price is at/above sell threshold
                elif self.holding and price >= self.sell_threshold:
                    order = self.binance.place_market_order(self.symbol, "SELL", self.quantity)
                    self.holding = False
                    self.entry_price = None
                    self.state["holding"] = False
                    self.state["entry_price"] = None
                    self.state["last_order"] = {"type": "SELL", "price": price, "response": order}
                    if self.db and self.user_id:
                        try:
                            from ..models.trade import Trade as DbTrade
                            from ..services.portfolio import Trade as PTrade
                            trade = DbTrade(
                                user_id=self.user_id,
                                symbol=self.symbol,
                                side="SELL",
                                quantity=self.quantity,
                                price=float(order.get("price", price)),
                                timestamp=datetime.utcnow(),
                                order_id=order.get("orderId"),
                                trade_type="BOT_THRESHOLD",
                                bot_config={
                                    "buy_threshold": self.buy_threshold,
                                    "sell_threshold": self.sell_threshold,
                                    "quantity": self.quantity,
                                },
                            )
                            self.db.save_trade(trade)
                            if self.portfolio:
                                ts_ms = int(time.time() * 1000)
                                p_trade = PTrade(symbol=self.symbol, side="SELL", quantity=self.quantity, price=trade.price, timestamp=ts_ms, order_id=trade.order_id)
                                self.portfolio.add_trade(p_trade)
                        except Exception:
                            pass

            except Exception as exc:  # noqa: BLE001
                self.state["error"] = str(exc)

            time.sleep(self.poll_interval)

        self.state["running"] = False

    def stop(self) -> None:
        self.stop_event.set()


class TradingBotManager:
    def __init__(self, binance, db=None, portfolio=None, user_id_getter=None):
        self.binance = binance
        self.db = db
        self.portfolio = portfolio
        # user_id_getter: callable returning current user id (optional)
        self.user_id_getter = user_id_getter
        self._lock = threading.Lock()
        self._bot: Optional[TradingBot] = None

    def start(self, symbol: str, buy_threshold: float, sell_threshold: float, quantity: float) -> Dict[str, Any]:
        with self._lock:
            if self._bot and self._bot.is_alive():
                raise RuntimeError("Bot already running")
            # Pass db/portfolio/user context if available
            uid = None
            try:
                from flask_login import current_user
                if current_user and current_user.is_authenticated:
                    uid = current_user.user_id
            except Exception:
                uid = None
            self._bot = TradingBot(self.binance, symbol, buy_threshold, sell_threshold, quantity, db=self.db, portfolio=self.portfolio, user_id=uid)
            self._bot.start()
            return {"started": True, "symbol": symbol, "buy_threshold": buy_threshold, "sell_threshold": sell_threshold, "quantity": quantity}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if not self._bot:
                return {"stopped": False, "reason": "not running"}
            self._bot.stop()
            self._bot.join(timeout=2.0)
            self._bot = None
            return {"stopped": True}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            if not self._bot:
                return {"running": False}
            return {"running": True, **self._bot.state}

    def is_running(self) -> bool:
        with self._lock:
            return self._bot is not None and self._bot.is_alive()
