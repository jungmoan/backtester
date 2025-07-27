import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import pickle
from typing import List, Dict
import time

class SP500DataManager:
    """S&P 500 데이터 관리 클래스"""
    
    def __init__(self, data_dir: str = "sp500_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def get_sp500_symbols(self) -> List[str]:
        """S&P 500 심볼 리스트 가져오기"""
        try:
            # Wikipedia에서 S&P 500 리스트 가져오기
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_table = tables[0]
            symbols = sp500_table['Symbol'].tolist()
            
            # 일부 심볼 정리 (특수문자 제거)
            clean_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str):
                    # BRK.B -> BRK-B 변환 등
                    clean_symbol = symbol.replace('.', '-')
                    clean_symbols.append(clean_symbol)
            
            print(f"S&P 500 심볼 {len(clean_symbols)}개를 가져왔습니다.")
            return clean_symbols
            
        except Exception as e:
            import traceback
            print(f"S&P 500 리스트를 가져오는 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
            # 백업 리스트 (일부 주요 종목들)
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B',
                'UNH', 'XOM', 'JNJ', 'JPM', 'V', 'PG', 'AVGO', 'HD', 'CVX', 'MA',
                'ABBV', 'PFE', 'COST', 'KO', 'MRK', 'TMO', 'PEP', 'BAC', 'NFLX',
                'ADBE', 'DIS', 'WMT', 'CRM', 'DHR', 'VZ', 'ABT', 'CMCSA', 'NKE',
                'ACN', 'TXN', 'QCOM', 'RTX', 'HON', 'NEE', 'PM', 'T', 'SPGI',
                'LOW', 'UNP', 'GE', 'IBM', 'CAT', 'SBUX', 'AXP', 'BLK', 'DE'
            ]
    
    def download_sp500_data(self, years: int = 5) -> Dict[str, pd.DataFrame]:
        """
        S&P 500 전체 데이터 다운로드 및 저장
        
        Args:
            years: 다운로드할 년수
            
        Returns:
            Dict: {symbol: DataFrame} 형태의 딕셔너리
        """
        symbols = self.get_sp500_symbols()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        cache_file = os.path.join(self.data_dir, f"sp500_data_{years}years.pkl")
        
        # 캐시 파일이 있고 최신이면 로드
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.now() - file_time).days < 1:  # 1일 이내면 캐시 사용
                print("캐시된 데이터를 로드합니다...")
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        print(f"S&P 500 데이터 다운로드 시작... ({len(symbols)}개 종목, {years}년간)")
        print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        all_data = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            try:
                print(f"[{i+1}/{len(symbols)}] {symbol} 다운로드 중...")
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if not data.empty and len(data) > 100:  # 최소 100일 데이터
                    # 컬럼명 영어로 통일
                    data.index.name = 'Date'
                    all_data[symbol] = data
                    print(f"  ✅ {symbol}: {len(data)} 일간 데이터")
                else:
                    failed_symbols.append(symbol)
                    print(f"  ❌ {symbol}: 데이터 부족 또는 없음")
                
                # API 제한을 위한 지연
                time.sleep(0.1)
                
            except Exception as e:
                import traceback
                failed_symbols.append(symbol)
                print(f"  ❌ {symbol}: 오류 - {e}")
                print(f"  📋 상세 오류:")
                traceback.print_exc()
                continue
        
        # 결과 저장
        with open(cache_file, 'wb') as f:
            pickle.dump(all_data, f)
        
        print(f"\n✅ 다운로드 완료!")
        print(f"성공: {len(all_data)}개 종목")
        print(f"실패: {len(failed_symbols)}개 종목")
        if failed_symbols:
            print(f"실패한 종목들: {failed_symbols[:10]}{'...' if len(failed_symbols) > 10 else ''}")
        
        return all_data
    
    def get_symbol_data(self, symbol: str, data_cache: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """특정 심볼의 데이터 반환"""
        if symbol in data_cache:
            return data_cache[symbol].copy()
        else:
            print(f"⚠️  {symbol} 데이터를 찾을 수 없습니다.")
            return pd.DataFrame()
    
    def clean_symbol_for_filename(self, symbol: str) -> str:
        """파일명에 사용할 수 있도록 심볼 정리"""
        return symbol.replace('-', '_').replace('.', '_')
