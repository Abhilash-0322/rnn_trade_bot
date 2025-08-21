from flask import Flask
from flask_cors import CORS
import threading
import os

from .config import Config
from .binance_client import BinanceClient
from .services.trading_bot import TradingBotManager
from .services.portfolio import PortfolioManager
from .services.price_storage import PriceStorage
from .database.mongodb import MongoDB
from .auth.auth_manager import AuthManager

def create_app():
    app = Flask(__name__, static_folder="../static", static_url_path="/static")
    app.config.from_object(Config)
    
    # Set secret key for sessions
    app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Initialize MongoDB
    app.mongodb = MongoDB()
    try:
        app.mongodb.connect()
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        # Continue without MongoDB for now
        app.mongodb = None

    # Initialize Authentication Manager
    if app.mongodb:
        app.auth_manager = AuthManager(app, app.mongodb)
    else:
        app.auth_manager = None

    # Initialize Binance client (will be user-specific later)
    app.binance = BinanceClient(
        api_key=app.config.get("BINANCE_API_KEY", ""),
        api_secret=app.config.get("BINANCE_API_SECRET", ""),
        base_url=app.config.get("BINANCE_BASE_URL", "https://testnet.binance.vision"),
        dry_run=app.config.get("DRY_RUN", True),
    )

    # Create shared lock for thread safety
    app.shared_lock = threading.Lock()
    
    app.portfolio = PortfolioManager(app.binance)
    app.portfolio.set_lock(app.shared_lock)
    # Provide db and portfolio to bot manager for future integration
    app.bot_manager = TradingBotManager(app.binance, db=app.mongodb, portfolio=app.portfolio)
    
    # Initialize price storage with Binance client and DB for dual-write
    app.price_storage = PriceStorage(binance_client=app.binance, db=app.mongodb)

    # Register blueprints
    from .api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    
    if app.auth_manager:
        from .routes.auth import auth_bp
        app.register_blueprint(auth_bp)

    @app.route("/")
    def root():
        return app.send_static_file("index.html")

    @app.route("/portfolio")
    def portfolio():
        return app.send_static_file("portfolio.html")



    @app.route("/dashboard")
    def dashboard():
        return app.send_static_file("dashboard.html")

    return app
