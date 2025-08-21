from typing import Any, Dict
import time

from binance.spot import Spot


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = Spot(api_key=api_key, api_secret=api_secret, base_url=base_url)

    def set_dry_run(self, dry_run: bool) -> None:
        self.dry_run = bool(dry_run)

    def get_price(self, symbol: str) -> float:
        data = self.client.ticker_price(symbol=symbol)
        return float(data["price"])

    # Backward-compat alias used by API routes
    def get_current_price(self, symbol: str) -> float:
        return self.get_price(symbol)

    def get_exchange_info(self):
        """Return list of trading symbols or raw exchange info.

        Provides a sensible fallback list when running in dry-run or
        if the upstream call fails.
        """
        try:
            info = self.client.exchange_info()
            # Return just symbol strings for convenience
            symbols = [s.get("symbol") for s in info.get("symbols", []) if s.get("symbol")]
            return symbols or info
        except Exception:
            # Fallback common symbols if network/auth restricted
            return ["ETHUSDT", "BTCUSDT", "SOLUSDT", "ADAUSDT", "AVAXUSDT"]

    def get_account_info(self) -> Dict[str, Any]:
        """Return account info; in dry-run return an empty balances stub."""
        if self.dry_run:
            return {"dry_run": True, "balances": []}
        try:
            return self.client.account()
        except Exception as exc:
            return {"error": str(exc)}

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        if self.dry_run:
            # Simulate execution at current market price
            try:
                simulated_price = self.get_price(symbol)
            except Exception:
                simulated_price = 0.0
            return {
                "dry_run": True,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": simulated_price,
                "timestamp": int(time.time() * 1000),
            }
        return self.client.new_order(symbol=symbol, side=side, type="MARKET", quantity=quantity)
