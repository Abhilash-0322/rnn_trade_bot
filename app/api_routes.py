from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import time
from datetime import datetime

from .models.trade import Trade
from .models.bot_config import BotConfig

api_bp = Blueprint('api', __name__)


@api_bp.get("/status")
def get_status():
    """Get bot status"""
    try:
        bot_manager = current_app.bot_manager
        binance_client = current_app.binance
        status = bot_manager.status()
        # Merge in dry_run info from client
        status["dry_run"] = binance_client.dry_run
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/price")
def get_price():
    """Get current price for a symbol"""
    try:
        symbol = request.args.get("symbol", "ETHUSDT")
        binance_client = current_app.binance
        
        price = binance_client.get_current_price(symbol)
        
        # Save price to storage
        if current_app.price_storage:
            current_app.price_storage.save_price(symbol, price)
        
        return jsonify({
            "symbol": symbol,
            "price": price,
            "timestamp": int(time.time() * 1000)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/price-history")
def get_price_history():
    """Get price history for a symbol"""
    try:
        symbol = request.args.get("symbol", "ETHUSDT")
        period = request.args.get("period", "1d")
        
        if not current_app.price_storage:
            return jsonify({"error": "Price storage not available"}), 500
        
        data = current_app.price_storage.get_price_history(symbol, period)
        
        return jsonify({
            "symbol": symbol,
            "period": period,
            "data": data,
            "count": len(data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/symbols")
def get_symbols():
    """Get available trading symbols"""
    try:
        binance_client = current_app.binance
        symbols = binance_client.get_exchange_info()
        return jsonify({"symbols": symbols})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.post("/start")
@login_required
def start_bot():
    """Start the trading bot"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "ETHUSDT")
        buy_threshold = float(data.get("buy_threshold", 3000))
        sell_threshold = float(data.get("sell_threshold", 3200))
        quantity = float(data.get("quantity", 0.01))
        dry_run = data.get("dry_run", True)
        
        bot_manager = current_app.bot_manager
        binance_client = current_app.binance
        
        # Update Binance client dry run setting
        binance_client.dry_run = dry_run
        
        # Save bot config to MongoDB if available
        if current_app.mongodb and current_user.is_authenticated:
            config = BotConfig(
                user_id=current_user.user_id,
                symbol=symbol,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold,
                quantity=quantity,
                is_active=True,
                dry_run=dry_run
            )
            current_app.mongodb.save_bot_config(config)
        
        # Start the bot with provided parameters
        bot_manager.start(symbol, buy_threshold, sell_threshold, quantity)
        
        return jsonify({
            "success": True,
            "message": "Bot started successfully",
            "dry_run": dry_run
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.post("/stop")
@login_required
def stop_bot():
    """Stop the trading bot"""
    try:
        bot_manager = current_app.bot_manager
        bot_manager.stop()
        
        # Update bot config in MongoDB if available
        if current_app.mongodb and current_user.is_authenticated:
            config = current_app.mongodb.get_bot_config(current_user.user_id, data.get("symbol", "ETHUSDT")) if (data := request.get_json(silent=True) or {}) else None
            if config:
                config.is_active = False
                current_app.mongodb.save_bot_config(config)
        
        return jsonify({"success": True, "message": "Bot stopped successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.post("/order")
@login_required
def place_order():
    """Place a manual order"""
    try:
        data = request.get_json()
        symbol = data.get("symbol", "ETHUSDT")
        side = data.get("side", "BUY")
        quantity = float(data.get("quantity", 0.01))
        
        binance_client = current_app.binance
        
        # Place order
        result = binance_client.place_market_order(symbol, side, quantity)
        
        # Save trade to MongoDB if available
        if current_app.mongodb and current_user.is_authenticated:
            trade = Trade(
                user_id=current_user.user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=float(result.get("price", 0) or current_app.binance.get_current_price(symbol)),
                timestamp=datetime.utcnow(),
                order_id=result.get("orderId"),
                trade_type="MANUAL"
            )
            current_app.mongodb.save_trade(trade)
            
            # Update portfolio
            if current_app.portfolio:
                from .services.portfolio import Trade as PortfolioTrade
                ts_ms = int(time.time() * 1000)
                p_trade = PortfolioTrade(symbol=symbol, side=side, quantity=quantity, price=trade.price, timestamp=ts_ms, order_id=trade.order_id)
                current_app.portfolio.add_trade(p_trade)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/portfolio")
@login_required
def get_portfolio():
    """Get user portfolio summary"""
    try:
        if not current_app.mongodb:
            return jsonify({"error": "Database not available"}), 500
        
        # Get portfolio summary from MongoDB
        summary = current_app.mongodb.get_user_portfolio_summary(current_user.user_id)
        
        # Get trade statistics
        stats = current_app.mongodb.get_user_trade_stats(current_user.user_id)
        
        return jsonify({
            "summary": summary,
            "stats": stats,
            "user_id": current_user.user_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/trades")
@login_required
def get_trades():
    """Get user trades"""
    try:
        if not current_app.mongodb:
            return jsonify({"error": "Database not available"}), 500
        
        limit = int(request.args.get("limit", 50))
        skip = int(request.args.get("skip", 0))
        
        trades = current_app.mongodb.get_user_trades(current_user.user_id, limit, skip)
        
        return jsonify({
            "trades": [trade.to_dict() for trade in trades],
            "count": len(trades)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/balances")
def get_balances():
    """Get account balances"""
    try:
        binance_client = current_app.binance
        balances = binance_client.get_account_info()
        return jsonify(balances)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/bot-configs")
@login_required
def get_bot_configs():
    """Get user's bot configurations"""
    try:
        if not current_app.mongodb:
            return jsonify({"error": "Database not available"}), 500
        
        configs = current_app.mongodb.get_user_bot_configs(current_user.user_id)
        
        return jsonify({
            "configs": [config.to_dict() for config in configs]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.post("/bot-config")
@login_required
def save_bot_config():
    """Save bot configuration"""
    try:
        if not current_app.mongodb:
            return jsonify({"error": "Database not available"}), 500
        
        data = request.get_json()
        config = BotConfig(
            user_id=current_user.user_id,
            symbol=data.get("symbol"),
            buy_threshold=float(data.get("buy_threshold")),
            sell_threshold=float(data.get("sell_threshold")),
            quantity=float(data.get("quantity")),
            is_active=data.get("is_active", False),
            dry_run=data.get("dry_run", True),
            bot_type=data.get("bot_type", "THRESHOLD")
        )
        
        config_id = current_app.mongodb.save_bot_config(config)
        
        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Bot configuration saved successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.delete("/bot-config/<symbol>")
@login_required
def delete_bot_config(symbol):
    """Delete bot configuration"""
    try:
        if not current_app.mongodb:
            return jsonify({"error": "Database not available"}), 500
        
        success = current_app.mongodb.delete_bot_config(current_user.user_id, symbol)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Bot configuration deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Bot configuration not found"
            }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.get("/check-auth")
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.user_id,
                'username': current_user.username,
                'email': current_user.email
            }
        })
    else:
        return jsonify({'authenticated': False}), 401
