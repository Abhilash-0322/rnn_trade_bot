from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class BotConfig:
    user_id: str
    symbol: str
    buy_threshold: float
    sell_threshold: float
    quantity: float
    is_active: bool = False
    dry_run: bool = True
    bot_type: str = "THRESHOLD"  # THRESHOLD, RNN
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    config_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bot config to dictionary for MongoDB storage"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at
        if self.updated_at:
            data['updated_at'] = self.updated_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotConfig':
        """Create bot config from dictionary"""
        data = dict(data)
        # Map Mongo _id to config_id and remove _id
        if '_id' in data:
            data['config_id'] = str(data.get('_id'))
            data.pop('_id', None)
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        # Keep only known keys
        allowed = {
            'user_id','symbol','buy_threshold','sell_threshold','quantity','is_active','dry_run','bot_type','created_at','updated_at','config_id'
        }
        sanitized = {k: v for k, v in data.items() if k in allowed}
        return cls(**sanitized)
    
    def update(self, **kwargs) -> None:
        """Update bot configuration"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
