import pandas as pd
import numpy as np
from typing import Dict, Any

class DataPreprocessor:
    """데이터 전처리 클래스"""
    
    @staticmethod
    def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 추가
        
        Args:
            data: 주식 데이터
            
        Returns:
            pd.DataFrame: 기술적 지표가 추가된 데이터
        """
        df = data.copy()
        
        # 이동평균선
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # 볼린저 밴드
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # 거래량 이동평균
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        # 가격 변화율
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_MA'] = df['Price_Change'].rolling(window=5).mean()
        
        return df
    
    @staticmethod
    def clean_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 정리
        
        Args:
            data: 원본 데이터
            
        Returns:
            pd.DataFrame: 정리된 데이터
        """
        df = data.copy()
        
        # 결측값 제거
        df = df.dropna()
        
        # 이상값 제거 (5% 이상의 급격한 변화)
        price_change = df['Close'].pct_change()
        df = df[abs(price_change) < 0.05]
        
        return df
    
    @staticmethod
    def add_market_features(data: pd.DataFrame) -> pd.DataFrame:
        """
        시장 특성 추가
        
        Args:
            data: 주식 데이터
            
        Returns:
            pd.DataFrame: 시장 특성이 추가된 데이터
        """
        df = data.copy()
        
        # 요일 정보
        df['Weekday'] = df.index.dayofweek
        df['IsMonday'] = (df['Weekday'] == 0).astype(int)
        df['IsFriday'] = (df['Weekday'] == 4).astype(int)
        
        # 월 정보
        df['Month'] = df.index.month
        
        # 변동성
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # 거래량 급증 여부
        df['Volume_Spike'] = (df['Volume'] > df['Volume_MA'] * 2).astype(int)
        
        return df
