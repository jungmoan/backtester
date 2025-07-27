import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

class DataLoader:
    """주식 데이터 로더 클래스"""
    
    def __init__(self):
        self.data_cache = {}
    
    def load_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        주식 데이터 로드
        
        Args:
            symbol: 주식 심볼 (예: 'AAPL', '005930.KS')
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: 주식 데이터
        """
        cache_key = f"{symbol}_{start_date}_{end_date}"
        
        if cache_key in self.data_cache:
            print(f"캐시에서 {symbol} 데이터를 로드합니다.")
            return self.data_cache[cache_key]
        
        try:
            print(f"{symbol} 데이터를 다운로드 중...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                raise ValueError(f"{symbol}에 대한 데이터를 찾을 수 없습니다.")
            
            # 컬럼명 영어로 통일
            # (yfinance 기본 컬럼명 사용: Open, High, Low, Close, Volume, Dividends, Stock Splits)
            data.index.name = 'Date'
            
            # 캐시에 저장
            self.data_cache[cache_key] = data.copy()
            
            print(f"{symbol} 데이터 로드 완료: {len(data)} 일간 데이터")
            return data
            
        except Exception as e:
            import traceback
            print(f"데이터 로드 중 오류 발생: {e}")
            print("상세 오류:")
            traceback.print_exc()
            return pd.DataFrame()
    
    def load_multiple_stocks(self, symbols: List[str], start_date: str, end_date: str) -> dict:
        """
        여러 주식 데이터 로드
        
        Args:
            symbols: 주식 심볼 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            dict: {symbol: DataFrame} 형태의 딕셔너리
        """
        data_dict = {}
        
        for symbol in symbols:
            data = self.load_stock_data(symbol, start_date, end_date)
            if not data.empty:
                data_dict[symbol] = data
        
        return data_dict
    
    def get_korean_stocks_examples(self) -> List[str]:
        """한국 주식 예제 심볼 반환"""
        return [
            '005930.KS',  # 삼성전자
            '000660.KS',  # SK하이닉스
            '035420.KS',  # NAVER
            '051910.KS',  # LG화학
            '006400.KS',  # 삼성SDI
        ]
    
    def get_us_stocks_examples(self) -> List[str]:
        """미국 주식 예제 심볼 반환"""
        return [
            'AAPL',   # Apple
            'GOOGL',  # Google
            'MSFT',   # Microsoft
            'TSLA',   # Tesla
            'NVDA',   # NVIDIA
        ]
