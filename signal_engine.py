import pandas as pd
import numpy as np
from datetime import datetime

class SignalEngine:
    """Professional multi-timeframe signal generator with fake breakout detection"""
    
    @staticmethod
    def calculate_indicators(df):
        """Calculate all technical indicators"""
        if df is None or len(df) < 20:
            return None
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        open_p = df['open'].values
        
        # --- RSI (14) ---
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(14).mean().values
        avg_loss = pd.Series(loss).rolling(14).mean().values
        rs = avg_gain / (avg_loss + 0.0001)
        rsi = 100 - (100 / (1 + rs))
        
        # --- MACD (12, 26, 9) ---
        ema12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
        ema26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
        macd = ema12 - ema26
        signal_line = pd.Series(macd).ewm(span=9, adjust=False).mean().values
        macd_hist = macd - signal_line
        
        # --- Bollinger Bands (20, 2) ---
        sma20 = pd.Series(close).rolling(20).mean().values
        std20 = pd.Series(close).rolling(20).std().values
        upper_band = sma20 + (2 * std20)
        lower_band = sma20 - (2 * std20)
        
        # --- EMA 9 & 21 ---
        ema9 = pd.Series(close).ewm(span=9, adjust=False).mean().values
        ema21 = pd.Series(close).ewm(span=21, adjust=False).mean().values
        
        # --- ADX (Average Directional Index) ---
        # Simplified ADX calculation
        tr = np.maximum(high - low, np.maximum(abs(high - np.roll(close, 1)), abs(low - np.roll(close, 1))))
        atr = pd.Series(tr).rolling(14).mean().values
        
        # --- Stochastic RSI ---
        rsi_min = pd.Series(rsi).rolling(14).min().values
        rsi_max = pd.Series(rsi).rolling(14).max().values
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min + 0.0001) * 100
        
        # --- Volume (if available) ---
        volume = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
        
        return {
            'rsi': rsi,
            'macd': macd,
            'macd_signal': signal_line,
            'macd_hist': macd_hist,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'sma20': sma20,
            'ema9': ema9,
            'ema21': ema21,
            'atr': atr,
            'stoch_rsi': stoch_rsi,
            'volume': volume,
            'close': close,
            'high': high,
            'low': low,
            'open': open_p
        }
    
    @staticmethod
    def detect_candlestick_patterns(df):
        """Detect key candlestick patterns"""
        patterns = []
        if len(df) < 3:
            return patterns
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        body = abs(last['close'] - last['open'])
        upper_wick = last['high'] - max(last['close'], last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        
        # Doji
        if body < (last['high'] - last['low']) * 0.1:
            patterns.append("DOJI")
        
        # Hammer / Shooting Star
        if body > 0 and lower_wick > body * 2 and upper_wick < body * 0.5:
            patterns.append("HAMMER")
        if body > 0 and upper_wick > body * 2 and lower_wick < body * 0.5:
            patterns.append("SHOOTING_STAR")
        
        # Engulfing
        if last['close'] > last['open'] and prev['close'] < prev['open']:
            if last['close'] > prev['open'] and last['open'] < prev['close']:
                patterns.append("BULLISH_ENGULFING")
        if last['close'] < last['open'] and prev['close'] > prev['open']:
            if last['close'] < prev['open'] and last['open'] > prev['close']:
                patterns.append("BEARISH_ENGULFING")
        
        return patterns
    
    @staticmethod
    def detect_fake_breakout(df, indicators):
        """Detect fake breakouts to avoid false signals"""
        if len(df) < 20:
            return False
        
        close = indicators['close']
        upper = indicators['upper_band']
        lower = indicators['lower_band']
        sma = indicators['sma20']
        
        last_close = close[-1]
        prev_close = close[-2]
        
        # Fake breakout: price breaks above upper band but closes back inside
        if prev_close > upper[-2] and last_close < upper[-1]:
            return True, "FAKE_BREAKOUT_ABOVE"
        
        # Fake breakdown: price breaks below lower band but closes back inside
        if prev_close < lower[-2] and last_close > lower[-1]:
            return True, "FAKE_BREAKOUT_BELOW"
        
        return False, None
    
    @staticmethod
    def generate_signal(df, timeframe="5min"):
        """Generate comprehensive trading signal"""
        if df is None or len(df) < 30:
            return {
                'signal': 'HOLD',
                'strength': 'LOW',
                'confidence': 0,
                'entry': None,
                'stop_loss': None,
                'take_profit': None,
                'reason': 'Insufficient data',
                'patterns': [],
                'next_candle': None,
                'fake_breakout': False
            }
        
        indicators = SignalEngine.calculate_indicators(df)
        if indicators is None:
            return None
        
        close = indicators['close']
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_hist = indicators['macd_hist']
        upper = indicators['upper_band']
        lower = indicators['lower_band']
        ema9 = indicators['ema9']
        ema21 = indicators['ema21']
        stoch_rsi = indicators['stoch_rsi']
        atr = indicators['atr']
        
        # Detect patterns
        patterns = SignalEngine.detect_candlestick_patterns(df)
        
        # Detect fake breakouts
        is_fake, fake_type = SignalEngine.detect_fake_breakout(df, indicators)
        
        # --- SIGNAL LOGIC ---
        buy_signals = 0
        sell_signals = 0
        total_signals = 0
        reasons = []
        
        last_rsi = rsi[-1] if not np.isnan(rsi[-1]) else 50
        last_macd = macd[-1] if not np.isnan(macd[-1]) else 0
        last_macd_signal = macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0
        last_macd_hist = macd_hist[-1] if not np.isnan(macd_hist[-1]) else 0
        last_close = close[-1]
        last_ema9 = ema9[-1] if not np.isnan(ema9[-1]) else last_close
        last_ema21 = ema21[-1] if not np.isnan(ema21[-1]) else last_close
        last_stoch = stoch_rsi[-1] if not np.isnan(stoch_rsi[-1]) else 50
        last_atr = atr[-1] if not np.isnan(atr[-1]) else 0
        
        # --- RSI ---
        if last_rsi < 30:
            buy_signals += 2
            reasons.append(f"RSI oversold ({last_rsi:.1f})")
        elif last_rsi > 70:
            sell_signals += 2
            reasons.append(f"RSI overbought ({last_rsi:.1f})")
        elif last_rsi < 45:
            buy_signals += 1
        elif last_rsi > 55:
            sell_signals += 1
        
        # --- MACD ---
        if last_macd > last_macd_signal and last_macd_hist > 0:
            buy_signals += 2
            reasons.append("MACD bullish crossover")
        elif last_macd < last_macd_signal and last_macd_hist < 0:
            sell_signals += 2
            reasons.append("MACD bearish crossover")
        elif last_macd > last_macd_signal:
            buy_signals += 1
        elif last_macd < last_macd_signal:
            sell_signals += 1
        
        # --- EMA Crossover ---
        if last_ema9 > last_ema21:
            buy_signals += 1
            reasons.append("EMA9 above EMA21")
        elif last_ema9 < last_ema21:
            sell_signals += 1
            reasons.append("EMA9 below EMA21")
        
        # --- Bollinger Bands ---
        if last_close < lower[-1] * 1.02:
            buy_signals += 1
            reasons.append("Price near lower BB")
        elif last_close > upper[-1] * 0.98:
            sell_signals += 1
            reasons.append("Price near upper BB")
        
        # --- Stochastic RSI ---
        if last_stoch < 20:
            buy_signals += 1
        elif last_stoch > 80:
            sell_signals += 1
        
        # --- Candlestick Patterns ---
        if "BULLISH_ENGULFING" in patterns:
            buy_signals += 2
            reasons.append("Bullish engulfing pattern")
        if "BEARISH_ENGULFING" in patterns:
            sell_signals += 2
            reasons.append("Bearish engulfing pattern")
        if "HAMMER" in patterns:
            buy_signals += 1
            reasons.append("Hammer pattern")
        if "SHOOTING_STAR" in patterns:
            sell_signals += 1
            reasons.append("Shooting star pattern")
        
        # --- Fake Breakout Filter ---
        if is_fake:
            reasons.append(f"⚠️ FAKE BREAKOUT detected: {fake_type}")
            # Reduce signal strength
            buy_signals = max(0, buy_signals - 2)
            sell_signals = max(0, sell_signals - 2)
        
        # --- FINAL SIGNAL ---
        total_signals = buy_signals + sell_signals
        
        if total_signals < 3:
            signal = "HOLD"
            strength = "LOW"
            confidence = 20 + (total_signals * 10)
        elif buy_signals > sell_signals and buy_signals >= 3:
            signal = "STRONG_BUY" if buy_signals >= 5 else "BUY"
            strength = "HIGH" if buy_signals >= 5 else "MEDIUM"
            confidence = min(95, 50 + (buy_signals * 8))
        elif sell_signals > buy_signals and sell_signals >= 3:
            signal = "STRONG_SELL" if sell_signals >= 5 else "SELL"
            strength = "HIGH" if sell_signals >= 5 else "MEDIUM"
            confidence = min(95, 50 + (sell_signals * 8))
        else:
            signal = "HOLD"
            strength = "LOW"
            confidence = 30
        
        # --- Entry, Stop Loss, Take Profit ---
        entry = last_close
        if last_atr > 0:
            stop_loss = entry - (last_atr * 1.5) if signal in ["BUY", "STRONG_BUY"] else entry + (last_atr * 1.5)
            take_profit = entry + (last_atr * 2.5) if signal in ["BUY", "STRONG_BUY"] else entry - (last_atr * 2.5)
        else:
            stop_loss = entry * 0.98 if signal in ["BUY", "STRONG_BUY"] else entry * 1.02
            take_profit = entry * 1.05 if signal in ["BUY", "STRONG_BUY"] else entry * 0.95
        
        # --- Next Candle Prediction ---
        next_candle = SignalEngine.predict_next_candle(df, indicators)
        
        # --- Fake Breakout Alert ---
        fake_alert = None
        if is_fake:
            fake_alert = f"⚠️ FAKE BREAKOUT: {fake_type} - Avoid trading this level!"
        
        return {
            'signal': signal,
            'strength': strength,
            'confidence': round(confidence, 1),
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'take_profit': round(take_profit, 4),
            'reason': ' | '.join(reasons[:5]) if reasons else 'No clear signal',
            'patterns': patterns,
            'next_candle': next_candle,
            'fake_breakout': is_fake,
            'fake_alert': fake_alert,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': total_signals
        }
    
    @staticmethod
    def predict_next_candle(df, indicators):
        """Predict next candle color and probability"""
        if len(df) < 10:
            return {'color': 'NEUTRAL', 'probability': 50, 'reason': 'Insufficient data'}
        
        close = indicators['close']
        open_p = indicators['open']
        rsi = indicators['rsi']
        macd_hist = indicators['macd_hist']
        
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # Check if current candle is bullish or bearish
        current_bullish = last_candle['close'] > last_candle['open']
        prev_bullish = prev_candle['close'] > prev_candle['open']
        
        score = 50  # Neutral base
        
        # RSI influence
        if rsi[-1] < 30:
            score += 15  # Oversold -> bullish bias
        elif rsi[-1] > 70:
            score -= 15  # Overbought -> bearish bias
        
        # MACD influence
        if macd_hist[-1] > 0 and macd_hist[-1] > macd_hist[-2]:
            score += 10
        elif macd_hist[-1] < 0 and macd_hist[-1] < macd_hist[-2]:
            score -= 10
        
        # Momentum
        if current_bullish and prev_bullish:
            score += 5
        elif not current_bullish and not prev_bullish:
            score -= 5
        
        # Final prediction
        if score >= 60:
            color = "GREEN (Bullish)"
            prob = min(85, score + 10)
            reason = "Bullish momentum building"
        elif score <= 40:
            color = "RED (Bearish)"
            prob = min(85, 100 - score + 10)
            reason = "Bearish momentum building"
        else:
            color = "NEUTRAL (Doji/Indecision)"
            prob = 50
            reason = "Mixed signals, wait for confirmation"
        
        return {
            'color': color,
            'probability': round(min(prob, 90), 1),
            'reason': reason,
            'score': score
      }
