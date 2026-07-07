from flask import Flask, render_template, request, jsonify
from data_fetcher import DataFetcher
from signal import SignalEngine
import json
from datetime import datetime

app = Flask(__name__)

# Cache for data to reduce API calls
cache = {}
CACHE_DURATION = 60  # seconds

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/signal/<pair>/<timeframe>')
def get_signal(pair, timeframe):
    """Get real-time signal for a specific pair and timeframe"""
    
    # Validate inputs
    valid_pairs = ['USDJPY', 'XAUUSD', 'BTC', 'NAS100']
    valid_timeframes = ['5min', '15min', '30min']
    
    if pair not in valid_pairs:
        return jsonify({'error': f'Invalid pair. Use: {valid_pairs}'}), 400
    if timeframe not in valid_timeframes:
        return jsonify({'error': f'Invalid timeframe. Use: {valid_timeframes}'}), 400
    
    # Check cache
    cache_key = f"{pair}_{timeframe}"
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if (datetime.now() - timestamp).total_seconds() < CACHE_DURATION:
            return jsonify(cached_data)
    
    # Fetch data
    df = DataFetcher.get_all_data(pair, timeframe, limit=100)
    
    if df is None or len(df) < 30:
        return jsonify({
            'error': 'Unable to fetch data. Please try again.',
            'pair': pair,
            'timeframe': timeframe
        }), 503
    
    # Generate signal
    signal_engine = SignalEngine()
    signal = signal_engine.generate_signal(df, timeframe)
    
    if signal is None:
        return jsonify({'error': 'Signal generation failed'}), 500
    
    # Prepare response
    response = {
        'pair': pair,
        'timeframe': timeframe,
        'timestamp': datetime.now().isoformat(),
        'signal': signal['signal'],
        'strength': signal['strength'],
        'confidence': signal['confidence'],
        'entry': signal['entry'],
        'stop_loss': signal['stop_loss'],
        'take_profit': signal['take_profit'],
        'reason': signal['reason'],
        'patterns': signal['patterns'],
        'next_candle': signal['next_candle'],
        'fake_breakout': signal['fake_breakout'],
        'fake_alert': signal['fake_alert'],
        'stats': {
            'last_close': round(df['close'].iloc[-1], 4),
            'high_24h': round(df['high'].max(), 4),
            'low_24h': round(df['low'].min(), 4),
            'change': round(((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]) * 100, 2) if len(df) >= 5 else 0,
            'volume': int(df['volume'].sum()) if 'volume' in df.columns else None
        }
    }
    
    # Cache response
    cache[cache_key] = (response, datetime.now())
    
    return jsonify(response)

@app.route('/api/signals/all')
def get_all_signals():
    """Get signals for all pairs on default timeframe"""
    pairs = ['USDJPY', 'XAUUSD', 'BTC', 'NAS100']
    timeframe = '15min'
    
    results = {}
    for pair in pairs:
        try:
            df = DataFetcher.get_all_data(pair, timeframe, limit=100)
            if df is not None and len(df) >= 30:
                signal = SignalEngine.generate_signal(df, timeframe)
                if signal:
                    results[pair] = {
                        'signal': signal['signal'],
                        'strength': signal['strength'],
                        'confidence': signal['confidence'],
                        'entry': signal['entry'],
                        'reason': signal['reason'],
                        'next_candle': signal['next_candle']
                    }
        except Exception as e:
            results[pair] = {'error': str(e)}
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'timeframe': timeframe,
        'signals': results
    })

@app.route('/api/price/<pair>')
def get_price(pair):
    """Get current price for a pair"""
    valid_pairs = ['USDJPY', 'XAUUSD', 'BTC', 'NAS100']
    if pair not in valid_pairs:
        return jsonify({'error': 'Invalid pair'}), 400
    
    df = DataFetcher.get_all_data(pair, '5min', limit=5)
    if df is None or len(df) == 0:
        return jsonify({'error': 'Unable to fetch price'}), 503
    
    return jsonify({
        'pair': pair,
        'price': round(df['close'].iloc[-1], 4),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
