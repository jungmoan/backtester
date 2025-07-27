#!/usr/bin/env python3
"""
Streamlit 백테스팅 웹 애플리케이션
- 종목 선택, 전략 선택, 실시간 백테스트
- 캔들차트 + 매매 시그널 시각화
- 성과 분석 및 리포트
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="🚀 Smart Backtester", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamlitBacktester:
    """Streamlit용 백테스터"""
    
    def __init__(self):
        self.initial_capital = 10000
        
    def calculate_ma_signals(self, data: pd.DataFrame, short: int = 20, long: int = 50) -> pd.DataFrame:
        """이동평균 신호"""
        df = data.copy()
        df['MA_Short'] = df['Close'].rolling(short).mean()
        df['MA_Long'] = df['Close'].rolling(long).mean()
        
        # 포지션 추적을 위한 변수
        df['Signal'] = 0
        df['Position'] = 0
        current_position = 0
        
        for i in range(len(df)):
            if pd.isna(df['MA_Short'].iloc[i]) or pd.isna(df['MA_Long'].iloc[i]):
                continue
                
            ma_short = df['MA_Short'].iloc[i]
            ma_long = df['MA_Long'].iloc[i]
            
            # 매수 조건: 포지션이 없고, 단기이평이 장기이평을 상향돌파
            if current_position == 0 and ma_short > ma_long:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 포지션이 있고, 단기이평이 장기이평을 하향돌파
            elif current_position == 1 and ma_short < ma_long:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        df['Position_Change'] = df['Signal'].diff()
        
        return df
    
    def calculate_rsi_signals(self, data: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
        """RSI 신호"""
        df = data.copy()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 포지션 추적을 위한 변수
        df['Signal'] = 0
        df['Position'] = 0
        current_position = 0
        
        for i in range(len(df)):
            if pd.isna(df['RSI'].iloc[i]):
                continue
                
            rsi_value = df['RSI'].iloc[i]
            
            # 매수 조건: 포지션이 없고, RSI가 과매도 구간일 때
            if current_position == 0 and rsi_value <= oversold:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 포지션이 있고, RSI가 과매수 구간일 때
            elif current_position == 1 and rsi_value >= overbought:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        df['Position_Change'] = df['Signal'].diff()
        
        return df
    
    def calculate_bollinger_signals(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """볼린저 밴드 신호"""
        df = data.copy()
        df['BB_Mid'] = df['Close'].rolling(period).mean()
        df['BB_Std'] = df['Close'].rolling(period).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * std_dev)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * std_dev)
        
        # 포지션 추적을 위한 변수
        df['Signal'] = 0
        df['Position'] = 0
        current_position = 0
        
        for i in range(len(df)):
            if pd.isna(df['BB_Upper'].iloc[i]) or pd.isna(df['BB_Lower'].iloc[i]):
                continue
                
            close_price = df['Close'].iloc[i]
            
            # 매수 조건: 포지션이 없고, 가격이 하단 밴드 아래로 떨어졌을 때
            if current_position == 0 and close_price <= df['BB_Lower'].iloc[i]:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 포지션이 있고, 가격이 상단 밴드 위로 올라갔을 때
            elif current_position == 1 and close_price >= df['BB_Upper'].iloc[i]:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        df['Position_Change'] = df['Signal'].diff()
        
        return df
    
    def run_backtest(self, data: pd.DataFrame, strategy_data: pd.DataFrame) -> Dict:
        """백테스트 실행"""
        cash = self.initial_capital
        position = 0
        portfolio_values = []
        trades = []
        buy_signals = []
        sell_signals = []
        
        for i, (date, row) in enumerate(strategy_data.iterrows()):
            price = row['Close']
            signal = row.get('Signal', 0)
            
            # 매수 신호 (Signal = 1이고 현재 포지션이 없을 때)
            if signal == 1 and position == 0:
                shares = (cash * 0.95) / price
                cash -= shares * price
                position = shares
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'portfolio_value': cash + position * price
                })
                buy_signals.append({'date': date, 'price': price})
            
            # 매도 신호 (Signal = -1이고 현재 포지션이 있을 때)
            elif signal == -1 and position > 0:
                cash += position * price
                trades.append({
                    'date': date,
                    'action': 'SELL',
                    'price': price,
                    'shares': position,
                    'portfolio_value': cash
                })
                sell_signals.append({'date': date, 'price': price})
                position = 0
            
            # 포트폴리오 가치 기록
            total_value = cash + position * price
            portfolio_values.append({
                'date': date,
                'portfolio_value': total_value,
                'cash': cash,
                'position_value': position * price,
                'price': price
            })
        
        # 최종 청산
        if position > 0:
            final_price = strategy_data['Close'].iloc[-1]
            cash += position * final_price
            sell_signals.append({'date': strategy_data.index[-1], 'price': final_price})
        
        return {
            'portfolio_history': pd.DataFrame(portfolio_values),
            'trades': trades,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'final_value': cash,
            'strategy_data': strategy_data
        }
    
    def calculate_metrics(self, result: Dict) -> Dict:
        """성과 지표 계산"""
        portfolio_df = result['portfolio_history']
        trades = result['trades']
        
        if portfolio_df.empty:
            return {}
        
        # 기본 지표
        final_value = result['final_value']
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # 수익률 시계열
        portfolio_values = portfolio_df['portfolio_value']
        returns = portfolio_values.pct_change().dropna()
        
        # 샤프 비율
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 최대 낙폭
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdowns.min() * 100
        
        # 변동성
        volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0
        
        # 거래 분석
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        # 승률 계산
        trade_returns = []
        for i in range(min(len(buy_trades), len(sell_trades))):
            buy_price = buy_trades[i]['price']
            sell_price = sell_trades[i]['price']
            trade_return = (sell_price - buy_price) / buy_price * 100
            trade_returns.append(trade_return)
        
        win_rate = 0
        if trade_returns:
            winning_trades = sum(1 for ret in trade_returns if ret > 0)
            win_rate = (winning_trades / len(trade_returns)) * 100
        
        return {
            'total_return': total_return,
            'final_value': final_value,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'total_trades': len(trade_returns),
            'winning_trades': sum(1 for ret in trade_returns if ret > 0),
            'avg_trade_return': np.mean(trade_returns) if trade_returns else 0,
            'best_trade': max(trade_returns) if trade_returns else 0,
            'worst_trade': min(trade_returns) if trade_returns else 0
        }

@st.cache_data(ttl=300)  # 5분 캐시
def load_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """주식 데이터 로드 (캐시됨)"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if data.empty:
            return pd.DataFrame()
        return data
    except:
        return pd.DataFrame()

