from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Trade:
    user_id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    timestamp: datetime
    order_id: Optional[str] = None
    trade_type: str = "MANUAL"  # MANUAL, BOT_THRESHOLD, BOT_RNN
    bot_config: Optional[Dict[str, Any]] = None
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary for MongoDB storage"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp
        # Drop None-valued optional fields to avoid null writes (esp. unique indexes)
        for key in ['order_id', 'bot_config', 'trade_id']:
            if key in data and data[key] is None:
                data.pop(key)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create trade from dictionary"""
        data = dict(data)
        # Map Mongo _id to trade_id and remove _id
        if '_id' in data:
            data['trade_id'] = str(data.get('_id'))
            data.pop('_id', None)
        # Normalize timestamp if string
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        # Drop unknown keys defensively
        allowed_keys = {
            'user_id','symbol','side','quantity','price','timestamp','order_id','trade_type','bot_config','trade_id'
        }
        sanitized = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**sanitized)
    
    def get_value(self) -> float:
        """Calculate total trade value"""
        return self.quantity * self.price
    
    def is_buy(self) -> bool:
        """Check if trade is a buy order"""
        return self.side.upper() == "BUY"
    
    def is_sell(self) -> bool:
        """Check if trade is a sell order"""
        return self.side.upper() == "SELL"
