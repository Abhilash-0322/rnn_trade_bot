from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

from ..models.user import User
from ..models.trade import Trade
from ..models.bot_config import BotConfig


class MongoDB:
    def __init__(self, connection_string: str = None, database_name: str = "rnn_crypto"):
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        
        # Collections
        self.users: Optional[Collection] = None
        self.trades: Optional[Collection] = None
        self.bot_configs: Optional[Collection] = None
        self.prices: Optional[Collection] = None
        
    def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.users = self.db.users
            self.trades = self.db.trades
            self.bot_configs = self.db.bot_configs
            self.prices = self.db.prices
            
            # Create indexes
            self._create_indexes()
            
            print(f"Connected to MongoDB: {self.database_name}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self) -> None:
        """Create database indexes for better performance"""
        # Users collection indexes
        self.users.create_index("username", unique=True)
        self.users.create_index("email", unique=True)
        
        # Trades collection indexes
        self.trades.create_index([("user_id", 1), ("timestamp", -1)])
        self.trades.create_index([("user_id", 1), ("symbol", 1)])
        self.trades.create_index("order_id", unique=True, sparse=True)
        
        # Bot configs collection indexes
        self.bot_configs.create_index([("user_id", 1), ("symbol", 1)], unique=True)
        self.bot_configs.create_index([("user_id", 1), ("is_active", 1)])

        # Prices collection indexes
        self.prices.create_index([("symbol", 1), ("timestamp", 1)])
        self.prices.create_index("timestamp")
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    # User operations
    def create_user(self, user: User) -> str:
        """Create a new user"""
        user_data = user.to_dict()
        result = self.users.insert_one(user_data)
        user.user_id = str(result.inserted_id)
        return user.user_id
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_data = self.users.find_one({"username": username})
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_data = self.users.find_one({"email": email})
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        from bson import ObjectId
        user_data = self.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        from bson import ObjectId
        result = self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    # Trade operations
    def save_trade(self, trade: Trade) -> str:
        """Save a new trade"""
        trade_data = trade.to_dict()
        result = self.trades.insert_one(trade_data)
        trade.trade_id = str(result.inserted_id)
        return trade.trade_id
    
    def get_user_trades(self, user_id: str, limit: int = 100, skip: int = 0) -> List[Trade]:
        """Get trades for a specific user"""
        cursor = self.trades.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
        return [Trade.from_dict(trade_data) for trade_data in cursor]
    
    def get_trades_by_symbol(self, user_id: str, symbol: str, limit: int = 100) -> List[Trade]:
        """Get trades for a specific symbol and user"""
        cursor = self.trades.find({"user_id": user_id, "symbol": symbol}).sort("timestamp", -1).limit(limit)
        return [Trade.from_dict(trade_data) for trade_data in cursor]
    
    def get_trades_by_type(self, user_id: str, trade_type: str, limit: int = 100) -> List[Trade]:
        """Get trades by type (MANUAL, BOT_THRESHOLD, etc.)"""
        cursor = self.trades.find({"user_id": user_id, "trade_type": trade_type}).sort("timestamp", -1).limit(limit)
        return [Trade.from_dict(trade_data) for trade_data in cursor]
    
    # Bot config operations
    def save_bot_config(self, config: BotConfig) -> str:
        """Save or update bot configuration"""
        config_data = config.to_dict()
        
        # Use upsert to create or update
        result = self.bot_configs.replace_one(
            {"user_id": config.user_id, "symbol": config.symbol},
            config_data,
            upsert=True
        )
        
        if result.upserted_id:
            config.config_id = str(result.upserted_id)
        return config.config_id or "updated"
    
    def get_bot_config(self, user_id: str, symbol: str) -> Optional[BotConfig]:
        """Get bot configuration for user and symbol"""
        config_data = self.bot_configs.find_one({"user_id": user_id, "symbol": symbol})
        if config_data:
            return BotConfig.from_dict(config_data)
        return None
    
    def get_user_bot_configs(self, user_id: str) -> List[BotConfig]:
        """Get all bot configurations for a user"""
        cursor = self.bot_configs.find({"user_id": user_id})
        return [BotConfig.from_dict(config_data) for config_data in cursor]
    
    def get_active_bot_configs(self, user_id: str) -> List[BotConfig]:
        """Get active bot configurations for a user"""
        cursor = self.bot_configs.find({"user_id": user_id, "is_active": True})
        return [BotConfig.from_dict(config_data) for config_data in cursor]
    
    def delete_bot_config(self, user_id: str, symbol: str) -> bool:
        """Delete bot configuration"""
        result = self.bot_configs.delete_one({"user_id": user_id, "symbol": symbol})
        return result.deleted_count > 0
    
    # Analytics operations
    def get_user_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio summary for a user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$symbol",
                "total_quantity": {"$sum": {"$cond": [{"$eq": ["$side", "BUY"]}, "$quantity", {"$multiply": ["$quantity", -1]}]}},
                "total_value": {"$sum": {"$multiply": ["$quantity", "$price"]}},
                "trade_count": {"$sum": 1},
                "last_trade": {"$last": "$timestamp"}
            }},
            {"$match": {"total_quantity": {"$gt": 0}}}
        ]
        
        positions = list(self.trades.aggregate(pipeline))
        return {"positions": positions}
    
    def get_user_trade_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get trading statistics for a user"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "timestamp": {"$gte": start_date}
            }},
            {"$group": {
                "_id": None,
                "total_trades": {"$sum": 1},
                "buy_trades": {"$sum": {"$cond": [{"$eq": ["$side", "BUY"]}, 1, 0]}},
                "sell_trades": {"$sum": {"$cond": [{"$eq": ["$side", "SELL"]}, 1, 0]}},
                "total_volume": {"$sum": {"$multiply": ["$quantity", "$price"]}},
                "manual_trades": {"$sum": {"$cond": [{"$eq": ["$trade_type", "MANUAL"]}, 1, 0]}},
                "bot_trades": {"$sum": {"$cond": [{"$ne": ["$trade_type", "MANUAL"]}, 1, 0]}}
            }}
        ]
        
        result = list(self.trades.aggregate(pipeline))
        return result[0] if result else {}

    # Price ticks operations
    def save_price_point(self, symbol: str, price: float, timestamp: int) -> str:
        """Insert a single price tick for a symbol."""
        doc = {
            "symbol": symbol,
            "timestamp": int(timestamp),
            "price": float(price),
        }
        result = self.prices.insert_one(doc)
        return str(result.inserted_id)

    def get_price_points_since(self, symbol: str, start_timestamp: int) -> List[Dict[str, Any]]:
        """Fetch price points for a symbol since a given timestamp, ascending."""
        cursor = self.prices.find({
            "symbol": symbol,
            "timestamp": {"$gte": int(start_timestamp)}
        }).sort("timestamp", 1)
        return [{
            "timestamp": int(doc["timestamp"]),
            "price": float(doc["price"])
        } for doc in cursor]
