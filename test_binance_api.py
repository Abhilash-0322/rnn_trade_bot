#!/usr/bin/env python3
"""
Standalone Binance Testnet API test script
"""
import os
import sys
from dotenv import load_dotenv
from binance.spot import Spot

load_dotenv()

def test_binance_api():
    print("🔍 Testing Binance Testnet API...")
    
    # Get credentials from env
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    base_url = os.getenv("BINANCE_BASE_URL", "https://testnet.binance.vision")
    
    if not api_key or not api_secret:
        print("❌ Missing API credentials in .env file")
        print("   Please set BINANCE_API_KEY and BINANCE_API_SECRET")
        return False
    
    try:
        # Initialize client
        client = Spot(api_key=api_key, api_secret=api_secret, base_url=base_url)
        print(f"✅ Connected to {base_url}")
        
        # Test 1: Get account info
        print("\n📊 Testing account info...")
        account = client.account()
        print(f"   Account status: {account.get('status', 'unknown')}")
        print(f"   Maker commission: {account.get('makerCommission', 'unknown')}")
        print(f"   Taker commission: {account.get('takerCommission', 'unknown')}")
        
        # Test 2: Get balances
        print("\n💰 Testing balances...")
        balances = account.get('balances', [])
        non_zero = [b for b in balances if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0]
        print(f"   Found {len(non_zero)} non-zero balances:")
        for balance in non_zero[:5]:  # Show first 5
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            print(f"     {asset}: {free} (free), {locked} (locked)")
        
        # Test 3: Get current prices
        print("\n📈 Testing price data...")
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for symbol in symbols:
            try:
                ticker = client.ticker_price(symbol=symbol)
                price = float(ticker['price'])
                print(f"   {symbol}: ${price:,.2f}")
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        # Test 4: Test order placement (dry run)
        print("\n🛒 Testing order placement (dry run)...")
        try:
            # This should fail gracefully in testnet without proper setup
            test_order = client.new_order(
                symbol="ETHUSDT",
                side="BUY",
                type="MARKET",
                quantity="0.001",
                test=True  # Test order
            )
            print("   ✅ Test order placement works")
        except Exception as e:
            print(f"   ⚠️  Order test: {e}")
            print("   (This is normal for testnet without proper account setup)")
        
        print("\n✅ Binance API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_binance_api()
    sys.exit(0 if success else 1)