def create_candlestick_chart(data: pd.DataFrame, buy_signals: List, sell_signals: List, strategy_data: pd.DataFrame, strategy_name: str):
    """캔들스틱 차트 + 시그널 생성"""
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=['Price & Signals', 'Volume', 'Indicators'],
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # 캔들스틱
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # 매수 시그널
    if buy_signals:
        buy_dates = [sig['date'] for sig in buy_signals]
        buy_prices = [sig['price'] for sig in buy_signals]
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                marker=dict(color='green', size=12, symbol='triangle-up'),
                name='Buy Signal'
            ),
            row=1, col=1
        )
    
    # 매도 시그널
    if sell_signals:
        sell_dates = [sig['date'] for sig in sell_signals]
        sell_prices = [sig['price'] for sig in sell_signals]
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                marker=dict(color='red', size=12, symbol='triangle-down'),
                name='Sell Signal'
            ),
            row=1, col=1
        )
    
    # 전략별 보조지표
    if strategy_name == "Moving Average":
        if 'MA_Short' in strategy_data.columns:
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['MA_Short'], 
                          name='MA Short', line=dict(color='orange')),
                row=1, col=1
            )
        if 'MA_Long' in strategy_data.columns:
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['MA_Long'], 
                          name='MA Long', line=dict(color='blue')),
                row=1, col=1
            )
    
    elif strategy_name == "RSI":
        if 'RSI' in strategy_data.columns:
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['RSI'], 
                          name='RSI', line=dict(color='purple')),
                row=3, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    elif strategy_name == "Bollinger Bands":
        if all(col in strategy_data.columns for col in ['BB_Upper', 'BB_Mid', 'BB_Lower']):
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['BB_Upper'], 
                          name='BB Upper', line=dict(color='gray', dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['BB_Mid'], 
                          name='BB Mid', line=dict(color='orange')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['BB_Lower'], 
                          name='BB Lower', line=dict(color='gray', dash='dash')),
                row=1, col=1
            )
    
    # 거래량
    fig.add_trace(
        go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='lightblue'),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"{strategy_name} Strategy Backtest",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True
    )
    
    return fig

