import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class DataFetcher:
    """Multi-asset data fetcher with fallback and dummy data generator"""
    
    TWELVE_DATA_API = "https://api.twelvedata.com"
    BINANCE_API = "https://api.binance.com/api/v3"
    
    @staticmethod
    def get_forex(symbol="USD/JPY", interval="5min", outputsize=100):
        """Get forex data from Twelve Data"""
        try:
            url = f"{DataFetcher.TWELVE_DATA_API}/time_series"
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": "04686c9409744e3d8453e3a371796a3c"
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
        """Get crypto data from Binance with fallback"""
        try:
            url = f"{DataFetcher.BINANCE_API}/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
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
            return None
        except Exception as e:
            print(f"Crypto fetch error: {e}")
            return None
    
    @staticmethod
    def generate_dummy_data(pair, base_price=100, volatility=0.01, periods=100):
        """Generate realistic dummy data when APIs fail"""
        np.random.seed(hash(pair) % 2**32)
        
        timestamps = pd.date_range(end=datetime.now(), periods=periods, freq='5min')
        
        # Base prices for different assets
        if pair == "XAUUSD":
            base_price = 2350 + random.randint(-50, 50)
            volatility = 0.005
        elif pair == "BTC":
            base_price = 62000 + random.randint(-3000, 3000)
            volatility = 0.015
        elif pair == "NAS100":
            base_price = 19800 + random.randint(-200, 200)
            volatility = 0.008
        elif pair == "USDJPY":
            base_price = 160 + random.randint(-5, 5)
            volatility = 0.002
        
        # Generate price movements
        returns = np.random.randn(periods) * volatility
        prices = base_price * (1 + np.cumsum(returns))
        prices = np.maximum(prices, base_price * 0.95)  # Prevent negative prices
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices * (1 + np.random.randn(periods) * volatility * 0.3),
            'high': prices * (1 + np.abs(np.random.randn(periods)) * volatility * 0.5),
            'low': prices * (1 - np.abs(np.random.randn(periods)) * volatility * 0.5),
            'close': prices
        })
        
        # Ensure high >= low and open/close within range
        df['high'] = df[['high', 'open', 'close']].max(axis=1)
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        return df
    
    @staticmethod
    def get_all_data(pair, interval="5min", limit=100):
        """Unified data fetcher with automatic fallback to dummy data"""
        
        # Map pairs to their symbols
        pair_map = {
            "USDJPY": {"api_symbol": "USD/JPY", "type": "forex", "base_price": 160},
            "XAUUSD": {"api_symbol": "XAU/USD", "type": "forex", "base_price": 2350},
            "BTC": {"api_symbol": "BTCUSDT", "type": "crypto", "base_price": 62000},
            "NAS100": {"api_symbol": "NDX", "type": "forex", "base_price": 19800}
        }
        
        if pair not in pair_map:
            return None
        
        config = pair_map[pair]
        interval_min = interval.replace("min", "m") if "min" in interval else interval
        
        # Try to fetch real data
        df = None
        try:
            if config["type"] == "crypto":
                df = DataFetcher.get_crypto(config["api_symbol"], interval_min, limit)
            else:
                df = DataFetcher.get_forex(config["api_symbol"], interval, limit)
            
            # Check if we got valid data
            if df is not None and len(df) >= 10:
                return df
        except Exception as e:
            print(f"Fetch failed for {pair}: {e}")
        
        # If real data failed, generate dummy data
        print(f"Using dummy data for {pair}")
        return DataFetcher.generate_dummy_data(pair, config["base_price"], periods=limit)
