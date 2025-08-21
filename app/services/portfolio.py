import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    entry_time: int
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: float = 0.0


@dataclass
class Trade:
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    timestamp: int
    order_id: Optional[str] = None


class PortfolioManager:
    def __init__(self, binance_client):
        self.binance = binance_client
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self._lock = None  # Will be set by Flask app
        
    def set_lock(self, lock):
        self._lock = lock
        
    def add_trade(self, trade: Trade) -> None:
        """Record a new trade and update positions"""
        if self._lock:
            with self._lock:
                self._add_trade_internal(trade)
        else:
            self._add_trade_internal(trade)
    
    def _add_trade_internal(self, trade: Trade) -> None:
        self.trades.append(trade)
        
        if trade.side == "BUY":
            # Add to position or create new
            if trade.symbol in self.positions:
                pos = self.positions[trade.symbol]
                # Weighted average price
                total_quantity = pos.quantity + trade.quantity
                total_value = (pos.quantity * pos.entry_price) + (trade.quantity * trade.price)
                pos.entry_price = total_value / total_quantity
                pos.quantity = total_quantity
            else:
                self.positions[trade.symbol] = Position(
                    symbol=trade.symbol,
                    quantity=trade.quantity,
                    entry_price=trade.price,
                    entry_time=trade.timestamp
                )
        elif trade.side == "SELL":
            # Reduce position
            if trade.symbol in self.positions:
                pos = self.positions[trade.symbol]
                if pos.quantity >= trade.quantity:
                    # Calculate realized PnL
                    realized_pnl = (trade.price - pos.entry_price) * trade.quantity
                    pos.realized_pnl += realized_pnl
                    pos.quantity -= trade.quantity
                    
                    # Remove position if quantity becomes 0
                    if pos.quantity <= 0:
                        del self.positions[trade.symbol]
                else:
                    # Partial sell - this shouldn't happen in normal trading
                    pos.quantity = 0
                    del self.positions[trade.symbol]
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices and calculate unrealized PnL"""
        if self._lock:
            with self._lock:
                self._update_prices_internal(prices)
        else:
            self._update_prices_internal(prices)
    
    def _update_prices_internal(self, prices: Dict[str, float]) -> None:
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with positions and PnL"""
        if self._lock:
            with self._lock:
                return self._get_portfolio_summary_internal()
        else:
            return self._get_portfolio_summary_internal()
    
    def _get_portfolio_summary_internal(self) -> Dict[str, Any]:
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in self.positions.values())
        
        positions_data = []
        for symbol, pos in self.positions.items():
            positions_data.append({
                "symbol": symbol,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "realized_pnl": pos.realized_pnl,
                "entry_time": pos.entry_time,
            })
        
        return {
            "positions": positions_data,
            "total_realized_pnl": total_realized_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_pnl": total_realized_pnl + total_unrealized_pnl,
            "position_count": len(self.positions),
            "trade_count": len(self.trades),
        }
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades"""
        if self._lock:
            with self._lock:
                return [asdict(trade) for trade in self.trades[-limit:]]
        else:
            return [asdict(trade) for trade in self.trades[-limit:]]
