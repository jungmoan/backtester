# 🚀 Smart Backtester

**Professional Trading Strategy Backtesting Platform**

A powerful, web-based backtesting application built with Streamlit for testing trading strategies with real-time data visualization.

## ✨ Features

- 📊 **Interactive Web Interface**: Clean, professional UI with real-time controls
- 🎯 **Multiple Strategies**: Moving Average, RSI, Bollinger Bands, MACD, Stochastic
- 📈 **Advanced Charting**: Interactive candlestick charts with trading signals
- 📊 **Performance Analytics**: Comprehensive metrics and visualizations
- 💾 **Export Capabilities**: Download results as CSV files
- ⚡ **Real-time Data**: Live stock data from Yahoo Finance
- 🎨 **Responsive Design**: Works on desktop and mobile devices
- 🔧 **Modular Architecture**: Separate strategy and backtest engine modules

## 🏗️ Project Structure

```
backtester/
├── streamlit_app.py     # Main Streamlit application
├── strategies.py        # Trading strategy implementations
├── backtest_engine.py   # Backtesting and performance analysis engine
├── requirements.txt     # Python dependencies
├── start.sh            # Startup script
└── README.md           # Documentation
```

## 🚀 Quick Start

### Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

4. Open your browser to `http://localhost:8501`

## 🎯 How to Use

1. **Select Stock**: Choose from popular presets or enter any symbol
2. **Choose Strategy**: Pick from 5 available strategies
3. **Adjust Parameters**: Fine-tune strategy settings with sliders
4. **Set Capital**: Configure initial investment amount
5. **Run Backtest**: Click the "RUN BACKTEST" button
6. **Analyze Results**: View interactive charts and performance metrics

## 📊 Supported Strategies

### 1. Moving Average Cross
- **Short MA**: Fast moving average (5-50 periods)
- **Long MA**: Slow moving average (20-200 periods)
- **Signal**: Buy when short > long, sell when short < long

### 2. RSI (Relative Strength Index)
- **Period**: RSI calculation period (5-30)
- **Oversold**: Buy threshold (10-40)
- **Overbought**: Sell threshold (60-90)

### 3. Bollinger Bands
- **Period**: Moving average period (10-50)
- **Standard Deviation**: Band width multiplier (1.0-3.0)
- **Signal**: Buy at lower band, sell at upper band

### 4. MACD (Moving Average Convergence Divergence)
- **Fast EMA**: Fast exponential moving average (5-20)
- **Slow EMA**: Slow exponential moving average (20-50)
- **Signal EMA**: Signal line smoothing (5-15)
- **Signal**: Buy/sell on MACD line crosses

### 5. Stochastic Oscillator
- **K Period**: %K calculation period (5-20)
- **D Period**: %D smoothing period (1-10)
- **Oversold/Overbought**: Entry/exit thresholds

## 📈 Performance Metrics

### Basic Metrics
- **Total Return**: Overall portfolio performance
- **Annual Return**: Annualized return rate
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough decline
- **Volatility**: Portfolio return standard deviation

### Advanced Metrics
- **Sortino Ratio**: Downside deviation adjusted return
- **Calmar Ratio**: Return to max drawdown ratio
- **Profit/Loss Ratio**: Average win vs average loss
- **Value at Risk (VaR)**: Potential loss estimate
- **Trade Analysis**: Detailed transaction history

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Charting**: Plotly
- **Data**: Yahoo Finance (yfinance)
- **Analysis**: Pandas, NumPy
- **Architecture**: Modular design with separate strategy and engine modules

## 🏗️ Module Architecture

### strategies.py
- `BaseStrategy`: Abstract strategy interface
- `MovingAverageStrategy`, `RSIStrategy`, etc.: Individual strategy implementations
- `StrategyManager`: Strategy factory and coordinator

### backtest_engine.py
- `BacktestEngine`: Core backtesting logic and portfolio management
- `PortfolioAnalyzer`: Advanced performance analysis tools
- Comprehensive metrics calculation

### streamlit_app.py
- Main Streamlit application
- UI components and user interaction
- Integration of strategies and engine modules

## 🎨 Features in Detail

### Interactive Charts
- Candlestick price charts
- Volume indicators
- Strategy-specific overlays
- Buy/sell signal markers
- Zoom and pan capabilities

### Real-time Analysis
- Live data fetching
- Cached data for performance
- Responsive parameter updates
- Instant backtest execution

### Export & Reporting
- CSV trade history download
- Performance metrics export
- Professional report formatting

