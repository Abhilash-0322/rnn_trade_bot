from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import redirect, url_for, flash, request
from typing import Optional
from datetime import datetime

from ..models.user import User
from ..database.mongodb import MongoDB


class AuthManager:
    def __init__(self, app, db: MongoDB):
        self.app = app
        self.db = db
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Please log in to access this page.'
        self.login_manager.login_message_category = 'info'
        
        # Set up user loader
        self.login_manager.user_loader(self.load_user)
    
    def load_user(self, user_id: str) -> Optional[User]:
        """Load user for Flask-Login"""
        return self.db.get_user_by_id(user_id)
    
    def register_user(self, username: str, email: str, password: str, 
                     binance_api_key: str = None, binance_api_secret: str = None) -> tuple[bool, str]:
        """Register a new user"""
        try:
            # Check if username already exists
            if self.db.get_user_by_username(username):
                return False, "Username already exists"
            
            # Check if email already exists
            if self.db.get_user_by_email(email):
                return False, "Email already exists"
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            user.binance_api_key = binance_api_key
            user.binance_api_secret = binance_api_secret
            
            # Save to database
            user_id = self.db.create_user(user)
            
            return True, f"User registered successfully with ID: {user_id}"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login_user_by_username(self, username: str, password: str) -> tuple[bool, str]:
        """Login user by username and password"""
        try:
            user = self.db.get_user_by_username(username)
            if user and user.check_password(password):
                login_user(user, remember=True)
                return True, "Login successful"
            else:
                return False, "Invalid username or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def login_user_by_email(self, email: str, password: str) -> tuple[bool, str]:
        """Login user by email and password"""
        try:
            user = self.db.get_user_by_email(email)
            if user and user.check_password(password):
                login_user(user, remember=True)
                return True, "Login successful"
            else:
                return False, "Invalid email or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def logout_user(self) -> None:
        """Logout current user"""
        logout_user()
    
    def update_user_api_keys(self, user_id: str, api_key: str, api_secret: str) -> bool:
        """Update user's Binance API keys"""
        try:
            return self.db.update_user(user_id, {
                'binance_api_key': api_key,
                'binance_api_secret': api_secret
            })
        except Exception as e:
            print(f"Failed to update API keys: {e}")
            return False
    
    def get_current_user_api_keys(self) -> tuple[Optional[str], Optional[str]]:
        """Get current user's API keys"""
        if current_user.is_authenticated:
            return current_user.binance_api_key, current_user.binance_api_secret
        return None, None
    
    def require_auth(self, f):
        """Decorator to require authentication"""
        return login_required(f)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.get_user_by_id(user_id)
    
    def update_user_profile(self, user_id: str, updates: dict) -> bool:
        """Update user profile information"""
        try:
            return self.db.update_user(user_id, updates)
        except Exception as e:
            print(f"Failed to update user profile: {e}")
            return False
