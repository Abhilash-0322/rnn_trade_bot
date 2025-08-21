from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Optional, Dict, Any


class User(UserMixin):
    def __init__(self, username: str, email: str, password_hash: str = None, 
                 user_id: str = None, created_at: datetime = None, 
                 binance_api_key: str = None, binance_api_secret: str = None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret

    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        """Return user ID for Flask-Login"""
        return str(self.user_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for MongoDB storage"""
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'binance_api_key': self.binance_api_key,
            'binance_api_secret': self.binance_api_secret
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        return cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            user_id=str(data['_id']),
            created_at=data.get('created_at'),
            binance_api_key=data.get('binance_api_key'),
            binance_api_secret=data.get('binance_api_secret')
        )
