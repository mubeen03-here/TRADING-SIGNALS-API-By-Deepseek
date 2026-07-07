import requests
import pandas as pd
import time
from datetime import datetime, timedelta

class DataFetcher:
    """Multi-asset data fetcher with fallback APIs"""
    
    TWELVE_DATA_API = "https://api.twelvedata.com"
    BINANCE_API = "https://api.binance.com/api/v3"
    ALPHA_VANTAGE_API = "https://www.alphavantage.co/query"  # Free, no key needed for demo
    
    @staticmethod
    def get_forex(symbol="USD/JPY", interval="5min", outputsize=100):
        """Get forex data from Twelve Data with fallback"""
        try:
            url = f"{DataFetcher.TWELVE_DATA_API}/time_series"
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": "demo"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if "values" in data and len(data["values"]) > 0:
                df = pd.DataFrame(data["values"])
                df = df.rename(columns={
                    "datetime": "timestamp",
                    "open": "open",
                    "high": "high", 
                    "low": "low",
                    "close": "close"
                })
                df["open"] = pd.to_numeric(df["open"])
                df["high"] = pd.to_numeric(df["high"])
                df["low"] = pd.to_numeric(df["low"])
                df["close"] = pd.to_numeric(df["close"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df
            return None
        except Exception as e:
            print(f"Forex fetch error: {e}")
            return None
    
    @staticmethod
    def get_crypto(symbol="BTCUSDT", interval="5m", limit=100):
        """Get crypto data from Binance public API"""
        try:
            url = f"{DataFetcher.BINANCE_API}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if not data or "code" in data:
                # Fallback: Twelve Data for crypto
                return DataFetcher.get_forex("BTC/USD", interval.replace("m", "min"), limit)
            
            df = pd.DataFrame(data, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
            ])
            df["open"] = pd.to_numeric(df["open"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])
            df["close"] = pd.to_numeric(df["close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
            return df[["timestamp", "open", "high", "low", "close"]]
        except Exception as e:
            print(f"Crypto fetch error: {e}")
            return None
    
    @staticmethod
    def get_gold(interval="5min", outputsize=100):
        """Get gold data with fallback"""
        try:
            # Try Twelve Data first
            return DataFetcher.get_forex("XAU/USD", interval, outputsize)
        except:
            # Fallback: generate synthetic data for demo (so app doesn't break)
            return DataFetcher._generate_demo_data("XAUUSD")
    
    @staticmethod
    def get_index(symbol="NDX", interval="5min", outputsize=100):
        """Get index data with fallback"""
        try:
            # Try Twelve Data
            return DataFetcher.get_forex(symbol, interval, outputsize)
        except:
            # Fallback: generate synthetic data
            return DataFetcher._generate_demo_data(symbol)
    
    @staticmethod
    def _generate_demo_data(pair):
        """Generate synthetic data for demo (when APIs fail)"""
        import numpy as np
        np.random.seed(42)
        
        timestamps = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        base_price = 1.0
        if pair == "XAUUSD":
            base_price = 2350
        elif pair == "BTCUSD":
            base_price = 62000
        elif pair == "NDX":
            base_price = 19800
        elif pair == "USDJPY":
            base_price = 160
        
        changes = np.random.randn(100) * 0.002
        prices = base_price * (1 + np.cumsum(changes))
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices * (1 - np.random.rand(100) * 0.001),
            'high': prices * (1 + np.random.rand(100) * 0.002),
            'low': prices * (1 - np.random.rand(100) * 0.002),
            'close': prices
        })
        return df
    
    @staticmethod
    def get_all_data(pair, interval="5min", limit=100):
        """Unified data fetcher with fallback support"""
        pair_map = {
            "USDJPY": ("USD/JPY", "forex"),
            "XAUUSD": ("XAU/USD", "gold"),
            "BTC": ("BTCUSDT", "crypto"),
            "NAS100": ("NDX", "index")
        }
        
        if pair not in pair_map:
            return None
        
        symbol, asset_type = pair_map[pair]
        
        try:
            if asset_type == "crypto":
                return DataFetcher.get_crypto(symbol, interval.replace("min", "m"), limit)
            elif asset_type == "gold":
                return DataFetcher.get_gold(interval, limit)
            elif asset_type == "index":
                return DataFetcher.get_index(symbol, interval, limit)
            else:
                return DataFetcher.get_forex(symbol, interval, limit)
        except:
            # Ultimate fallback: generate demo data
            return DataFetcher._generate_demo_data(pair)
