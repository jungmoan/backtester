#!/usr/bin/env python3
"""
S&P 500 대량 백테스트 분석기
- 데이터 캐싱 (SQLite)
- 병렬 처리
- 성능 순위 분석
"""

import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple, Optional
import streamlit as st
from pathlib import Path

from strategies import StrategyManager
from backtest_engine import BacktestEngine


class SP500DataManager:
    """S&P 500 데이터 관리 및 캐싱"""
    
    def __init__(self, db_path: str = "sp500_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # S&P 500 종목 리스트 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sp500_symbols (
                symbol TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                last_updated TEXT
            )
        """)
        
        # 주가 데이터 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                last_updated TEXT,
                PRIMARY KEY (symbol, date)
            )
        """)
        
        # 백테스트 결과 캐시 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                symbol TEXT,
                strategy_name TEXT,
                strategy_params TEXT,
                period TEXT,
                total_return REAL,
                annual_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                total_trades INTEGER,
                profit_loss_ratio REAL,
                volatility REAL,
                last_updated TEXT,
                PRIMARY KEY (symbol, strategy_name, strategy_params, period)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_sp500_symbols(self, force_update: bool = False) -> List[Dict]:
        """S&P 500 종목 리스트 가져오기"""
        conn = sqlite3.connect(self.db_path)
        
        # 캐시된 데이터 확인
        if not force_update:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sp500_symbols LIMIT 1")
            if cursor.fetchone():
                df = pd.read_sql_query("SELECT * FROM sp500_symbols", conn)
                conn.close()
                # 문제가 있는 심볼들 필터링
                filtered_symbols = self._filter_valid_symbols(df.to_dict('records'))
                return filtered_symbols
        
        # 위키피디아에서 S&P 500 리스트 가져오기
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            
            # 컬럼명 정리
            df.columns = ['symbol', 'company_name', 'sector', 'industry', 'headquarters', 'date_added', 'cik', 'founded']
            df = df[['symbol', 'company_name', 'sector', 'industry']]
            
            # 심볼 정리 (특수 문자 처리)
            df['symbol'] = df['symbol'].str.replace('.', '-', regex=False)
            
            df['market_cap'] = 0.0  # 시가총액은 별도로 가져올 수 있음
            df['last_updated'] = datetime.now().isoformat()
            
            # 데이터베이스에 저장
            df.to_sql('sp500_symbols', conn, if_exists='replace', index=False)
            conn.close()
            
            # 문제가 있는 심볼들 필터링
            filtered_symbols = self._filter_valid_symbols(df.to_dict('records'))
            return filtered_symbols
            
        except Exception as e:
            print(f"Error fetching S&P 500 symbols: {e}")
            conn.close()
            return []
    
    def _filter_valid_symbols(self, symbols: List[Dict]) -> List[Dict]:
        """문제가 있는 심볼들을 필터링"""
        # 알려진 문제 심볼들 (클래스 B 주식, 특수문자 등)
        problematic_symbols = {
            'BRK.B', 'BF.B', 'BRK-B', 'BF-B',  # 클래스 B 주식
        }
        
        # 특수 문자나 문제가 있는 심볼들 제외
        valid_symbols = []
        for symbol_info in symbols:
            symbol = symbol_info['symbol']
            
            # 문제 심볼 제외
            if symbol in problematic_symbols:
                continue
                
            # 너무 긴 심볼 제외 (5자 이상)
            if len(symbol) > 5:
                continue
                
            # 숫자로만 구성된 심볼 제외
            if symbol.isdigit():
                continue
                
            valid_symbols.append(symbol_info)
        
        return valid_symbols
    
    def get_stock_data(self, symbol: str, period: str = "1y", force_update: bool = False) -> pd.DataFrame:
        """개별 종목 데이터 가져오기 (캐싱)"""
        conn = sqlite3.connect(self.db_path)
        
        # 캐시된 데이터 확인
        if not force_update:
            query = """
                SELECT * FROM stock_data 
                WHERE symbol = ? AND date >= ?
                ORDER BY date
            """
            
            # 기간 계산
            end_date = datetime.now()
            if period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "2y":
                start_date = end_date - timedelta(days=730)
            elif period == "5y":
                start_date = end_date - timedelta(days=1825)
            else:
                start_date = end_date - timedelta(days=365)
            
            df = pd.read_sql_query(query, conn, params=[symbol, start_date.strftime('%Y-%m-%d')])
            
            if not df.empty and len(df) > 200:  # 충분한 데이터가 있으면
                df['Date'] = pd.to_datetime(df['date'])
                df.set_index('Date', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                conn.close()
                return df
        
        # 새로운 데이터 다운로드
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # yfinance의 다양한 오류들을 처리
                ticker = yf.Ticker(symbol)
                
                # 짧은 타임아웃으로 빠르게 실패 처리
                data = ticker.history(period=period, timeout=10)
                
                # 데이터가 비어있거나 너무 적으면 실패
                if data.empty or len(data) < 50:
                    print(f"⚠️ {symbol}: 데이터 부족 ({len(data) if not data.empty else 0} rows)")
                    conn.close()
                    return pd.DataFrame()
                
                # 주말 제거 및 거래량 필터링
                data = data[data.index.dayofweek < 5]
                data = data[data['Volume'] > 0]
                
                # 다시 데이터 검증
                if len(data) < 50:
                    print(f"⚠️ {symbol}: 필터링 후 데이터 부족 ({len(data)} rows)")
                    conn.close()
                    return pd.DataFrame()
                
                # 데이터베이스에 저장
                data_to_save = data.reset_index()
                data_to_save['symbol'] = symbol
                data_to_save['date'] = data_to_save['Date'].dt.strftime('%Y-%m-%d')
                data_to_save['last_updated'] = datetime.now().isoformat()
                data_to_save = data_to_save[['symbol', 'date', 'Open', 'High', 'Low', 'Close', 'Volume', 'last_updated']]
                data_to_save.columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'last_updated']
                
                # 기존 데이터 삭제 후 새 데이터 삽입
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stock_data WHERE symbol = ?", [symbol])
                data_to_save.to_sql('stock_data', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                
                print(f"✅ {symbol}: 데이터 다운로드 성공 ({len(data)} rows)")
                return data
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e).lower()
                
                # 상장폐지나 심볼 오류 등은 재시도하지 않음
                if any(keyword in error_msg for keyword in ['delisted', 'no data found', 'not found', 'invalid']):
                    print(f"❌ {symbol}: 상장폐지 또는 유효하지 않은 심볼 - {e}")
                    conn.close()
                    return pd.DataFrame()
                
                # 네트워크 오류는 재시도
                if retry_count < max_retries:
                    print(f"⚠️ {symbol}: 재시도 {retry_count}/{max_retries} - {e}")
                    time.sleep(1)  # 1초 대기 후 재시도
                    continue
                else:
                    print(f"❌ {symbol}: 최대 재시도 초과 - {e}")
                    conn.close()
                    return pd.DataFrame()
    
    def get_cached_backtest_result(self, symbol: str, strategy_name: str, strategy_params: Dict, period: str) -> Optional[Dict]:
        """캐시된 백테스트 결과 가져오기"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        params_str = json.dumps(strategy_params, sort_keys=True)
        
        cursor.execute("""
            SELECT * FROM backtest_results 
            WHERE symbol = ? AND strategy_name = ? AND strategy_params = ? AND period = ?
        """, [symbol, strategy_name, params_str, period])
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['symbol', 'strategy_name', 'strategy_params', 'period', 'total_return', 
                      'annual_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades', 
                      'profit_loss_ratio', 'volatility', 'last_updated']
            return dict(zip(columns, result))
        return None
    
    def save_backtest_result(self, symbol: str, strategy_name: str, strategy_params: Dict, 
                           period: str, metrics: Dict):
        """백테스트 결과 캐시 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        params_str = json.dumps(strategy_params, sort_keys=True)
        
        cursor.execute("""
            INSERT OR REPLACE INTO backtest_results 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            symbol, strategy_name, params_str, period,
            metrics.get('total_return', 0),
            metrics.get('annual_return', 0),
            metrics.get('sharpe_ratio', 0),
            metrics.get('max_drawdown', 0),
            metrics.get('win_rate', 0),
            metrics.get('total_trades', 0),
            metrics.get('profit_loss_ratio', 0),
            metrics.get('volatility', 0),
            datetime.now().isoformat()
        ])
        
        conn.commit()
        conn.close()


class SP500BacktestRunner:
    """S&P 500 대량 백테스트 실행기"""
    
    def __init__(self, initial_capital: float = 10000):
        self.data_manager = SP500DataManager()
        self.strategy_manager = StrategyManager()
        self.initial_capital = initial_capital
        
    def run_single_backtest(self, symbol: str, strategy_name: str, strategy_params: Dict, 
                          period: str = "1y", use_cache: bool = True) -> Dict:
        """단일 종목 백테스트"""
        
        # 캐시 확인
        if use_cache:
            cached_result = self.data_manager.get_cached_backtest_result(
                symbol, strategy_name, strategy_params, period
            )
            if cached_result:
                return cached_result
        
        # 데이터 가져오기
        data = self.data_manager.get_stock_data(symbol, period)
        if data.empty:
            return {'symbol': symbol, 'error': 'No data available', 'skip': True}
        
        # 데이터 품질 검증
        if len(data) < 50:
            return {'symbol': symbol, 'error': 'Insufficient data', 'skip': True}
        
        # NaN 값 확인
        if data.isnull().any().any():
            data = data.dropna()
            if len(data) < 50:
                return {'symbol': symbol, 'error': 'Too many NaN values', 'skip': True}
        
        # 전략 신호 계산 (exception 처리 제거)
        strategy_data = self.strategy_manager.calculate_signals(strategy_name, data, **strategy_params)
        
        # 신호 데이터 검증
        if strategy_data.empty or len(strategy_data) < 50:
            return {'symbol': symbol, 'error': 'Strategy calculation failed', 'skip': True}
        
        # 백테스트 실행
        engine = BacktestEngine(self.initial_capital)
        result = engine.run_backtest(data, strategy_data)
        metrics = engine.calculate_metrics(result)
        
        # 메트릭스 검증
        if not metrics or metrics.get('total_trades', 0) == 0:
            return {'symbol': symbol, 'error': 'No trades generated', 'skip': True}
        
        # 결과에 심볼 추가
        metrics['symbol'] = symbol
        
        # 캐시 저장
        self.data_manager.save_backtest_result(symbol, strategy_name, strategy_params, period, metrics)
        
        return metrics
    
    def run_parallel_backtests(self, symbols: List[str], strategy_name: str, strategy_params: Dict, 
                             period: str = "1y", max_workers: int = 10, use_cache: bool = True) -> pd.DataFrame:
        """병렬 백테스트 실행"""
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_summary = {'data_errors': [], 'strategy_errors': [], 'other_errors': []}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            future_to_symbol = {
                executor.submit(self.run_single_backtest, symbol, strategy_name, strategy_params, period, use_cache): symbol
                for symbol in symbols
            }
            
            # 결과 수집
            completed = 0
            successful = 0
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 성공/실패 분류
                    if 'error' not in result:
                        successful += 1
                    else:
                        error_msg = result['error']
                        if 'data' in error_msg.lower() or 'delisted' in error_msg.lower():
                            error_summary['data_errors'].append(symbol)
                        elif 'strategy' in error_msg.lower() or 'squeeze' in error_msg.lower():
                            error_summary['strategy_errors'].append(symbol)
                        else:
                            error_summary['other_errors'].append(symbol)
                    
                except Exception as e:
                    results.append({'symbol': symbol, 'error': str(e), 'skip': True})
                    error_summary['other_errors'].append(symbol)
                
                completed += 1
                progress = completed / len(symbols)
                progress_bar.progress(progress)
                status_text.text(f"Processing {symbol}... ({successful}/{completed} successful)")
        
        progress_bar.empty()
        status_text.empty()
        
        # 오류 요약 표시
        total_errors = sum(len(errors) for errors in error_summary.values())
        if total_errors > 0:
            st.warning(f"⚠️ 총 {total_errors}개 종목에서 오류 발생:")
            
            if error_summary['data_errors']:
                st.error(f"📊 데이터 오류 ({len(error_summary['data_errors'])}개): {error_summary['data_errors'][:5]}{'...' if len(error_summary['data_errors']) > 5 else ''}")
            
            if error_summary['strategy_errors']:
                st.warning(f"🔧 전략 계산 오류 ({len(error_summary['strategy_errors'])}개): {error_summary['strategy_errors'][:5]}{'...' if len(error_summary['strategy_errors']) > 5 else ''}")
            
            if error_summary['other_errors']:
                st.info(f"❓ 기타 오류 ({len(error_summary['other_errors'])}개): {error_summary['other_errors'][:5]}{'...' if len(error_summary['other_errors']) > 5 else ''}")
        
        # DataFrame으로 변환 (성공한 결과만)
        df = pd.DataFrame(results)
        
        # 에러가 없는 결과만 필터링
        if 'error' in df.columns:
            valid_df = df[df['error'].isna()].copy()
            valid_df = valid_df.drop(columns=['error', 'skip'], errors='ignore')
        else:
            valid_df = df.copy()
        
        st.success(f"✅ {len(valid_df)}개 종목 분석 완료 (성공률: {len(valid_df)/len(symbols)*100:.1f}%)")
        
        return valid_df
    
    def get_top_performers(self, results_df: pd.DataFrame, metric: str = 'total_return', top_n: int = 20) -> pd.DataFrame:
        """성과 상위 종목 분석"""
        if results_df.empty:
            return pd.DataFrame()
        
        # 유효한 결과만 필터링
        valid_results = results_df.dropna(subset=[metric])
        
        # 상위 종목 선별
        top_performers = valid_results.nlargest(top_n, metric)
        
        return top_performers[['symbol', 'total_return', 'annual_return', 'sharpe_ratio', 
                              'max_drawdown', 'win_rate', 'total_trades', 'profit_loss_ratio']]
    
    def analyze_sector_performance(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """섹터별 성과 분석"""
        if results_df.empty:
            return pd.DataFrame()
        
        # S&P 500 심볼 정보와 조인
        symbols_info = self.data_manager.get_sp500_symbols()
        symbols_df = pd.DataFrame(symbols_info)
        
        # 결과와 섹터 정보 병합
        merged = results_df.merge(symbols_df[['symbol', 'sector']], on='symbol', how='left')
        
        # 섹터별 평균 성과 계산
        sector_performance = merged.groupby('sector').agg({
            'total_return': ['mean', 'median', 'std', 'count'],
            'sharpe_ratio': 'mean',
            'win_rate': 'mean',
            'max_drawdown': 'mean'
        }).round(2)
        
        # 컬럼명 정리
        sector_performance.columns = ['avg_return', 'median_return', 'return_std', 'count', 
                                    'avg_sharpe', 'avg_win_rate', 'avg_max_drawdown']
        
        return sector_performance.sort_values('avg_return', ascending=False)


def create_strategy_controls(strategy_name: str) -> Dict:
    """전략별 파라미터 컨트롤 생성"""
    
    if strategy_name == "Moving Average":
        return {
            'short': st.sidebar.slider("📈 Short MA", 5, 30, 20, help="단기 이동평균 기간"),
            'long': st.sidebar.slider("📈 Long MA", 20, 100, 50, help="장기 이동평균 기간")
        }
    
    elif strategy_name == "RSI":
        return {
            'period': st.sidebar.slider("📊 RSI Period", 10, 30, 14, help="RSI 계산 기간"),
            'oversold': st.sidebar.slider("📉 Oversold", 20, 40, 30, help="과매도 기준선"),
            'overbought': st.sidebar.slider("� Overbought", 60, 80, 70, help="과매수 기준선")
        }
    
    elif strategy_name == "Bollinger Bands":
        return {
            'period': st.sidebar.slider("📊 BB Period", 10, 30, 20, help="볼린저 밴드 기간"),
            'std': st.sidebar.slider("📏 BB Std", 1.5, 3.0, 2.0, 0.1, help="표준편차 승수")
        }
    
    elif strategy_name == "MACD":
        return {
            'fast': st.sidebar.slider("⚡ Fast EMA", 8, 15, 12, help="빠른 EMA 기간"),
            'slow': st.sidebar.slider("🐌 Slow EMA", 20, 30, 26, help="느린 EMA 기간"),
            'signal': st.sidebar.slider("📶 Signal", 7, 12, 9, help="신호선 기간")
        }
    
    elif strategy_name == "Stochastic":
        return {
            'k_period': st.sidebar.slider("� %K Period", 10, 20, 14, help="%K 기간"),
            'd_period': st.sidebar.slider("📈 %D Period", 3, 7, 3, help="%D 기간"),
            'oversold': st.sidebar.slider("📉 Oversold", 15, 25, 20, help="과매도 기준선"),
            'overbought': st.sidebar.slider("� Overbought", 75, 85, 80, help="과매수 기준선")
        }
    
    elif strategy_name == "Squeeze Momentum":
        return {
            'bb_period': st.sidebar.slider("📈 BB Period", 10, 30, 20, help="볼린저 밴드 기간"),
            'bb_std': st.sidebar.slider("📈 BB Std Dev", 1.5, 2.5, 2.0, 0.1, help="볼린저 밴드 표준편차 승수"),
            'kc_period': st.sidebar.slider("⚡ KC Period", 10, 30, 20, help="켈트너 채널 기간"),
            'kc_mult': st.sidebar.slider("⚡ KC Multiplier", 1.0, 2.5, 1.5, 0.1, help="켈트너 채널 승수"),
            'momentum_period': st.sidebar.slider("🚀 Momentum Period", 8, 20, 12, help="모멘텀 기간"),
            'ema_period': st.sidebar.slider("📈 EMA Filter", 50, 300, 200, help="EMA 필터 기간")
        }
    
    else:
        return {}


def get_strategy_description(strategy_name: str) -> str:
    """전략별 설명 반환"""
    descriptions = {
        "Moving Average": "이동평균 크로스오버 전략: 단기/장기 이동평균선의 교차로 매매 신호 생성",
        "RSI": "상대강도지수 전략: 과매수/과매도 구간에서 역추세 매매",
        "Bollinger Bands": "볼린저 밴드 전략: 가격의 밴드 이탈 및 회귀를 이용한 매매",
        "MACD": "MACD 전략: 이동평균수렴확산 지표의 신호선 교차로 매매",
        "Stochastic": "스토캐스틱 전략: %K와 %D선의 교차와 과매수/과매도 구간 활용",
        "Squeeze Momentum": "TTM Squeeze 전략: 변동성 압축 해제 후 모멘텀 방향으로 매매 (200일 EMA 필터 추가)"
    }
    return descriptions.get(strategy_name, "선택된 전략에 대한 설명입니다.")


def create_sp500_analysis_page():
    """S&P 500 분석 페이지 생성"""
    st.title("🏆 S&P 500 Strategy Analysis")
    st.markdown("### 📊 All Trading Strategies Performance Analysis")
    
    # 사이드바 설정
    st.sidebar.header("⚙️ Analysis Settings")
    
    # 전략 선택
    st.sidebar.subheader("🎯 Strategy Selection")
    
    # 사용 가능한 전략 목록 가져오기
    from strategies import StrategyManager
    strategy_manager = StrategyManager()
    available_strategies = strategy_manager.get_available_strategies()
    
    selected_strategy = st.sidebar.selectbox(
        "Choose Strategy",
        available_strategies,
        index=available_strategies.index("Squeeze Momentum") if "Squeeze Momentum" in available_strategies else 0,
        help="분석할 전략을 선택하세요"
    )
    
    # 선택된 전략에 대한 설명
    st.sidebar.info(get_strategy_description(selected_strategy))
    
    # 기간 선택
    period = st.sidebar.selectbox("📅 Analysis Period", ["1y", "2y", "5y"], index=0)
    
    # 전략별 파라미터 설정
    st.sidebar.subheader(f"🔧 {selected_strategy} Parameters")
    strategy_params = create_strategy_controls(selected_strategy)
    
    # 분석 옵션
    st.sidebar.subheader("🎯 Analysis Options")
    use_cache = st.sidebar.checkbox("Use Cache", value=True, help="캐시된 결과 사용 (빠른 분석)")
    max_workers = st.sidebar.slider("🔄 Parallel Workers", 5, 20, 10, help="병렬 처리 스레드 수")
    top_n = st.sidebar.slider("🏆 Top N Stocks", 10, 50, 20, help="상위 몇 개 종목 표시")
    
    # 테스트 모드 추가
    test_mode = st.sidebar.checkbox("🧪 Test Mode", value=False, help="소수 종목으로 먼저 테스트")
    if test_mode:
        test_symbols_count = st.sidebar.slider("테스트 종목 수", 10, 100, 50, help="테스트할 종목 개수")
    
    # 실행 버튼
    run_analysis = st.sidebar.button("🚀 RUN SP500 ANALYSIS", type="primary", use_container_width=True)
    
    if run_analysis:
        runner = SP500BacktestRunner()
        
        # S&P 500 종목 리스트 가져오기
        with st.spinner("S&P 500 종목 리스트 로딩..."):
            symbols_info = runner.data_manager.get_sp500_symbols()
            all_symbols = [info['symbol'] for info in symbols_info]
            
            # 테스트 모드인 경우 일부만 선택
            if test_mode:
                symbols = all_symbols[:test_symbols_count]
                st.info(f"🧪 테스트 모드: {len(symbols)}개 종목으로 제한")
            else:
                symbols = all_symbols
        
        st.success(f"✅ {len(symbols)}개 종목 로딩 완료 (전체 S&P 500: {len(all_symbols)}개)")
        
        # 병렬 백테스트 실행
        st.subheader(f"🔄 Running {selected_strategy} Backtests")
        start_time = time.time()
        
        results_df = runner.run_parallel_backtests(
            symbols, selected_strategy, strategy_params, period, max_workers, use_cache
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if not results_df.empty:
            st.success(f"✅ {selected_strategy} 분석 완료! ({len(results_df)}개 종목, {execution_time:.1f}초)")
            
            # 전체 통계
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("분석 종목 수", len(results_df))
            with col2:
                avg_return = results_df['total_return'].mean()
                st.metric("평균 수익률", f"{avg_return:.1f}%")
            with col3:
                positive_returns = (results_df['total_return'] > 0).sum()
                success_rate = (positive_returns / len(results_df)) * 100
                st.metric("성공률", f"{success_rate:.1f}%")
            with col4:
                avg_sharpe = results_df['sharpe_ratio'].mean()
                st.metric("평균 샤프비율", f"{avg_sharpe:.2f}")
            
            # 상위 성과 종목
            st.subheader(f"🏆 Top {top_n} {selected_strategy} Performers")
            top_performers = runner.get_top_performers(results_df, 'total_return', top_n)
            
            if not top_performers.empty:
                st.dataframe(
                    top_performers.style.format({
                        'total_return': '{:.1f}%',
                        'annual_return': '{:.1f}%',
                        'sharpe_ratio': '{:.2f}',
                        'max_drawdown': '{:.1f}%',
                        'win_rate': '{:.1f}%',
                        'profit_loss_ratio': '{:.2f}'
                    }),
                    use_container_width=True
                )
                
                # 상위 종목 차트
                st.subheader("📊 Top Performers Distribution")
                col1, col2 = st.columns(2)
                
                with col1:
                    import plotly.express as px
                    fig = px.histogram(results_df, x='total_return', nbins=30, 
                                     title="수익률 분포", labels={'total_return': '수익률 (%)'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(results_df, x='sharpe_ratio', y='total_return', 
                                   title="샤프비율 vs 수익률", 
                                   labels={'sharpe_ratio': '샤프비율', 'total_return': '수익률 (%)'})
                    st.plotly_chart(fig, use_container_width=True)
            
            # 섹터별 분석
            st.subheader("🏢 Sector Performance Analysis")
            sector_performance = runner.analyze_sector_performance(results_df)
            
            if not sector_performance.empty:
                st.dataframe(
                    sector_performance.style.format({
                        'avg_return': '{:.1f}%',
                        'median_return': '{:.1f}%',
                        'return_std': '{:.1f}%',
                        'avg_sharpe': '{:.2f}',
                        'avg_win_rate': '{:.1f}%',
                        'avg_max_drawdown': '{:.1f}%'
                    }),
                    use_container_width=True
                )
            
            # 전체 결과 다운로드
            st.subheader("📥 Download Results")
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Results (CSV)",
                data=csv,
                file_name=f"sp500_smi_analysis_{period}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        else:
            st.error("❌ 분석 결과가 없습니다. 설정을 확인해주세요.")


if __name__ == "__main__":
    create_sp500_analysis_page()
