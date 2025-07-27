import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import os

def plot_trade_signals(symbol: str, start_date: str, end_date: str, trades_file: str, save_path: str = None):
    """
    Visualize buy/sell points on the price chart and save as image (no plt.show)
    """
    # 1. Load price data
    ticker = yf.Ticker(symbol)
    price_df = ticker.history(start=start_date, end=end_date)
    if price_df.empty:
        print(f"No data for {symbol}.")
        return
    price_df.index = pd.to_datetime(price_df.index)

    # 2. Load trade history
    trades = pd.read_csv(trades_file, parse_dates=['date'])

    # 3. Extract buy/sell points
    buy_trades = trades[trades['action'] == 'BUY']
    sell_trades = trades[trades['action'] == 'SELL']

    # 4. Try to extract strategy name from file path or trades_file
    strategy_name = None
    if 'Strategy_' in trades_file:
        # e.g. ..._Moving_Average_Strategy_20250726_151538_trades.csv
        base = os.path.basename(trades_file)
        parts = base.split('_')
        try:
            idx = parts.index('Strategy')
            strategy_name = '_'.join(parts[idx-1:idx+2])
        except Exception as e:
            import traceback
            print(f"전략명 파싱 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
            strategy_name = None
    if not strategy_name:
        # fallback: use part before _trades.csv
        strategy_name = os.path.basename(trades_file).replace('_trades.csv','')

    # 5. Draw chart
    plt.figure(figsize=(16, 8))
    plt.plot(price_df.index, price_df['Close'], label='Close Price', color='black', linewidth=2)
    plt.scatter(buy_trades['date'], buy_trades['price'], marker='^', color='green', s=120, label='Buy', zorder=5)
    plt.scatter(sell_trades['date'], sell_trades['price'], marker='v', color='red', s=120, label='Sell', zorder=5)

    # English title with strategy name
    plt.title(f"{symbol} Price & Trade Points ({start_date} ~ {end_date})\nStrategy: {strategy_name}", fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Price (KRW)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save only, do not show
    if save_path is None:
        save_path = f"results/{symbol}_trade_chart.png"
    plt.savefig(save_path, dpi=300)
    print(f"Chart saved: {save_path}")
