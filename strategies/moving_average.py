import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, SignalType

class MovingAverageStrategy(BaseStrategy):
    """이동평균 교차 전략"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__("Moving Average Strategy")
        self.short_window = short_window
        self.long_window = long_window
        self.set_parameters(
            short_window=short_window,
            long_window=long_window
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        이동평균 교차 신호 생성
        단기 이동평균이 장기 이동평균을 상향 돌파하면 매수
        단기 이동평균이 장기 이동평균을 하향 돌파하면 매도
        """
        if not self.validate_data(data):
            raise ValueError("데이터에 필요한 컬럼이 없습니다.")
        
        df = data.copy()
        
        # 이동평균 계산
        df['MA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['MA_Long'] = df['Close'].rolling(window=self.long_window).mean()
        
        # 신호 생성
        df['signal'] = SignalType.HOLD
        
        # 골든크로스 (매수 신호)
        golden_cross = (df['MA_Short'] > df['MA_Long']) & (df['MA_Short'].shift(1) <= df['MA_Long'].shift(1))
        df.loc[golden_cross, 'signal'] = SignalType.BUY
        
        # 데드크로스 (매도 신호)
        dead_cross = (df['MA_Short'] < df['MA_Long']) & (df['MA_Short'].shift(1) >= df['MA_Long'].shift(1))
        df.loc[dead_cross, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self) -> str:
        return f"이동평균 교차 전략 (단기: {self.short_window}일, 장기: {self.long_window}일)"

class MovingAverageTrendStrategy(BaseStrategy):
    """이동평균 추세 전략"""
    
    def __init__(self, ma_window: int = 20, trend_threshold: float = 0.02):
        super().__init__("Moving Average Trend Strategy")
        self.ma_window = ma_window
        self.trend_threshold = trend_threshold
        self.set_parameters(
            ma_window=ma_window,
            trend_threshold=trend_threshold
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        이동평균 추세 신호 생성
        가격이 상승 추세의 이동평균선 위에 있으면 매수
        가격이 하락 추세의 이동평균선 아래에 있으면 매도
        """
        if not self.validate_data(data):
            raise ValueError("데이터에 필요한 컬럼이 없습니다.")
        
        df = data.copy()
        
        # 이동평균 계산
        df['MA'] = df['Close'].rolling(window=self.ma_window).mean()
        
        # 이동평균의 기울기 계산 (추세 판단)
        df['MA_Slope'] = df['MA'].pct_change(periods=5)
        
        # 신호 생성
        df['signal'] = SignalType.HOLD
        
        # 매수 신호: 가격 > 이동평균 & 이동평균 상승 추세
        buy_condition = (df['Close'] > df['MA']) & (df['MA_Slope'] > self.trend_threshold)
        df.loc[buy_condition, 'signal'] = SignalType.BUY
        
        # 매도 신호: 가격 < 이동평균 & 이동평균 하락 추세
        sell_condition = (df['Close'] < df['MA']) & (df['MA_Slope'] < -self.trend_threshold)
        df.loc[sell_condition, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self) -> str:
        return f"이동평균 추세 전략 (기간: {self.ma_window}일, 임계값: {self.trend_threshold:.1%})"