## 🔧 Configuration

All settings are available through the web interface:
- Stock symbol selection
- Time period configuration
- Strategy parameter tuning
- Capital allocation settings

## 🚀 Performance

- **Fast Execution**: Optimized for real-time interaction
- **Caching**: 5-minute data cache for improved speed
- **Responsive**: Immediate feedback on parameter changes
- **Scalable**: Handles various timeframes and data sizes

---

Built with ❤️ using Streamlit for professional trading analysis.

### 2. 간단한 예제 실행
```bash
python simple_example.py
```

### 3. 결과 분석 및 시각화
```bash
python analyze_results.py
```

## 주요 기능

### 📈 지원하는 전략
- **이동평균 교차 전략**: 단기/장기 이동평균선의 골든크로스/데드크로스
- **이동평균 추세 전략**: 가격이 상승추세 이동평균선 위에 있을 때 매수
- **RSI 전략**: 과매도/과매수 구간에서의 역추세 매매
- **RSI 평균회귀 전략**: 극단적 RSI 구간에서의 평균회귀 매매

### 📊 성과 분석 지표
- **수익률 지표**: 총수익률, 연환산수익률
- **리스크 지표**: 변동성, 샤프비율, 최대낙폭(MDD)
- **거래 지표**: 승률, 총거래횟수, 수익팩터
- **시각화**: 포트폴리오 성과 차트, 거래 분석, 전략 비교

### 💾 결과 저장
- CSV 형태로 상세한 결과 저장
- 포트폴리오 히스토리, 거래 내역, 성과 보고서
- PNG 형태의 차트 자동 생성

## 사용 예제

### 기본 사용법
```python
from strategies.moving_average import MovingAverageStrategy
from backtester.engine import BacktestEngine

# 전략 생성
strategy = MovingAverageStrategy(short_window=5, long_window=20)

# 백테스트 엔진 생성
engine = BacktestEngine(strategy, initial_capital=10_000_000)

# 백테스트 실행
results = engine.run_backtest(
    symbol='005930.KS',  # 삼성전자
    start_date='2023-01-01',
    end_date='2024-12-31'
)

# 결과 출력 및 저장
engine.print_results()
engine.save_results_to_csv("my_backtest")
```

### 커스텀 전략 만들기
```python
from strategies.base_strategy import BaseStrategy, SignalType

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Custom Strategy")
    
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = SignalType.HOLD
        
        # 여기에 매매 로직 구현
        # df.loc[buy_condition, 'signal'] = SignalType.BUY
        # df.loc[sell_condition, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self):
        return "내가 만든 커스텀 전략"
```

## 설정

`config/config.py`에서 백테스트 설정을 변경할 수 있습니다:

```python
class Config:
    INITIAL_CAPITAL = 10_000_000  # 초기 자본
    COMMISSION_RATE = 0.003       # 수수료율
    SLIPPAGE_RATE = 0.001         # 슬리피지
    POSITION_SIZE = 0.1           # 포지션 크기
    START_DATE = "2020-01-01"     # 기본 시작일
    END_DATE = "2024-12-31"       # 기본 종료일
```

## 지원하는 주식

### 한국 주식 (KRX)
- 삼성전자 (005930.KS)
- SK하이닉스 (000660.KS)
- NAVER (035420.KS)
- LG화학 (051910.KS)
- 삼성SDI (006400.KS)

### 미국 주식 (NYSE/NASDAQ)
- Apple (AAPL)
- Google (GOOGL)
- Microsoft (MSFT)
- Tesla (TSLA)
- NVIDIA (NVDA)

## 결과 파일 설명

백테스트 실행 후 `results/` 폴더에 다음 파일들이 생성됩니다:

- `*_portfolio.csv`: 일별 포트폴리오 가치 변화
- `*_trades.csv`: 상세한 거래 내역
- `*_report.csv`: 성과 지표 요약
- `*_positions.csv`: 최종 보유 포지션
- `*_chart.png`: 포트폴리오 성과 차트
- `*_analysis.png`: 거래 분석 차트
- `strategy_comparison.png`: 전략 비교 차트

## 개발자 정보

이 프로젝트는 주식 자동매매 시스템의 사전 검증을 위한 백테스팅 도구입니다.

## 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 사용되어야 합니다. 실제 투자 결정에 사용하기 전에 충분한 검토와 테스트를 수행하시기 바랍니다. 투자에는 항상 리스크가 따르며, 과거 성과가 미래 수익을 보장하지 않습니다.
