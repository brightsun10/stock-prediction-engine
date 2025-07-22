import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index with consistent length."""
    deltas = np.diff(prices, prepend=prices[0])  # Prepend to maintain length
    gains = deltas.clip(min=0)
    losses = -deltas.clip(max=0)
    avg_gain = pd.Series(gains).rolling(window=period).mean().fillna(0)
    avg_loss = pd.Series(losses).rolling(window=period).mean().fillna(0)
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def generate_stock_data(n_samples=10000, stock_symbol='AAPL'):
    """Generate realistic stock market data with OHLC."""
    np.random.seed(42)
    timestamps = pd.date_range(start='2025-01-01', periods=n_samples, freq='min')
    # Simulate close prices using Geometric Brownian Motion
    mu, sigma = 0.0001, 0.01
    close_prices = [100.0]
    for _ in range(n_samples - 1):
        drift = mu - 0.5 * sigma**2
        shock = np.random.normal(0, sigma)
        close_prices.append(close_prices[-1] * np.exp(drift + shock))
    close_prices = np.array(close_prices)
    # Simulate OHLC
    open_prices = np.roll(close_prices, 1) * np.random.uniform(0.99, 1.01, n_samples)
    open_prices[0] = close_prices[0]
    high_prices = np.maximum(close_prices, open_prices) * np.random.uniform(1.0, 1.02, n_samples)
    low_prices = np.minimum(close_prices, open_prices) * np.random.uniform(0.98, 1.0, n_samples)
    volumes = np.random.randint(1000, 20000, n_samples)
    returns = np.diff(close_prices, prepend=close_prices[0]) / close_prices
    volatility = pd.Series(close_prices).rolling(window=5).std().fillna(0).values
    bid_prices = close_prices * np.random.uniform(0.98, 0.99, n_samples)
    ask_prices = close_prices * np.random.uniform(1.01, 1.02, n_samples)
    rsi = calculate_rsi(close_prices)
    ma_5 = pd.Series(close_prices).rolling(window=5).mean().fillna(close_prices[0]).values
    market_sentiment = np.random.uniform(-1, 1, n_samples)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'stock_symbol': stock_symbol,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes,
        'returns': returns,
        'volatility': volatility,
        'bid_price': bid_prices,
        'ask_price': ask_prices,
        'rsi': rsi,
        'ma_5': ma_5,
        'market_sentiment': market_sentiment
    })
    return df

def train_model():
    """Train and save Random Forest model."""
    df = generate_stock_data()
    features = ['open', 'high', 'low', 'volume', 'returns', 'volatility', 'bid_price', 'ask_price', 'rsi', 'ma_5', 'market_sentiment']
    X = df[features]
    y = df['close'].shift(-1).fillna(method='ffill')  # Predict next close price
    split = int(0.8 * len(df))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred) / y_test.mean() * 100
    logger.info(f"Test MAE: {mae:.2f}%")
    
    joblib.dump(model, 'models/stock_model.pkl')
    logger.info("Model saved to models/stock_model.pkl")

if __name__ == "__main__":
    train_model()