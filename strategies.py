#!/usr/bin/env python3
"""
백테스팅 전략 모듈
- 다양한 기술적 분석 기반 매매 전략들
- 각 전략은 독립적으로 구현되어 재사용 가능
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod
import pandas_ta as ta


class BaseStrategy(ABC):
    """기본 전략 클래스"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        """신호 계산 메서드 (각 전략에서 구현)"""
        pass
    
    def _init_signal_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """신호 컬럼 초기화"""
        df['Signal'] = 0
        df['Position'] = 0
        return df
    
    def _finalize_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """신호 마무리 처리"""
        df['Position_Change'] = df['Signal'].diff()
        return df


class MovingAverageStrategy(BaseStrategy):
    """이동평균 전략"""
    
    def __init__(self):
        super().__init__("Moving Average")
    
    def calculate_signals(self, data: pd.DataFrame, short: int = 20, long: int = 50) -> pd.DataFrame:
        """이동평균 신호 계산
        
        Args:
            data: OHLCV 데이터
            short: 단기 이동평균 기간
            long: 장기 이동평균 기간
            
        Returns:
            신호가 추가된 데이터프레임
        """
        df = data.copy()
        df['MA_Short'] = df['Close'].rolling(short).mean()
        df['MA_Long'] = df['Close'].rolling(long).mean()
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
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
        
        return self._finalize_signals(df)


class RSIStrategy(BaseStrategy):
    """RSI 전략"""
    
    def __init__(self):
        super().__init__("RSI")
    
    def calculate_signals(self, data: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
        """RSI 신호 계산
        
        Args:
            data: OHLCV 데이터
            period: RSI 계산 기간
            oversold: 과매도 기준값
            overbought: 과매수 기준값
            
        Returns:
            신호가 추가된 데이터프레임
        """
        df = data.copy()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
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
        
        return self._finalize_signals(df)


class BollingerBandsStrategy(BaseStrategy):
    """볼린저 밴드 전략"""
    
    def __init__(self):
        super().__init__("Bollinger Bands")
    
    def calculate_signals(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """볼린저 밴드 신호 계산
        
        Args:
            data: OHLCV 데이터
            period: 이동평균 및 표준편차 계산 기간
            std_dev: 표준편차 승수
            
        Returns:
            신호가 추가된 데이터프레임
        """
        df = data.copy()
        df['BB_Mid'] = df['Close'].rolling(period).mean()
        df['BB_Std'] = df['Close'].rolling(period).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * std_dev)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * std_dev)
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
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
        
        return self._finalize_signals(df)


class MACDStrategy(BaseStrategy):
    """MACD 전략"""
    
    def __init__(self):
        super().__init__("MACD")
    
    def calculate_signals(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD 신호 계산
        
        Args:
            data: OHLCV 데이터
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간
            signal: 신호선 EMA 기간
            
        Returns:
            신호가 추가된 데이터프레임
        """
        df = data.copy()
        
        # MACD 계산
        exp1 = df['Close'].ewm(span=fast).mean()
        exp2 = df['Close'].ewm(span=slow).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=signal).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
        current_position = 0
        
        for i in range(1, len(df)):  # 이전 값과 비교하므로 1부터 시작
            if pd.isna(df['MACD'].iloc[i]) or pd.isna(df['MACD_Signal'].iloc[i]):
                continue
                
            macd_current = df['MACD'].iloc[i]
            signal_current = df['MACD_Signal'].iloc[i]
            macd_prev = df['MACD'].iloc[i-1]
            signal_prev = df['MACD_Signal'].iloc[i-1]
            
            # 매수 조건: 포지션이 없고, MACD가 신호선을 상향돌파
            if current_position == 0 and macd_prev <= signal_prev and macd_current > signal_current:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 포지션이 있고, MACD가 신호선을 하향돌파
            elif current_position == 1 and macd_prev >= signal_prev and macd_current < signal_current:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        return self._finalize_signals(df)


