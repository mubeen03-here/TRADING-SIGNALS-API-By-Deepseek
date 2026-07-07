import requests
import pandas as pd
import time
from datetime import datetime, timedelta

class DataFetcher:
    """Multi-asset data fetcher using free APIs"""
    
    # Twelve Data - Free tier: 800 requests/day
    TWELVE_DATA_API = "https://api.twelvedata.com"
    
    # Binance Public API - No key required
    BINANCE_API = "https://api.binance.com/api/v3"
    
    # Metals-API - Free tier
    METALS_API = "https://api.metals-api.com/v1"
    
    @staticmethod
    def get_forex(symbol="USD/JPY", interval="5min", outputsize=100):
        """Get forex data from Twelve Data (free, no key needed for limited calls)"""
        try:
            # Twelve Data free endpoint
            url = f"{DataFetcher.TWELVE_DATA_API}/time_series"
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": "demo"  # Free demo key, 800 requests/day
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if "values" in data:
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
        """Get crypto data from Binance public API (no key required)"""
        try:
            url = f"{DataFetcher.BINANCE_API}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
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
        """Get gold (XAUUSD) data from free API"""
        try:
            # Using Twelve Data for XAU/USD
            return DataFetcher.get_forex("XAU/USD", interval, outputsize)
        except:
            # Fallback: Metals-API
            url = f"{DataFetcher.METALS_API}/latest"
            params = {
                "access_key": "demo",  # Free demo key
                "base": "USD",
                "symbols": "XAU"
            }
            response = requests.get(url, params=params, timeout=10)
            return None
    
    @staticmethod
    def get_index(symbol="NDX", interval="5min", outputsize=100):
        """Get index data (NAS100/NDX) from Twelve Data"""
        try:
            return DataFetcher.get_forex(symbol, interval, outputsize)
        except Exception as e:
            print(f"Index fetch error: {e}")
            return None

    @staticmethod
    def get_all_data(pair, interval="5min", limit=100):
        """Unified data fetcher for all pairs"""
        pair_map = {
            "USDJPY": ("USD/JPY", "forex"),
            "XAUUSD": ("XAU/USD", "gold"),
            "BTC": ("BTCUSDT", "crypto"),
            "NAS100": ("NDX", "index")
        }
        
        if pair not in pair_map:
            return None
        
        symbol, asset_type = pair_map[pair]
        
        if asset_type == "crypto":
            return DataFetcher.get_crypto(symbol, interval.replace("min", "m"), limit)
        elif asset_type == "gold":
            return DataFetcher.get_gold(interval, limit)
        else:
            return DataFetcher.get_forex(symbol, interval, limit)
