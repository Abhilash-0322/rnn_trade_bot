import csv
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class PriceStorage:
    def __init__(self, data_dir: str = "data", binance_client=None, db=None):
        self.data_dir = data_dir
        self.binance = binance_client
        self.db = db
        os.makedirs(data_dir, exist_ok=True)
        
    def _get_file_path(self, symbol: str) -> str:
        """Get CSV file path for a symbol"""
        return os.path.join(self.data_dir, f"{symbol.lower()}_prices.csv")
    
    def save_price(self, symbol: str, price: float, timestamp: Optional[int] = None) -> None:
        """Save a single price point to CSV and MongoDB (if available)."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
            
        file_path = self._get_file_path(symbol)
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['timestamp', 'price', 'datetime'])
            
            dt = datetime.fromtimestamp(timestamp / 1000)
            writer.writerow([timestamp, price, dt.isoformat()])

        # Also write to MongoDB if available
        if self.db and getattr(self.db, 'prices', None) is not None:
            try:
                self.db.save_price_point(symbol, price, timestamp)
            except Exception as e:
                # Keep CSV as source of truth if DB write fails
                print(f"Warning: failed to save price to MongoDB for {symbol}: {e}")
    
    def fetch_historical_data(self, symbol: str, period: str = "1d") -> List[Dict[str, Any]]:
        """Fetch historical data from Binance API"""
        if not self.binance:
            return []
        
        try:
            # Calculate time range
            now = datetime.now()
            if period == "1h":
                start_time = now - timedelta(hours=1)
                interval = "1m"
            elif period == "1d":
                start_time = now - timedelta(days=1)
                interval = "5m"
            elif period == "3d":
                start_time = now - timedelta(days=3)
                interval = "15m"
            elif period == "1w":
                start_time = now - timedelta(weeks=1)
                interval = "1h"
            elif period == "1m":
                start_time = now - timedelta(days=30)
                interval = "4h"
            else:
                start_time = now - timedelta(days=1)
                interval = "5m"
            
            start_timestamp = int(start_time.timestamp() * 1000)
            
            # Fetch klines/candlestick data from Binance
            klines = self.binance.client.klines(
                symbol=symbol,
                interval=interval,
                startTime=start_timestamp,
                limit=1000
            )
            
            data = []
            for kline in klines:
                timestamp = int(kline[0])  # Open time
                price = float(kline[4])    # Close price
                dt = datetime.fromtimestamp(timestamp / 1000)
                
                data.append({
                    'timestamp': timestamp,
                    'price': price,
                    'datetime': dt.isoformat()
                })
            
            return data
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    def get_price_history(self, symbol: str, period: str = "1d") -> List[Dict[str, Any]]:
        """Get price history combining local storage and Binance API"""
        # First try to get data from local storage
        local_data = self._get_local_price_history(symbol, period)
        
        # If we have enough local data, return it
        if len(local_data) > 10:
            return local_data
        
        # Otherwise, fetch from Binance API and merge
        api_data = self.fetch_historical_data(symbol, period)
        
        if api_data:
            # Merge API data with local data, avoiding duplicates
            all_data = {}
            
            # Add local data
            for item in local_data:
                all_data[item['timestamp']] = item
            
            # Add API data (overwrite if newer)
            for item in api_data:
                all_data[item['timestamp']] = item
            
            # Convert back to list and sort by timestamp
            merged_data = list(all_data.values())
            merged_data.sort(key=lambda x: x['timestamp'])
            
            return merged_data
        
        return local_data
    
    def _get_local_price_history(self, symbol: str, period: str = "1d") -> List[Dict[str, Any]]:
        """Get price history from local CSV storage and merge with MongoDB points."""
        file_path = self._get_file_path(symbol)
        if not os.path.exists(file_path):
            return []
        
        # Calculate time range
        now = datetime.now()
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "1d":
            start_time = now - timedelta(days=1)
        elif period == "3d":
            start_time = now - timedelta(days=3)
        elif period == "1w":
            start_time = now - timedelta(weeks=1)
        elif period == "1m":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        start_timestamp = int(start_time.timestamp() * 1000)
        
        # Read CSV and filter by time
        data = []
        try:
            df = pd.read_csv(file_path)
            df = df[df['timestamp'] >= start_timestamp]
            
            for _, row in df.iterrows():
                data.append({
                    'timestamp': int(row['timestamp']),
                    'price': float(row['price']),
                    'datetime': row['datetime']
                })
        except Exception as e:
            print(f"Error reading price data: {e}")

        # Merge with MongoDB ticks if available
        if self.db and getattr(self.db, 'prices', None) is not None:
            try:
                db_points = self.db.get_price_points_since(symbol, start_timestamp)
                # Index existing by timestamp to dedupe
                existing = {item['timestamp']: item for item in data}
                for p in db_points:
                    ts = int(p['timestamp'])
                    if ts not in existing:
                        existing[ts] = {
                            'timestamp': ts,
                            'price': float(p['price']),
                            'datetime': datetime.fromtimestamp(ts / 1000).isoformat()
                        }
                merged = list(existing.values())
                merged.sort(key=lambda x: x['timestamp'])
                return merged
            except Exception as e:
                print(f"Warning: failed to merge MongoDB price points for {symbol}: {e}")

        return data
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the most recent price for a symbol"""
        file_path = self._get_file_path(symbol)
        if not os.path.exists(file_path):
            return None
        
        try:
            df = pd.read_csv(file_path)
            if len(df) > 0:
                return float(df.iloc[-1]['price'])
        except Exception as e:
            print(f"Error reading latest price: {e}")
        
        return None
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Remove price data older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = int(cutoff_time.timestamp() * 1000)
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_prices.csv'):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    df = df[df['timestamp'] >= cutoff_timestamp]
                    df.to_csv(file_path, index=False)
                except Exception as e:
                    print(f"Error cleaning up {filename}: {e}")