class StochasticStrategy(BaseStrategy):
    """스토캐스틱 전략"""
    
    def __init__(self):
        super().__init__("Stochastic")
    
    def calculate_signals(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3, oversold: int = 20, overbought: int = 80) -> pd.DataFrame:
        """스토캐스틱 신호 계산
        
        Args:
            data: OHLCV 데이터
            k_period: %K 계산 기간
            d_period: %D 계산 기간
            oversold: 과매도 기준값
            overbought: 과매수 기준값
            
        Returns:
            신호가 추가된 데이터프레임
        """
        df = data.copy()
        
        # 스토캐스틱 계산
        low_min = df['Low'].rolling(k_period).min()
        high_max = df['High'].rolling(k_period).max()
        df['%K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        df['%D'] = df['%K'].rolling(d_period).mean()
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
        current_position = 0
        
        for i in range(len(df)):
            if pd.isna(df['%K'].iloc[i]) or pd.isna(df['%D'].iloc[i]):
                continue
                
            k_value = df['%K'].iloc[i]
            d_value = df['%D'].iloc[i]
            
            # 매수 조건: 포지션이 없고, %K가 과매도 구간에서 %D를 상향돌파
            if current_position == 0 and k_value <= oversold and k_value > d_value:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 포지션이 있고, %K가 과매수 구간에서 %D를 하향돌파
            elif current_position == 1 and k_value >= overbought and k_value < d_value:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        return self._finalize_signals(df)


def _calculate_squeeze_momentum(df, bb_length=20, kc_length=20, kc_mult=1.5, use_tr=True):
    """
    LazyBear의 Squeeze Momentum Indicator 로직을 기반으로 스퀴즈 모멘텀을 계산합니다.
    pandas-ta의 기본 squeeze와 달라 직접 구현합니다.
    """
    df_copy = df.copy()
    
    # 1. 볼린저 밴드 (켈트너 채널 승수 사용)
    basis = ta.sma(df_copy['Close'], length=bb_length)
    dev = kc_mult * ta.stdev(df_copy['Close'], length=bb_length)
    df_copy['BBU_LB'] = basis + dev
    df_copy['BBL_LB'] = basis - dev

    # 2. 켈트너 채널 (True Range의 SMA 사용)
    ma = ta.sma(df_copy['Close'], length=kc_length)
    tr = ta.true_range(df_copy['High'], df_copy['Low'], df_copy['Close']) if use_tr else (df_copy['High'] - df_copy['Low'])
    rangema = ta.sma(tr, length=kc_length)
    df_copy['KCU_LB'] = ma + rangema * kc_mult
    df_copy['KCL_LB'] = ma - rangema * kc_mult

    # 3. 스퀴즈 ON/OFF/NO 조건
    df_copy['SQZ_ON_CUSTOM'] = (df_copy['BBL_LB'] > df_copy['KCL_LB']) & (df_copy['BBU_LB'] < df_copy['KCU_LB'])
    df_copy['SQZ_OFF_CUSTOM'] = (df_copy['BBL_LB'] < df_copy['KCL_LB']) & (df_copy['BBU_LB'] > df_copy['KCU_LB'])
    df_copy['SQZ_NO_CUSTOM'] = ~df_copy['SQZ_ON_CUSTOM'] & ~df_copy['SQZ_OFF_CUSTOM']

    # 4. 모멘텀 값 (Linear Regression)
    highest_high = df_copy['High'].rolling(kc_length).max()
    lowest_low = df_copy['Low'].rolling(kc_length).min()
    sma_close = ta.sma(df_copy['Close'], length=kc_length)
    mom_source = df_copy['Close'] - ((highest_high + lowest_low) / 2 + sma_close) / 2
    df_copy['SQZ_VAL_CUSTOM'] = ta.linreg(close=mom_source, length=kc_length)

    return df_copy


class SqueezeMomentumStrategy(BaseStrategy):
    """Squeeze Momentum Indicator 전략 (LazyBear 완벽 구현)"""
    
    def __init__(self):
        super().__init__("Squeeze Momentum")
    
    def calculate_signals(self, data: pd.DataFrame, bb_period: int = 20, bb_std: float = 2.0, 
                         kc_period: int = 20, kc_mult: float = 1.5, momentum_period: int = 12) -> pd.DataFrame:
        """Squeeze Momentum 신호 계산 (LazyBear 완벽 구현)
        
        Args:
            data: OHLCV 데이터
            bb_period: 볼린저 밴드 기간 (bb_length)
            bb_std: 사용하지 않음 (kc_mult를 사용)
            kc_period: 켈트나 채널 기간 (kc_length)  
            kc_mult: 켈트나 채널 승수
            momentum_period: 사용하지 않음 (호환성을 위해 유지)
            
        Returns:
            신호가 추가된 데이터프레임
        """
        # 완벽한 LazyBear 함수 사용
        df = _calculate_squeeze_momentum(data, bb_period, kc_period, kc_mult, use_tr=True)
        
        # 컬럼명 통일
        df['BB_Upper'] = df['BBU_LB']
        df['BB_Lower'] = df['BBL_LB']
        df['KC_Upper'] = df['KCU_LB']
        df['KC_Lower'] = df['KCL_LB']
        df['SQZ_ON'] = df['SQZ_ON_CUSTOM']
        df['SQZ_OFF'] = df['SQZ_OFF_CUSTOM']
        df['NO_SQZ'] = df['SQZ_NO_CUSTOM']
        df['SQZ_VAL'] = df['SQZ_VAL_CUSTOM']
        
        # 디버깅: Squeeze 상태 통계 출력
        total_rows = len(df)
        sqz_on_count = df['SQZ_ON'].sum()
        sqz_off_count = df['SQZ_OFF'].sum() 
        no_sqz_count = df['NO_SQZ'].sum()
        
        print(f"Squeeze 상태 통계 (LazyBear 완벽 구현):")
        print(f"  Total rows: {total_rows}")
        print(f"  SQZ_ON: {sqz_on_count} ({sqz_on_count/total_rows*100:.1f}%)")
        print(f"  SQZ_OFF: {sqz_off_count} ({sqz_off_count/total_rows*100:.1f}%)")
        print(f"  NO_SQZ: {no_sqz_count} ({no_sqz_count/total_rows*100:.1f}%)")
        
        # 모멘텀 방향 및 색상 정보
        df['SQZ_VAL_PREV'] = df['SQZ_VAL'].shift(1)
        df['SQZ_INCREASING'] = df['SQZ_VAL'] > df['SQZ_VAL_PREV']
        df['SQZ_POSITIVE'] = df['SQZ_VAL'] > 0
        
        # 변동성 및 모멘텀 상태 (LazyBear 로직)
        df['VOLA_START'] = (~df['NO_SQZ'] & ~df['SQZ_ON']).astype(int)  # 변동성 시작
        df['MOMENTUM_POS'] = df['SQZ_POSITIVE'].astype(int)  # 모멘텀 방향
        
        # 변화점 감지
        df['VOLA_CHANGE'] = df['VOLA_START'].diff() == 1
        df['MOMENTUM_CHANGE'] = df['MOMENTUM_POS'].diff() != 0
        
        # 신호 생성 (LazyBear 로직)
        df['IS_LONG'] = df['VOLA_CHANGE'] & df['SQZ_POSITIVE']
        df['IS_SHORT'] = df['VOLA_CHANGE'] & ~df['SQZ_POSITIVE']
        
        # 포지션 추적을 위한 변수
        df = self._init_signal_columns(df)
        current_position = 0
        
        for i in range(1, len(df)):
            # 데이터 유효성 검사
            if pd.isna(df['SQZ_VAL'].iloc[i]) or pd.isna(df['VOLA_CHANGE'].iloc[i]):
                continue
            
            # 매수 조건: 변동성 시작 + 양의 모멘텀
            if current_position == 0 and df['IS_LONG'].iloc[i]:
                current_position = 1
                df.iloc[i, df.columns.get_loc('Signal')] = 1
                
            # 매도 조건: 모멘텀 변화 (양수에서 음수로 또는 그 반대)
            elif current_position == 1 and df['MOMENTUM_CHANGE'].iloc[i]:
                current_position = 0
                df.iloc[i, df.columns.get_loc('Signal')] = -1
            
            df.iloc[i, df.columns.get_loc('Position')] = current_position
        
        return self._finalize_signals(df)


class StrategyManager:
    """전략 관리자 클래스"""
    
    def __init__(self):
        self.strategies = {
            "Moving Average": MovingAverageStrategy(),
            "RSI": RSIStrategy(),
            "Bollinger Bands": BollingerBandsStrategy(),
            "MACD": MACDStrategy(),
            "Stochastic": StochasticStrategy(),
            "Squeeze Momentum": SqueezeMomentumStrategy()
        }
    
    def get_strategy(self, name: str) -> BaseStrategy:
        """전략 객체 반환"""
        if name not in self.strategies:
            raise ValueError(f"Unknown strategy: {name}")
        return self.strategies[name]
    
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 전략 목록 반환"""
        return list(self.strategies.keys())
    
    def calculate_signals(self, strategy_name: str, data: pd.DataFrame, **params) -> pd.DataFrame:
        """전략별 신호 계산"""
        strategy = self.get_strategy(strategy_name)
        return strategy.calculate_signals(data, **params)
