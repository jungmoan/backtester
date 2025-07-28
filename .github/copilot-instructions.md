# Copilot Instructions for Smart Backtester

## Project Overview
This is a professional trading strategy backtesting platform built with Streamlit. The system allows users to test various technical analysis strategies against historical stock data with real-time visualization and comprehensive performance analytics.

## Architecture & Core Components

### 3-Layer Modular Design
- **`streamlit_app.py`**: Web interface layer with Plotly charts and user controls
- **`strategies.py`**: Strategy layer with `BaseStrategy` abstract class and 6 concrete implementations
- **`backtest_engine.py`**: Core engine with `BacktestEngine` and `PortfolioAnalyzer` classes

### Key Patterns

#### Strategy Implementation Pattern
All strategies inherit from `BaseStrategy` and follow this pattern:
```python
class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Strategy Name")
    
    def calculate_signals(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = self._init_signal_columns(data.copy())
        current_position = 0
        
        for i in range(len(df)):
            # Strategy logic here
            if buy_condition:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
            elif sell_condition:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        return self._finalize_signals(df)
```

#### Signal Column Convention
- `Signal`: 1 (buy), -1 (sell), 0 (hold)
- `Position`: Current position state (0 or 1)
- `Position_Change`: Signal differences for trade detection

#### Streamlit State Management
Use `@st.cache_data(ttl=300)` for data loading with 5-minute cache:
```python
@st.cache_data(ttl=300)
def load_stock_data(symbol: str, period: str) -> pd.DataFrame:
    # Returns weekend-filtered data
```

## Critical Technical Details

### pandas-ta Integration
- **Squeeze Momentum**: Uses `ta.sma()`, `ta.stdev()`, `ta.true_range()`, `ta.linreg()` for LazyBear TradingView accuracy
- **Column naming**: Always map pandas-ta outputs to standardized names (e.g., `BBU_LB` → `BB_Upper`)

### Chart Visualization Pattern
```python
# Always filter weekends for cleaner charts
clean_data = data[data.index.weekday < 5]

# Use subplot pattern for indicators
fig = make_subplots(rows=3, cols=1, shared_xaxis=True, 
                   row_heights=[0.6, 0.2, 0.2])

# Add squeeze visualization with grouped background regions
squeeze_periods = get_squeeze_periods(data['SQZ_ON'])
for period in squeeze_periods:
    fig.add_shape(type="rect", fillcolor="rgba(255,0,0,0.1)", ...)
```

### Portfolio Management
- **Position tracking**: Single position (0 or 1), no partial positions
- **Stop loss**: Counts as losses in win rate calculation (`STOP_LOSS` in sell_trades array)
- **Trade validation**: Always validate trades with `validate_trades()` method

## Development Workflows

### Adding New Strategies
1. Inherit from `BaseStrategy` in `strategies.py`
2. Implement `calculate_signals()` with pandas operations
3. Add to `StrategyManager.strategies` dict
4. Add description in `streamlit_app.py` `get_strategy_description()`
5. Add parameter controls in `create_strategy_controls()`

### Testing Strategy Changes
```bash
# Run with specific strategy to see debug output
streamlit run streamlit_app.py
# Check console for "Squeeze 상태 통계" debug prints
```

### Performance Optimization
- Data is cached for 5 minutes using `@st.cache_data(ttl=300)`
- Use `yfinance` with error handling for data fetching
- Filter weekends early to reduce chart rendering time

## Critical Dependencies
- **pandas-ta**: Required for accurate technical indicators (version >=0.3.14b0)
- **yfinance**: Stock data source (handles delisting/errors gracefully)
- **plotly**: All charts use plotly.graph_objects for consistent styling

## Error Handling Patterns
- Always check for NaN values before strategy calculations
- Use bounds checking for pandas operations (especially in Squeeze momentum)
- Validate column existence before iloc operations
- Handle yfinance download failures with try/catch

## Project-Specific Conventions
- Korean comments for business logic, English for technical implementation
- Print debug statements show Korean text for user feedback
- All monetary values default to 10,000,000 (10M) for Korean market context
- Date format: 'YYYY-MM-DD' strings for user inputs
- File structure: Keep all main logic in 3 core files (no subdirectories)

This is a financial analysis tool requiring precision in calculations and robust error handling for real market data.

모든 테스트를 진핼할 때 파이썬 가상환경을 켜고해.
# Ensure virtual environment is activated
```bash
source .venv/bin/activate
```