def main():
    """메인 애플리케이션"""
    
    # 헤더
    st.title("🚀 Smart Backtester")
    st.markdown("### 📈 Professional Trading Strategy Backtesting Platform")
    
    # 사이드바 - 설정
    st.sidebar.header("⚙️ Settings")
    
    # 종목 선택
    st.sidebar.subheader("📊 Stock Selection")
    
    # 인기 종목 프리셋
    popular_stocks = {
        "🇺🇸 US Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
        "🇺🇸 US Finance": ["JPM", "BAC", "WFC", "C", "GS"],
        "🇰🇷 Korean": ["005930.KS", "000660.KS", "035420.KS", "051910.KS"]
    }
    
    preset_category = st.sidebar.selectbox("Quick Select", list(popular_stocks.keys()))
    if preset_category:
        selected_preset = st.sidebar.selectbox("Symbol", popular_stocks[preset_category])
        symbol = selected_preset
    else:
        symbol = st.sidebar.text_input("Enter Symbol", value="AAPL").upper()
    
    # 기간 설정
    period_options = {
        "6개월": "6mo",
        "1년": "1y", 
        "2년": "2y",
        "5년": "5y"
    }
    period_kr = st.sidebar.selectbox("📅 Period", list(period_options.keys()))
    period = period_options[period_kr]
    
    # 전략 선택
    st.sidebar.subheader("🎯 Strategy Selection")
    
    strategy_options = {
        "Moving Average": {
            "short_window": st.sidebar.slider("Short MA", 5, 50, 20),
            "long_window": st.sidebar.slider("Long MA", 20, 200, 50)
        },
        "RSI": {
            "period": st.sidebar.slider("RSI Period", 5, 30, 14),
            "oversold": st.sidebar.slider("Oversold", 10, 40, 30),
            "overbought": st.sidebar.slider("Overbought", 60, 90, 70)
        },
        "Bollinger Bands": {
            "period": st.sidebar.slider("BB Period", 10, 50, 20),
            "std_dev": st.sidebar.slider("Standard Deviation", 1.0, 3.0, 2.0, 0.1)
        }
    }
    
    strategy_name = st.sidebar.selectbox("Strategy", list(strategy_options.keys()))
    strategy_params = strategy_options[strategy_name]
    
    # 초기 자본
    initial_capital = st.sidebar.number_input("💰 Initial Capital ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
    
    # RUN 버튼
    run_button = st.sidebar.button("🚀 RUN BACKTEST", type="primary", use_container_width=True)
    
    # 메인 영역
    if run_button:
        if not symbol:
            st.error("Please enter a stock symbol!")
            return
        
        # 로딩 표시
        with st.spinner(f"Loading data for {symbol}..."):
            data = load_stock_data(symbol, period)
        
        if data.empty:
            st.error(f"Could not load data for {symbol}. Please check the symbol.")
            return
        
        # 백테스터 생성
        backtester = StreamlitBacktester()
        backtester.initial_capital = initial_capital
        
        # 전략 실행
        with st.spinner("Running backtest..."):
            if strategy_name == "Moving Average":
                strategy_data = backtester.calculate_ma_signals(
                    data, 
                    strategy_params['short_window'], 
                    strategy_params['long_window']
                )
            elif strategy_name == "RSI":
                strategy_data = backtester.calculate_rsi_signals(
                    data,
                    strategy_params['period'],
                    strategy_params['oversold'],
                    strategy_params['overbought']
                )
            elif strategy_name == "Bollinger Bands":
                strategy_data = backtester.calculate_bollinger_signals(
                    data,
                    strategy_params['period'],
                    strategy_params['std_dev']
                )
            
            # 백테스트 실행
            result = backtester.run_backtest(data, strategy_data)
            metrics = backtester.calculate_metrics(result)
        
        # 결과 표시
        if metrics:
            # 상단 메트릭 카드
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📈 Total Return", 
                    f"{metrics['total_return']:.2f}%",
                    delta=f"${metrics['final_value'] - initial_capital:.2f}"
                )
            
            with col2:
                st.metric(
                    "🎯 Win Rate", 
                    f"{metrics['win_rate']:.1f}%",
                    delta=f"{metrics['winning_trades']}/{metrics['total_trades']} trades"
                )
            
            with col3:
                st.metric(
                    "📊 Sharpe Ratio", 
                    f"{metrics['sharpe_ratio']:.3f}",
                    delta="Higher is better"
                )
            
            with col4:
                st.metric(
                    "📉 Max Drawdown", 
                    f"{metrics['max_drawdown']:.2f}%",
                    delta="Lower is better"
                )
            
            # 차트
            st.subheader("📊 Trading Chart & Signals")
            fig = create_candlestick_chart(
                data, 
                result['buy_signals'], 
                result['sell_signals'], 
                strategy_data,
                strategy_name
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 성과 분석
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Portfolio Performance")
                portfolio_df = result['portfolio_history']
                fig_portfolio = px.line(
                    portfolio_df, 
                    x='date', 
                    y='portfolio_value',
                    title="Portfolio Value Over Time"
                )
                fig_portfolio.add_hline(y=initial_capital, line_dash="dash", annotation_text="Initial Capital")
                st.plotly_chart(fig_portfolio, use_container_width=True)
            
            with col2:
                st.subheader("📊 Detailed Metrics")
                metrics_df = pd.DataFrame([
                    ["Initial Capital", f"${initial_capital:,.2f}"],
                    ["Final Value", f"${metrics['final_value']:.2f}"],
                    ["Total Return", f"{metrics['total_return']:.2f}%"],
                    ["Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}"],
                    ["Max Drawdown", f"{metrics['max_drawdown']:.2f}%"],
                    ["Volatility", f"{metrics['volatility']:.2f}%"],
                    ["Win Rate", f"{metrics['win_rate']:.1f}%"],
                    ["Total Trades", f"{metrics['total_trades']}"],
                    ["Winning Trades", f"{metrics['winning_trades']}"],
                    ["Avg Trade Return", f"{metrics['avg_trade_return']:.2f}%"],
                    ["Best Trade", f"{metrics['best_trade']:.2f}%"],
                    ["Worst Trade", f"{metrics['worst_trade']:.2f}%"]
                ], columns=["Metric", "Value"])
                
                st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # 거래 내역
            if result['trades']:
                st.subheader("📋 Trade History")
                trades_df = pd.DataFrame(result['trades'])
                trades_df['date'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y-%m-%d')
                trades_df['price'] = trades_df['price'].round(2)
                trades_df['shares'] = trades_df['shares'].round(2)
                trades_df['portfolio_value'] = trades_df['portfolio_value'].round(2)
                
                # 색상 코딩
                def color_trades(val):
                    if val == 'BUY':
                        return 'background-color: #d4edda'
                    elif val == 'SELL':
                        return 'background-color: #f8d7da'
                    return ''
                
                styled_trades = trades_df.style.applymap(color_trades, subset=['action'])
                st.dataframe(styled_trades, use_container_width=True, hide_index=True)
            
            # 다운로드 버튼
            st.subheader("💾 Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                if result['trades']:
                    trades_csv = pd.DataFrame(result['trades']).to_csv(index=False)
                    st.download_button(
                        "📥 Download Trades CSV",
                        trades_csv,
                        f"{symbol}_{strategy_name}_trades.csv",
                        "text/csv"
                    )
            
            with col2:
                metrics_csv = pd.DataFrame([metrics]).to_csv(index=False)
                st.download_button(
                    "📊 Download Metrics CSV",
                    metrics_csv,
                    f"{symbol}_{strategy_name}_metrics.csv",
                    "text/csv"
                )
    
    else:
        # 초기 화면
        st.info("👈 Select a stock symbol and strategy, then click 'RUN BACKTEST' to start!")
        
        # 샘플 차트 표시
        st.subheader("📊 Sample: Apple Inc. (AAPL)")
        sample_data = load_stock_data("AAPL", "6mo")
        if not sample_data.empty:
            fig_sample = go.Figure(data=go.Candlestick(
                x=sample_data.index,
                open=sample_data['Open'],
                high=sample_data['High'],
                low=sample_data['Low'],
                close=sample_data['Close']
            ))
            fig_sample.update_layout(title="Sample Chart", xaxis_rangeslider_visible=False, height=400)
            st.plotly_chart(fig_sample, use_container_width=True)

if __name__ == "__main__":
    main()
