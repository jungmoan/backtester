from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, Tuple

class BaseStrategy(ABC):
    """기본 전략 추상 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.parameters = {}
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        매매 신호 생성
        
        Args:
            data: 주식 데이터
            
        Returns:
            pd.DataFrame: 매매 신호가 추가된 데이터
                - 'signal': 1(매수), -1(매도), 0(관망)
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """전략 설명 반환"""
        pass
    
    def set_parameters(self, **kwargs):
        """전략 파라미터 설정"""
        self.parameters.update(kwargs)
    
    def get_parameters(self) -> Dict[str, Any]:
        """전략 파라미터 반환"""
        return self.parameters.copy()
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """데이터 유효성 검사"""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in data.columns for col in required_columns)

class SignalType:
    """신호 타입 상수"""
    BUY = 1      # 매수
    SELL = -1    # 매도
    HOLD = 0     # 관망
