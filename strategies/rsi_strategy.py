import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, SignalType

class RSIStrategy(BaseStrategy):
    """RSI 전략"""
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI Strategy")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.set_parameters(
            rsi_period=rsi_period,
            oversold=oversold,
            overbought=overbought
        )
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 신호 생성
        RSI < oversold (과매도) → 매수
        RSI > overbought (과매수) → 매도
        """
        if not self.validate_data(data):
            raise ValueError("데이터에 필요한 컬럼이 없습니다.")
        
        df = data.copy()
        
        # RSI 계산
        df['RSI'] = self.calculate_rsi(df['Close'])
        
        # 신호 생성
        df['signal'] = SignalType.HOLD
        
        # 매수 신호: RSI가 과매도 구간에서 상승
        buy_condition = (df['RSI'] < self.oversold) & (df['RSI'].shift(1) >= self.oversold)
        df.loc[buy_condition, 'signal'] = SignalType.BUY
        
        # 매도 신호: RSI가 과매수 구간에서 하락
        sell_condition = (df['RSI'] > self.overbought) & (df['RSI'].shift(1) <= self.overbought)
        df.loc[sell_condition, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self) -> str:
        return f"RSI 전략 (기간: {self.rsi_period}일, 과매도: {self.oversold}, 과매수: {self.overbought})"

class RSIMeanReversionStrategy(BaseStrategy):
    """RSI 평균회귀 전략"""
    
    def __init__(self, rsi_period: int = 14, extreme_oversold: float = 20, extreme_overbought: float = 80):
        super().__init__("RSI Mean Reversion Strategy")
        self.rsi_period = rsi_period
        self.extreme_oversold = extreme_oversold
        self.extreme_overbought = extreme_overbought
        self.set_parameters(
            rsi_period=rsi_period,
            extreme_oversold=extreme_oversold,
            extreme_overbought=extreme_overbought
        )
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 평균회귀 신호 생성
        극단적 과매도에서 매수, 극단적 과매수에서 매도
        """
        if not self.validate_data(data):
            raise ValueError("데이터에 필요한 컬럼이 없습니다.")
        
        df = data.copy()
        
        # RSI 계산
        df['RSI'] = self.calculate_rsi(df['Close'])
        
        # 신호 생성
        df['signal'] = SignalType.HOLD
        
        # 매수 신호: 극단적 과매도
        buy_condition = df['RSI'] < self.extreme_oversold
        df.loc[buy_condition, 'signal'] = SignalType.BUY
        
        # 매도 신호: 극단적 과매수
        sell_condition = df['RSI'] > self.extreme_overbought
        df.loc[sell_condition, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self) -> str:
        return f"RSI 평균회귀 전략 (기간: {self.rsi_period}일, 극단 과매도: {self.extreme_oversold}, 극단 과매수: {self.extreme_overbought})"
