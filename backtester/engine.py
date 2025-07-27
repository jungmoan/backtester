import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import os

from data.loader import DataLoader
from data.preprocessor import DataPreprocessor
from strategies.base_strategy import BaseStrategy
from backtester.portfolio import Portfolio
from backtester.metrics import PerformanceMetrics
from config.config import Config

class BacktestEngine:
    def run_backtest_with_data(self, symbol: str, data: pd.DataFrame, position_size: float = None) -> Dict[str, Any]:
        """
        이미 로드된 데이터프레임으로 백테스트 실행
        Args:
            symbol: 주식 심볼
            data: 데이터프레임 (OHLCV 등)
            position_size: 포지션 크기 (총 자본 대비 비율)
        Returns:
            Dict: 백테스트 결과
        """
        print(f"\n=== 백테스트 시작 (데이터 직접 주입) ===")
        print(f"종목: {symbol}")
        print(f"전략: {self.strategy.get_description()}")
        print(f"초기자본: {self.initial_capital:,}원")

        if data.empty:
            print("데이터를 로드할 수 없습니다.")
            return {}

        # 데이터 전처리
        from data.preprocessor import DataPreprocessor
        preprocessor = DataPreprocessor()
        data = preprocessor.add_technical_indicators(data)
        data = preprocessor.clean_data(data)

        # 신호 생성
        data_with_signals = self.strategy.generate_signals(data)
        self.signals = data_with_signals

        # 포지션 크기 설정
        if position_size is None:
            position_size = Config.POSITION_SIZE

        # 백테스트 실행
        current_position = 0  # 0: 없음, 1: 보유
        for i, (date, row) in enumerate(data_with_signals.iterrows()):
            if pd.isna(row['signal']):
                continue
            current_price = row['Close']
            signal = int(row['signal'])
            # 매수 신호
            if signal == 1 and current_position == 0:
                invest_amount = self.portfolio.cash * position_size
                quantity = int(invest_amount / current_price)
                if quantity > 0:
                    success = self.portfolio.buy_stock(symbol, current_price, quantity, date)
                    if success:
                        current_position = 1
                        print(f"{date.strftime('%Y-%m-%d')}: 매수 - 가격: {current_price:,.0f}원, 수량: {quantity:,}주")
            # 매도 신호
            elif signal == -1 and current_position == 1:
                if symbol in self.portfolio.positions:
                    position = self.portfolio.positions[symbol]
                    success = self.portfolio.sell_stock(symbol, current_price, position.quantity, date)
                    if success:
                        current_position = 0
                        print(f"{date.strftime('%Y-%m-%d')}: 매도 - 가격: {current_price:,.0f}원, 수량: {position.quantity:,}주")
            # 포트폴리오 상태 기록
            self.portfolio.record_portfolio_state(date, {symbol: current_price})

        # 결과 생성
        portfolio_history = self.portfolio.get_portfolio_history_df()
        trade_history = self.portfolio.get_trade_history_df()
        from backtester.metrics import PerformanceMetrics
        performance_report = PerformanceMetrics.generate_performance_report(
            portfolio_history, trade_history, self.initial_capital
        )
        self.results = {
            'strategy': self.strategy.get_description(),
            'symbol': symbol,
            'period': f"{data_with_signals.index[0].strftime('%Y-%m-%d')} ~ {data_with_signals.index[-1].strftime('%Y-%m-%d')}",
            'portfolio_history': portfolio_history,
            'trade_history': trade_history,
            'performance_report': performance_report,
            'final_positions': self.portfolio.get_positions_summary({symbol: data_with_signals['Close'].iloc[-1]})
        }
        return self.results
    """백테스팅 엔진 클래스"""
    
    def __init__(self, strategy: BaseStrategy, initial_capital: float = None):
        self.strategy = strategy
        self.initial_capital = initial_capital or Config.INITIAL_CAPITAL
        self.commission_rate = Config.COMMISSION_RATE
        self.slippage_rate = Config.SLIPPAGE_RATE
        self.portfolio = Portfolio(self.initial_capital, self.commission_rate, self.slippage_rate)
        self.results = {}
        self.config = Config
        
    def run_backtest(self, symbol: str, start_date: str, end_date: str, 
                    position_size: float = None) -> Dict[str, Any]:
        """
        백테스트 실행
        
        Args:
            symbol: 주식 심볼
            start_date: 시작 날짜
            end_date: 종료 날짜
            position_size: 포지션 크기 (총 자본 대비 비율)
            
        Returns:
            Dict: 백테스트 결과
        """
        print(f"\n=== 백테스트 시작 ===")
        print(f"종목: {symbol}")
        print(f"전략: {self.strategy.get_description()}")
        print(f"기간: {start_date} ~ {end_date}")
        print(f"초기자본: {self.initial_capital:,}원")
        
        # 데이터 로드
        data_loader = DataLoader()
        data = data_loader.load_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            print("데이터를 로드할 수 없습니다.")
            return {}
        
        # 데이터 전처리
        preprocessor = DataPreprocessor()
        data = preprocessor.add_technical_indicators(data)
        data = preprocessor.clean_data(data)
        
        # 신호 생성
        data_with_signals = self.strategy.generate_signals(data)
        self.signals = data_with_signals
        
        # 포지션 크기 설정
        if position_size is None:
            position_size = Config.POSITION_SIZE
        
        # 백테스트 실행
        current_position = 0  # 0: 없음, 1: 보유
        
        for i, (date, row) in enumerate(data_with_signals.iterrows()):
            if pd.isna(row['signal']):
                continue
            current_price = row['Close']
            signal = int(row['signal'])
            
            # 매수 신호
            if signal == 1 and current_position == 0:
                # 투자 금액 계산
                invest_amount = self.portfolio.cash * position_size
                quantity = int(invest_amount / current_price)
                
                if quantity > 0:
                    success = self.portfolio.buy_stock(symbol, current_price, quantity, date)
                    if success:
                        current_position = 1
                        print(f"{date.strftime('%Y-%m-%d')}: 매수 - 가격: {current_price:,.0f}원, 수량: {quantity:,}주")
            
            # 매도 신호
            elif signal == -1 and current_position == 1:
                if symbol in self.portfolio.positions:
                    position = self.portfolio.positions[symbol]
                    success = self.portfolio.sell_stock(symbol, current_price, position.quantity, date)
                    if success:
                        current_position = 0
                        print(f"{date.strftime('%Y-%m-%d')}: 매도 - 가격: {current_price:,.0f}원, 수량: {position.quantity:,}주")
            
            # 포트폴리오 상태 기록
            self.portfolio.record_portfolio_state(date, {symbol: current_price})
        
        # 결과 생성
        portfolio_history = self.portfolio.get_portfolio_history_df()
        trade_history = self.portfolio.get_trade_history_df()
        
        # 성과 분석
        performance_report = PerformanceMetrics.generate_performance_report(
            portfolio_history, trade_history, self.initial_capital
        )
        
        self.results = {
            'strategy': self.strategy.get_description(),
            'symbol': symbol,
            'period': f"{start_date} ~ {end_date}",
            'portfolio_history': portfolio_history,
            'trade_history': trade_history,
            'performance_report': performance_report,
            'final_positions': self.portfolio.get_positions_summary({symbol: data_with_signals['Close'].iloc[-1]})
        }
        
        return self.results
    
    def print_results(self):
        """결과를 콘솔에 출력"""
        if not self.results:
            print("백테스트 결과가 없습니다.")
            return
        
        print(f"\n=== 백테스트 결과 ===")
        print(f"전략: {self.results['strategy']}")
        print(f"종목: {self.results['symbol']}")
        print(f"기간: {self.results['period']}")
        print()
        
        # 성과 지표 출력
        report = self.results['performance_report']
        print("📊 성과 지표")
        print("-" * 50)
        for key, value in report.items():
            print(f"{key}: {value}")
        
        print()
        
        # 거래 내역 출력
        trade_history = self.results['trade_history']
        if not trade_history.empty:
            print("📈 주요 거래 내역")
            print("-" * 50)
            print(trade_history.to_string(index=False))
        
        print()
        
        # 현재 포지션 출력
        positions = self.results['final_positions']
        if not positions.empty:
            print("💼 최종 포지션")
            print("-" * 50)
            print(positions.to_string(index=False))
    
    def save_results_to_csv(self, symbol: str, strategy_name: str) -> str:
        """백테스트 결과를 CSV 파일로 저장"""
        if not hasattr(self, 'results') or self.results is None:
            print("저장할 결과가 없습니다.")
            return ""
        
        # 파일명에 사용할 수 있도록 심볼 정리
        safe_symbol = symbol.replace('.', '_').replace('-', '_')
        safe_strategy = strategy_name.replace(' ', '_').replace('.', '_')
        
        # 날짜 제거된 파일명
        filename = f"{safe_symbol}_{safe_strategy}.csv"
        filepath = os.path.join(self.config.RESULTS_DIR, filename)
        
        # 결과 DataFrame 생성
        perf = self.results['performance_report']
        results_data = {
            'Metric': [
                'Total Return (%)',
                'Annual Return (%)',
                'Sharpe Ratio',
                'Maximum Drawdown (%)',
                'Win Rate (%)',
                'Profit Factor',
                'Total Trades',
                'Winning Trades',
                'Losing Trades',
                'Average Win (%)',
                'Average Loss (%)',
                'Largest Win (%)',
                'Largest Loss (%)',
                'Start Date',
                'End Date'
            ],
            'Value': [
                f"{perf.get('총수익률', '0.00%').replace('%', '')}",
                f"{perf.get('연환산수익률', '0.00%').replace('%', '')}",
                f"{perf.get('샤프비율', '0.0000')}",
                f"{perf.get('최대낙폭', '0.00%').replace('%', '')}",
                f"{perf.get('승률', '0.00%').replace('%', '')}",
                f"{perf.get('수익팩터', '0.0000')}",
                perf.get('총거래횟수', 0),
                perf.get('승리거래', 0),
                perf.get('패배거래', 0),
                '0.00',  # 평균 승리 수익률 (추후 구현)
                '0.00',  # 평균 손실 수익률 (추후 구현)
                '0.00',  # 최대 승리 수익률 (추후 구현)
                '0.00',  # 최대 손실 수익률 (추후 구현)
                perf.get('백테스트기간', 'N/A').split(' ~ ')[0] if ' ~ ' in perf.get('백테스트기간', 'N/A') else 'N/A',
                perf.get('백테스트기간', 'N/A').split(' ~ ')[1] if ' ~ ' in perf.get('백테스트기간', 'N/A') else 'N/A'
            ]
        }
        
        df = pd.DataFrame(results_data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        # trades 데이터도 저장
        trades_filename = f"{safe_symbol}_{safe_strategy}_trades.csv"
        trades_filepath = os.path.join(self.config.RESULTS_DIR, trades_filename)
        if 'trade_history' in self.results and not self.results['trade_history'].empty:
            trade_df = self.results['trade_history'].copy()
            # 컬럼명 맞추기 (trade_chart.py에서 기대하는 형식)
            if 'Date' in trade_df.columns:
                trade_df = trade_df.rename(columns={'Date': 'date'})
            if 'Action' in trade_df.columns:
                trade_df = trade_df.rename(columns={'Action': 'action'})
            if 'Price' in trade_df.columns:
                trade_df = trade_df.rename(columns={'Price': 'price'})
            trade_df.to_csv(trades_filepath, index=False, encoding='utf-8')
        
        print(f"결과가 저장되었습니다: {filepath}")
        
        # 차트 생성
        try:
            from visualization.trade_chart import plot_trade_signals
            chart_filename = f"{safe_symbol}_{safe_strategy}.png"
            chart_path = os.path.join(self.config.RESULTS_DIR, chart_filename)
            
            # trades_file은 이미 위에서 생성된 trades_filepath
            trades_file = trades_filepath
            
            # 백테스트 기간 (signals 데이터에서 추출)
            if hasattr(self, 'signals') and not self.signals.empty:
                start_date = self.signals.index.min().strftime('%Y-%m-%d')
                end_date = self.signals.index.max().strftime('%Y-%m-%d')
                plot_trade_signals(symbol, start_date, end_date, trades_file, chart_path)
                print(f"차트가 저장되었습니다: {chart_path}")
            else:
                print("신호 데이터가 없어 차트를 생성할 수 없습니다.")
        except Exception as e:
            import traceback
            print(f"차트 생성 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
        
        return filepath
    
    def get_results(self) -> Dict[str, Any]:
        """결과 반환"""
        return self.results
