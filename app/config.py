import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binance.vision")

    DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "ETHUSDT")
    ORDER_QUANTITY = float(os.getenv("ORDER_QUANTITY", "0.01"))
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
