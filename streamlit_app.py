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
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 로컬 모듈 import
from strategies import StrategyManager
from backtest_engine import BacktestEngine, PortfolioAnalyzer

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
        self.strategy_manager = StrategyManager()
        self.backtest_engine = BacktestEngine()
        self.portfolio_analyzer = PortfolioAnalyzer()
    
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 전략 목록 반환"""
        return self.strategy_manager.get_available_strategies()
    
    def calculate_strategy_signals(self, strategy_name: str, data: pd.DataFrame, **params) -> pd.DataFrame:
        """전략별 신호 계산"""
        return self.strategy_manager.calculate_signals(strategy_name, data, **params)
    
    def run_backtest(self, data: pd.DataFrame, strategy_data: pd.DataFrame, initial_capital: float, 
                     stop_loss_pct: float = None, take_profit_pct: float = None, support_resistance_lookback: int = None) -> Dict:
        """백테스트 실행"""
        self.backtest_engine.initial_capital = initial_capital
        return self.backtest_engine.run_backtest(data, strategy_data, stop_loss_pct, take_profit_pct, support_resistance_lookback)
    
    def calculate_metrics(self, result: Dict) -> Dict:
        """성과 지표 계산"""
        return self.backtest_engine.calculate_metrics(result)
    
    def validate_trades(self, result: Dict) -> Dict:
        """거래 유효성 검증"""
        return self.backtest_engine.validate_trades(result)

def get_strategy_description(strategy_name: str) -> str:
    """전략별 상세 설명 반환"""
    descriptions = {
        "Moving Average": """
        **이동평균 크로스오버 전략**
        
        두 개의 서로 다른 기간의 이동평균선을 사용하여 매매 신호를 생성합니다.
        
        📈 **매수 신호**: 단기 이동평균이 장기 이동평균을 상향 돌파
        📉 **매도 신호**: 단기 이동평균이 장기 이동평균을 하향 돌파
        
        **장점**: 단순하고 이해하기 쉬우며, 트렌드 추종에 효과적
        **단점**: 횡보장에서 잦은 거짓 신호 발생 가능
        """,
        
        "RSI": """
        **RSI (상대강도지수) 전략**
        
        가격의 상승폭과 하락폭의 비율을 이용해 과매수/과매도 상태를 판단합니다.
        
        📈 **매수 신호**: RSI가 과매도선(보통 30) 아래에서 위로 상승
        📉 **매도 신호**: RSI가 과매수선(보통 70) 위에서 아래로 하락
        
        **장점**: 횡보장에서 효과적, 과매수/과매도 구간 식별 용이
        **단점**: 강한 트렌드에서는 지속적으로 과매수/과매도 상태 유지 가능
        """,
        
        "Bollinger Bands": """
        **볼린저 밴드 전략**
        
        이동평균선과 표준편차를 이용해 가격의 상한과 하한을 설정합니다.
        
        📈 **매수 신호**: 가격이 하단 밴드 아래로 떨어진 후 반등
        📉 **매도 신호**: 가격이 상단 밴드 위로 올라간 후 하락
        
        **장점**: 변동성을 고려한 동적 지지/저항선 제공
        **단점**: 강한 트렌드에서는 밴드를 따라 계속 움직일 수 있음
        """,
        
        "MACD": """
        **MACD (이동평균수렴확산) 전략**
        
        두 지수이동평균의 차이(MACD)와 그 신호선의 교차를 이용합니다.
        
        📈 **매수 신호**: MACD선이 신호선을 상향 돌파
        📉 **매도 신호**: MACD선이 신호선을 하향 돌파
        
        **장점**: 트렌드 변화를 빠르게 감지, 모멘텀 분석 가능
        **단점**: 횡보장에서 잦은 거짓 신호 발생 가능
        """,
        
        "Stochastic": """
        **스토캐스틱 오실레이터 전략**
        
        일정 기간 동안의 최고가와 최저가 대비 현재가의 위치를 백분율로 나타냅니다.
        
        📈 **매수 신호**: 과매도 구간에서 %K선이 %D선을 상향 돌파
        📉 **매도 신호**: 과매수 구간에서 %K선이 %D선을 하향 돌파
        
        **장점**: 단기 모멘텀 변화에 민감, 횡보장에서 효과적
        **단점**: 노이즈가 많아 거짓 신호 발생 가능성 높음
        """,
        
        "Squeeze Momentum": """
        **Squeeze Momentum Indicator 전략 (TTM Squeeze)**
        
        볼린저 밴드와 켈트너 채널의 압축 상태를 감지하여 가격 폭발 시점을 예측합니다.
        
        📈 **매수 신호**: Squeeze 해제 후 모멘텀이 양수로 전환
        📉 **매도 신호**: 모멘텀이 음수로 전환
        
        **원리**: 
        - Squeeze 상태: 볼린저 밴드가 켈트나 채널 내부에 위치 (변동성 축소)
        - Squeeze 해제: 변동성 폭발 직전 신호
        - 모멘텀: 가격 움직임의 방향성 확인
        
        **장점**: 큰 가격 움직임을 사전에 감지, 높은 수익률 잠재력
        **단점**: 신호 빈도가 낮음, 거짓 돌파 가능성
        """
    }
    return descriptions.get(strategy_name, "")

@st.cache_data(ttl=300)  # 5분 캐시
def load_stock_data(symbol: str, period: str = "1y") -> Tuple[pd.DataFrame, str]:
    """주식 데이터 로드 (캐시됨)"""
    try:
        if not symbol or symbol.strip() == "":
            return pd.DataFrame(), "티커가 입력되지 않았습니다."
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        
        if data.empty:
            return pd.DataFrame(), f"'{symbol}' 티커의 데이터를 찾을 수 없습니다. 티커를 확인해주세요."
        
        # 주말 및 거래 없는 날 제거 (토요일=5, 일요일=6)
        data = data[data.index.dayofweek < 5]
        
        # 거래량이 0인 날도 제거 (공휴일 등)
        data = data[data['Volume'] > 0]
        
        # 인덱스를 날짜 형식으로 확실히 변환
        data.index = pd.to_datetime(data.index)
        
        if len(data) < 50:
            return pd.DataFrame(), f"'{symbol}' 티커의 충분한 데이터가 없습니다. (최소 50일 필요)"
        
        return data, "데이터 로딩 성공"
        
    except Exception as e:
        error_msg = f"'{symbol}' 데이터 로딩 중 오류: {str(e)}"
        return pd.DataFrame(), error_msg

def get_squeeze_periods(strategy_data: pd.DataFrame) -> List[Dict]:
    """Squeeze 구간을 연속된 기간으로 그룹화"""
    if 'SQZ_ON' not in strategy_data.columns:
        return []
    
    periods = []
    current_period = None
    
    for i, (date, row) in enumerate(strategy_data.iterrows()):
        if pd.isna(row['SQZ_ON']):
            continue
            
        # Squeeze 상태 결정
        if row['SQZ_ON']:
            state = 'squeeze_on'
            color = 'black'
            opacity = 0.3
        elif 'NO_SQZ' in strategy_data.columns and row['NO_SQZ']:
            state = 'no_squeeze'
            color = 'blue'
            opacity = 0.2
        else:
            state = 'squeeze_off'
            color = 'gray'
            opacity = 0.1
        
        # 새로운 구간 시작 또는 기존 구간 연장
        if current_period is None or current_period['state'] != state:
            # 이전 구간 종료
            if current_period is not None:
                current_period['end'] = strategy_data.index[i-1] if i > 0 else date
                periods.append(current_period)
            
            # 새 구간 시작
            current_period = {
                'state': state,
                'start': date,
                'end': date,
                'color': color,
                'opacity': opacity
            }
        else:
            # 기존 구간 연장
            current_period['end'] = date
    
    # 마지막 구간 처리
    if current_period is not None:
        periods.append(current_period)
    
    return periods

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
                marker=dict(color='lime', size=12, symbol='triangle-up'),
                name='Buy Signal'
            ),
            row=1, col=1
        )
    
    # 매도 시그널 (일반 매도와 손절매 구분)
    if sell_signals:
        # 일반 매도 신호
        regular_sells = [sig for sig in sell_signals if sig.get('type', 'strategy') in ['strategy', 'final']]
        if regular_sells:
            sell_dates = [sig['date'] for sig in regular_sells]
            sell_prices = [sig['price'] for sig in regular_sells]
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
        
        # 손절매 신호
        stop_loss_sells = [sig for sig in sell_signals if sig.get('type') == 'stop_loss']
        if stop_loss_sells:
            stop_dates = [sig['date'] for sig in stop_loss_sells]
            stop_prices = [sig['price'] for sig in stop_loss_sells]
            fig.add_trace(
                go.Scatter(
                    x=stop_dates,
                    y=stop_prices,
                    mode='markers',
                    marker=dict(color='orange', size=14, symbol='x'),
                    name='Stop Loss'
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
    
    elif strategy_name == "MACD":
        if all(col in strategy_data.columns for col in ['MACD', 'MACD_Signal']):
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['MACD'], 
                          name='MACD', line=dict(color='blue')),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['MACD_Signal'], 
                          name='Signal', line=dict(color='red')),
                row=3, col=1
            )
            if 'MACD_Histogram' in strategy_data.columns:
                fig.add_trace(
                    go.Bar(x=strategy_data.index, y=strategy_data['MACD_Histogram'], 
                           name='Histogram', marker_color='gray'),
                    row=3, col=1
                )
            fig.add_hline(y=0, line_dash="dash", line_color="black", row=3, col=1)
    
    elif strategy_name == "Stochastic":
        if all(col in strategy_data.columns for col in ['%K', '%D']):
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['%K'], 
                          name='%K', line=dict(color='blue')),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['%D'], 
                          name='%D', line=dict(color='red')),
                row=3, col=1
            )
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", row=3, col=1)
    
    elif strategy_name == "Squeeze Momentum":
        # Squeeze 구간을 연속된 기간으로 표시
        squeeze_periods = get_squeeze_periods(strategy_data)
        
        for period in squeeze_periods:
            if period['state'] == 'squeeze_on':
                label = 'Squeeze ON'
            elif period['state'] == 'no_squeeze':
                label = 'No Squeeze'
            else:
                label = 'Squeeze OFF'
                
            # 가격 차트에 배경색 추가
            fig.add_vrect(
                x0=period['start'], 
                x1=period['end'],
                fillcolor=period['color'], 
                opacity=period['opacity'],
                layer="below", 
                line_width=0,
                annotation_text=label if period['end'] != period['start'] else "",
                annotation_position="top left",
                row=1, col=1
            )
            
            # 인디케이터 차트에도 배경색 추가
            fig.add_vrect(
                x0=period['start'], 
                x1=period['end'],
                fillcolor=period['color'], 
                opacity=period['opacity'],
                layer="below", 
                line_width=0,
                row=3, col=1
            )
        
        # 모멘텀 히스토그램 (LazyBear 스타일)
        if 'SQZ_VAL' in strategy_data.columns:
            # NaN 값 제거
            valid_data = strategy_data.dropna(subset=['SQZ_VAL'])
            
            # 색상 계산 (LazyBear 로직)
            colors = []
            for i in range(len(valid_data)):
                val = valid_data['SQZ_VAL'].iloc[i]
                prev_val = valid_data['SQZ_VAL'].iloc[i-1] if i > 0 else 0
                
                if pd.isna(val):
                    colors.append('gray')
                    continue
                
                if val > 0:
                    # 양수: 증가하면 lime, 감소하면 green
                    if val > prev_val:
                        colors.append('lime')
                    else:
                        colors.append('green')
                else:
                    # 음수: 감소하면 red, 증가하면 maroon
                    if val < prev_val:
                        colors.append('red')
                    else:
                        colors.append('maroon')
            
            fig.add_trace(
                go.Bar(
                    x=valid_data.index, 
                    y=valid_data['SQZ_VAL'], 
                    name='Momentum', 
                    marker_color=colors,
                    showlegend=True
                ),
                row=3, col=1
            )
            fig.add_hline(y=0, line_dash="dash", line_color="black", row=3, col=1)
        
        # 볼린저 밴드와 켈트나 채널 표시
        if all(col in strategy_data.columns for col in ['BB_Upper', 'BB_Lower', 'KC_Upper', 'KC_Lower']):
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['BB_Upper'], 
                          name='BB Upper', line=dict(color='blue', dash='dash'), opacity=0.7),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['BB_Lower'], 
                          name='BB Lower', line=dict(color='blue', dash='dash'), opacity=0.7),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['KC_Upper'], 
                          name='KC Upper', line=dict(color='red', dash='dot'), opacity=0.7),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['KC_Lower'], 
                          name='KC Lower', line=dict(color='red', dash='dot'), opacity=0.7),
                row=1, col=1
            )
        
        # 200일 EMA 표시
        if 'EMA_200' in strategy_data.columns:
            fig.add_trace(
                go.Scatter(x=strategy_data.index, y=strategy_data['EMA_200'], 
                          name='EMA 200', line=dict(color='purple', width=2)),
                row=1, col=1
            )
            
        # Squeeze 상태 범례 추가
        if squeeze_periods:
            # 각 상태별로 하나씩만 범례에 추가
            states_added = set()
            for period in squeeze_periods:
                if period['state'] not in states_added:
                    if period['state'] == 'squeeze_on':
                        label = '⚫ Squeeze ON'
                        color = 'black'
                    elif period['state'] == 'no_squeeze':
                        label = '🔵 No Squeeze'
                        color = 'blue'
                    else:
                        label = '⚪ Squeeze OFF'
                        color = 'gray'
                    
                    # 빈 scatter로 범례만 추가
                    fig.add_trace(
                        go.Scatter(
                            x=[None], y=[None],
                            mode='markers',
                            marker=dict(color=color, size=10),
                            name=label,
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    states_added.add(period['state'])
    
    # 거래량
    fig.add_trace(
        go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='lightblue'),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"{strategy_name} Strategy Backtest",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        # 연속 시계열 차트 설정 (주말/공휴일 자동 제거)
        xaxis=dict(
            type='date',  # 날짜 타입으로 설정
            tickformat='%Y-%m-%d',
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # 주말 제거
            ]
        ),
        xaxis2=dict(
            type='date',
            tickformat='%Y-%m-%d',
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # 주말 제거
            ]
        ),
        xaxis3=dict(
            type='date',
            tickformat='%Y-%m-%d',
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # 주말 제거
            ]
        )
    )
    
    return fig

def main():
    """메인 애플리케이션"""
    
    # 페이지 선택
    st.sidebar.title("📍 Navigation")
    page = st.sidebar.selectbox(
        "Choose Analysis Type",
        ["🎯 Single Stock Analysis", "🏆 S&P 500 Batch Analysis"]
    )
    
    if page == "🏆 S&P 500 Batch Analysis":
        # S&P 500 분석 페이지 import 및 실행
        try:
            from sp500_analyzer import create_sp500_analysis_page
            create_sp500_analysis_page()
        except ImportError as e:
            st.error(f"S&P 500 분석 모듈을 로드할 수 없습니다: {e}")
        return
    
    # 기존 단일 종목 분석 페이지
    # 헤더
    st.title("🚀 Smart Backtester v3")
    st.markdown("### 📈 Professional Trading Strategy Backtesting Platform")
    
    # 사이드바 - 설정
    st.sidebar.header("⚙️ Settings")
    
    # 종목 선택
    st.sidebar.subheader("📊 Stock Selection")
    
    # 티커 입력 방식 선택
    input_method = st.sidebar.radio(
        "입력 방식",
        ["🔤 직접 입력", "⭐ 인기 종목 선택"],
        horizontal=True
    )
    
    if input_method == "🔤 직접 입력":
        symbol = st.sidebar.text_input(
            "티커 입력", 
            value="AAPL", 
            help="예: AAPL, MSFT, 005930.KS (삼성전자), TSLA 등"
        ).upper().strip()
        
        # 티커 형식 검증 및 피드백
        if symbol:
            if "." in symbol:
                # 국제 주식
                if symbol.endswith(".KS"):
                    st.sidebar.success("🇰🇷 한국 주식")
                elif symbol.endswith(".T"):
                    st.sidebar.success("🇯🇵 일본 주식")
                elif symbol.endswith(".L"):
                    st.sidebar.success("🇬🇧 영국 주식")
                else:
                    st.sidebar.info("🌍 국제 주식")
            else:
                # 미국 주식
                st.sidebar.success("🇺🇸 미국 주식")
        
        # 입력 가이드
        st.sidebar.info("""
        💡 **티커 입력 가이드:**
        - 🇺🇸 미국: AAPL, MSFT, GOOGL
        - 🇰🇷 한국: 005930.KS, 000660.KS
        - 🇯🇵 일본: 7203.T, 9984.T
        - �� 영국: RDSA.L, BP.L
        """)
        
    else:
        # 인기 종목 프리셋
        popular_stocks = {
            "🇺🇸 US Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
            "🇺🇸 US Finance": ["JPM", "BAC", "WFC", "C", "GS", "V", "MA"],
            "🇺🇸 US Consumer": ["KO", "PEP", "WMT", "HD", "MCD", "NKE"],
            "🇰🇷 Korean": ["005930.KS", "000660.KS", "035420.KS", "051910.KS", "035720.KS"],
            "🌏 Global ETF": ["SPY", "QQQ", "VTI", "IWM", "EFA", "EEM"]
        }
        
        preset_category = st.sidebar.selectbox("카테고리 선택", list(popular_stocks.keys()))
        symbol = st.sidebar.selectbox("종목 선택", popular_stocks[preset_category])
    
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
    
    # 백테스터 생성 (전략 목록을 가져오기 위해)
    backtester = StreamlitBacktester()
    available_strategies = backtester.get_available_strategies()
    
    # 전략 선택
    strategy_name = st.sidebar.selectbox("Strategy", available_strategies)
    
    # 전략 설명 표시
    with st.sidebar.expander("📖 Strategy Info", expanded=False):
        st.markdown(get_strategy_description(strategy_name))
    
    # 선택된 전략에 따른 동적 파라미터 설정
    st.sidebar.subheader("⚙️ Strategy Parameters")
    strategy_params = {}
    
    if strategy_name == "Moving Average":
        strategy_params = {
            "short": st.sidebar.slider("📈 Short MA Period", 5, 50, 20, 
                                     help="단기 이동평균 기간 (작을수록 민감)"),
            "long": st.sidebar.slider("📊 Long MA Period", 20, 200, 50,
                                    help="장기 이동평균 기간 (클수록 안정적)")
        }
        st.sidebar.info("💡 단기 MA가 장기 MA를 상향돌파시 매수, 하향돌파시 매도")
        
    elif strategy_name == "RSI":
        strategy_params = {
            "period": st.sidebar.slider("📊 RSI Period", 5, 30, 14,
                                      help="RSI 계산 기간"),
            "oversold": st.sidebar.slider("📉 Oversold Level", 10, 40, 30,
                                        help="과매도 기준선 (낮을수록 보수적)"),
            "overbought": st.sidebar.slider("📈 Overbought Level", 60, 90, 70,
                                          help="과매수 기준선 (높을수록 보수적)")
        }
        st.sidebar.info("💡 RSI가 과매도선 아래로 떨어지면 매수, 과매수선 위로 올라가면 매도")
        
    elif strategy_name == "Bollinger Bands":
        strategy_params = {
            "period": st.sidebar.slider("📊 BB Period", 10, 50, 20,
                                      help="볼린저 밴드 기간"),
            "std_dev": st.sidebar.slider("📏 Standard Deviation", 1.0, 3.0, 2.0, 0.1,
                                       help="표준편차 승수 (클수록 밴드가 넓어짐)")
        }
        st.sidebar.info("💡 가격이 하단밴드 아래로 떨어지면 매수, 상단밴드 위로 올라가면 매도")
        
    elif strategy_name == "MACD":
        strategy_params = {
            "fast": st.sidebar.slider("⚡ Fast EMA", 5, 20, 12,
                                    help="빠른 지수이동평균 기간"),
            "slow": st.sidebar.slider("🐌 Slow EMA", 20, 50, 26,
                                    help="느린 지수이동평균 기간"),
            "signal": st.sidebar.slider("📶 Signal EMA", 5, 15, 9,
                                      help="시그널선 평활화 기간")
        }
        st.sidebar.info("💡 MACD선이 시그널선을 상향돌파시 매수, 하향돌파시 매도")
        
    elif strategy_name == "Stochastic":
        strategy_params = {
            "k_period": st.sidebar.slider("📊 %K Period", 5, 20, 14,
                                        help="스토캐스틱 %K 계산 기간"),
            "d_period": st.sidebar.slider("📈 %D Period", 1, 10, 3,
                                        help="스토캐스틱 %D 평활화 기간"),
            "oversold": st.sidebar.slider("📉 Oversold Level", 10, 30, 20,
                                        help="과매도 기준선"),
            "overbought": st.sidebar.slider("📈 Overbought Level", 70, 90, 80,
                                          help="과매수 기준선")
        }
        st.sidebar.info("💡 과매도 구간에서 %K가 %D를 상향돌파시 매수, 과매수 구간에서 하향돌파시 매도")
        
    elif strategy_name == "Squeeze Momentum":
        strategy_params = {
            "bb_period": st.sidebar.slider("📊 Bollinger Period", 10, 30, 20,
                                         help="볼린저 밴드 계산 기간"),
            "bb_std": st.sidebar.slider("📏 BB Std Dev", 1.5, 3.0, 2.0, 0.1,
                                      help="볼린저 밴드 표준편차 승수"),
            "kc_period": st.sidebar.slider("📈 Keltner Period", 10, 30, 20,
                                         help="켈트나 채널 계산 기간"),
            "kc_mult": st.sidebar.slider("⚡ Keltner Multiplier", 1.0, 2.5, 1.5, 0.1,
                                       help="켈트나 채널 ATR 승수"),
            "momentum_period": st.sidebar.slider("🚀 Momentum Period", 8, 20, 12,
                                                help="모멘텀 계산 기간"),
            "ema_period": st.sidebar.slider("📈 EMA Filter Period", 50, 300, 200,
                                          help="EMA 필터 기간 (매수 조건: 주가 > EMA)")
        }
        st.sidebar.info("💡 Squeeze 해제 후 모멘텀이 양수로 전환시 + 주가가 EMA 위에 있을 때 매수")
        st.sidebar.warning("⚠️ EMA 필터로 인해 매수 기회가 줄어들 수 있습니다.")
    
    # 손절매 설정
    st.sidebar.subheader("🛡️ Risk Management")
    
    # 손절매 활성화
    enable_stop_loss = st.sidebar.checkbox("Enable Stop Loss", value=False)
    
    stop_loss_pct = None
    support_resistance_lookback = None
    
    if enable_stop_loss:
        stop_loss_type = st.sidebar.selectbox(
            "Stop Loss Type", 
            ["Percentage Based", "Support/Resistance Based", "Both"]
        )
        
        if stop_loss_type in ["Percentage Based", "Both"]:
            stop_loss_pct = st.sidebar.slider(
                "📉 Stop Loss (%)", 
                1.0, 20.0, 5.0, 0.5,
                help="손실이 이 비율에 도달하면 자동 매도"
            )
        
        if stop_loss_type in ["Support/Resistance Based", "Both"]:
            support_resistance_lookback = st.sidebar.slider(
                "📊 Lookback Period", 
                10, 50, 20,
                help="지지/저항선 계산을 위한 과거 기간"
            )
            st.sidebar.info("💡 지지선을 2% 하향 돌파시 자동 매도")
    
    # 익절매 설정 추가
    enable_take_profit = st.sidebar.checkbox("Enable Take Profit", value=False)
    
    take_profit_pct = None
    
    if enable_take_profit:
        take_profit_pct = st.sidebar.slider(
            "📈 Take Profit (%)", 
            5.0, 50.0, 15.0, 1.0,
            help="수익이 이 비율에 도달하면 자동 매도"
        )
        st.sidebar.info("💡 매수가 대비 수익률이 설정값에 도달하면 익절매 실행")
    
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
            data, load_message = load_stock_data(symbol, period)
        
        if data.empty:
            st.error(f"❌ {load_message}")
            st.info("""
            **티커 입력 팁:**
            - 🇺🇸 미국 주식: 회사명의 축약형 (예: AAPL, MSFT, GOOGL)
            - 🇰🇷 한국 주식: 종목코드.KS (예: 005930.KS, 000660.KS)
            - 🇯🇵 일본 주식: 종목코드.T (예: 7203.T)
            - 🇨🇳 중국 주식: 나스닥 상장 중국기업 (예: BABA, JD)
            """)
            return
        else:
            st.success(f"✅ {symbol} 데이터 로딩 완료! ({len(data)}일간 데이터)")
        
        # 전략 실행
        with st.spinner("Running backtest..."):
            # 전략 신호 계산
            strategy_data = backtester.calculate_strategy_signals(strategy_name, data, **strategy_params)
            
            # 백테스트 실행 (손절매/익절매 설정 포함)
            result = backtester.run_backtest(
                data, strategy_data, initial_capital, 
                stop_loss_pct, take_profit_pct, support_resistance_lookback
            )
            metrics = backtester.calculate_metrics(result)
            
            # 거래 유효성 검증
            validation = backtester.validate_trades(result)
            if not validation['is_valid']:
                st.warning("⚠️ 거래 유효성 검증에서 문제가 발견되었습니다:")
                for issue in validation['issues']:
                    st.error(f"• {issue}")
            else:
                st.success("✅ 거래 유효성 검증 통과")
        
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
                # 주말/공휴일 제거 설정
                fig_portfolio.update_layout(
                    xaxis=dict(
                        type='date',
                        rangebreaks=[
                            dict(bounds=["sat", "mon"]),  # 주말 제거
                        ]
                    )
                )
                st.plotly_chart(fig_portfolio, use_container_width=True)
            
            with col2:
                st.subheader("📊 Detailed Metrics")
                
                # 손절매 통계 계산
                stop_loss_count = len([t for t in result['trades'] if t.get('action') == 'STOP_LOSS'])
                regular_sell_count = len([t for t in result['trades'] if t.get('action') == 'SELL'])
                
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
                    ["Regular Sells", f"{regular_sell_count}"],
                    ["Stop Losses", f"{stop_loss_count}"],
                    ["Avg Trade Return", f"{metrics['avg_trade_return']:.2f}%"],
                    ["Best Trade", f"{metrics['best_trade']:.2f}%"],
                    ["Worst Trade", f"{metrics['worst_trade']:.2f}%"]
                ], columns=["Metric", "Value"])
                
                st.dataframe(metrics_df, use_container_width=True, hide_index=True)
                
                # 손절매 비율 강조 표시
                if stop_loss_count > 0:
                    stop_loss_rate = (stop_loss_count / metrics['total_trades']) * 100 if metrics['total_trades'] > 0 else 0
                    st.error(f"🔻 Stop Loss Rate: {stop_loss_rate:.1f}% (All counted as losses)")
            
            # 거래 내역
            if result['trades']:
                st.subheader("📋 Trade History")
                trades_df = pd.DataFrame(result['trades'])
                trades_df['date'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y-%m-%d')
                trades_df['price'] = trades_df['price'].round(2)
                trades_df['shares'] = trades_df['shares'].round(2)
                trades_df['portfolio_value'] = trades_df['portfolio_value'].round(2)
                
                # 손절매 정보가 있으면 표시
                if 'reason' in trades_df.columns:
                    trades_df['reason'] = trades_df['reason'].fillna('-')
                
                # 색상 코딩
                def color_trades(val):
                    if val == 'BUY':
                        return 'background-color: #d4edda'
                    elif val == 'SELL':
                        return 'background-color: #f8d7da'
                    elif val == 'STOP_LOSS':
                        return 'background-color: #fff3cd'
                    return ''
                
                styled_trades = trades_df.style.applymap(color_trades, subset=['action'])
                st.dataframe(styled_trades, use_container_width=True, hide_index=True)
                
                # 손절매 통계
                stop_loss_trades = [t for t in result['trades'] if t.get('action') == 'STOP_LOSS']
                regular_sell_trades = [t for t in result['trades'] if t.get('action') == 'SELL']
                
                if stop_loss_trades:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"🛡️ Stop Loss activated {len(stop_loss_trades)} times")
                        for trade in stop_loss_trades:
                            st.caption(f"• {trade['date'].strftime('%Y-%m-%d')}: {trade.get('reason', 'Stop Loss')}")
                    
                    with col2:
                        st.warning(f"⚠️ All {len(stop_loss_trades)} stop loss trades are counted as losses in win rate calculation")
                        st.caption(f"📊 Regular sells: {len(regular_sell_trades)} | Stop losses: {len(stop_loss_trades)}")
                        if 'total_trades' in metrics:
                            stop_loss_rate = (len(stop_loss_trades) / metrics['total_trades']) * 100 if metrics['total_trades'] > 0 else 0
                            st.caption(f"🔻 Stop loss rate: {stop_loss_rate:.1f}%")
            
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
        sample_data, _ = load_stock_data("AAPL", "6mo")
        if not sample_data.empty:
            fig_sample = go.Figure(data=go.Candlestick(
                x=sample_data.index,
                open=sample_data['Open'],
                high=sample_data['High'],
                low=sample_data['Low'],
                close=sample_data['Close']
            ))
            fig_sample.update_layout(
                title="Sample Chart", 
                xaxis_rangeslider_visible=False, 
                height=400,
                xaxis=dict(
                    type='date',
                    rangebreaks=[
                        dict(bounds=["sat", "mon"]),  # 주말 제거
                    ]
                )
            )
            st.plotly_chart(fig_sample, use_container_width=True)

if __name__ == "__main__":
    main()
