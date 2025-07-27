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


class StrategyManager:
    """전략 관리자 클래스"""
    
    def __init__(self):
        self.strategies = {
            "Moving Average": MovingAverageStrategy(),
            "RSI": RSIStrategy(),
            "Bollinger Bands": BollingerBandsStrategy(),
            "MACD": MACDStrategy(),
            "Stochastic": StochasticStrategy()
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
