#!/usr/bin/env python3
"""
가벼운 S&P 500 백테스팅 시스템
- 메모리 최적화
- 불필요한 파일 저장 최소화
- 빠른 실행
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class LightBacktester:
    """가벼운 백테스터"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        
    def calculate_ma_signals(self, data: pd.DataFrame, short: int = 20, long: int = 50) -> pd.Series:
        """이동평균 신호"""
        ma_short = data['Close'].rolling(short).mean()
        ma_long = data['Close'].rolling(long).mean()
        signals = pd.Series(0, index=data.index)
        signals[ma_short > ma_long] = 1
        signals[ma_short < ma_long] = -1
        return signals.diff().fillna(0)  # 변화점만
    
    def calculate_rsi_signals(self, data: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.Series:
        """RSI 신호"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=data.index)
        signals[(rsi < oversold)] = 1  # 매수
        signals[(rsi > overbought)] = -1  # 매도
        return signals.diff().fillna(0)
    
    def run_simple_backtest(self, prices: pd.Series, signals: pd.Series) -> Dict:
        """간단한 백테스트"""
        cash = self.initial_capital
        position = 0
        portfolio_value = []
        trades = []  # 거래 기록
        buy_price = 0
        
        for i, (date, price) in enumerate(prices.items()):
            signal = signals.iloc[i] if i < len(signals) else 0
            
            # 매수
            if signal == 1 and position == 0:
                shares = cash * 0.95 / price  # 95% 투자
                cash -= shares * price
                position = shares
                buy_price = price
            
            # 매도
            elif signal == -1 and position > 0:
                cash += position * price
                # 거래 수익률 기록
                trade_return = (price - buy_price) / buy_price * 100
                trades.append(trade_return)
                position = 0
                buy_price = 0
            
            # 포트폴리오 가치
            total_value = cash + position * price
            portfolio_value.append(total_value)
        
        # 최종 청산
        if position > 0:
            final_price = prices.iloc[-1]
            cash += position * final_price
            # 마지막 거래 기록
            if buy_price > 0:
                trade_return = (final_price - buy_price) / buy_price * 100
                trades.append(trade_return)
            position = 0
        
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # 간단한 성과 지표
        portfolio_series = pd.Series(portfolio_value, index=prices.index)
        returns = portfolio_series.pct_change().dropna()
        
        # 승률 계산
        win_rate = 0
        total_trades = len(trades)
        if total_trades > 0:
            winning_trades = sum(1 for trade in trades if trade > 0)
            win_rate = (winning_trades / total_trades) * 100
        
        return {
            'total_return': total_return,
            'final_value': final_value,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': ((portfolio_series / portfolio_series.expanding().max() - 1) * 100).min(),
            'volatility': returns.std() * np.sqrt(252) * 100,
            'win_rate': win_rate,
            'total_trades': total_trades
        }

class CompactSP500Tester:
    """가벼운 S&P 500 테스터"""
    
    def __init__(self, sample_size: int = 20):
        self.sample_size = sample_size
        self.backtester = LightBacktester()
        
        # S&P 500 심볼 (인기 종목만)
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'WMT', 'LLY',
            'JPM', 'V', 'UNH', 'ORCL', 'MA', 'HD', 'PG', 'JNJ', 'MRK', 'CVX',
            'ABBV', 'COST', 'PEP', 'KO', 'ADBE', 'WFC', 'BAC', 'CRM', 'NFLX', 'AMD',
            'DIS', 'PFE', 'TMO', 'ACN', 'LIN', 'CSCO', 'ABT', 'VZ', 'TXN', 'INTC'
        ][:sample_size]
        
        # 전략 정의
        self.strategies = {
            'MA_Cross': lambda data: self.backtester.calculate_ma_signals(data, 20, 50),
            'MA_Fast': lambda data: self.backtester.calculate_ma_signals(data, 5, 20),
            'RSI_Classic': lambda data: self.backtester.calculate_rsi_signals(data, 14, 30, 70),
            'RSI_Aggressive': lambda data: self.backtester.calculate_rsi_signals(data, 14, 20, 80)
        }
    
    def load_data_batch(self, period: str = "2y") -> Dict[str, pd.DataFrame]:
        """배치로 데이터 로드"""
        print(f"📊 {len(self.symbols)}개 종목 데이터 로드 중...")
        
        data = {}
        failed = []
        
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
                if not df.empty and len(df) > 100:  # 최소 데이터 확인
                    data[symbol] = df[['Close']].dropna()
                else:
                    failed.append(symbol)
            except:
                failed.append(symbol)
        
        if failed:
            print(f"⚠️  로드 실패: {failed}")
        
        print(f"✅ {len(data)}개 종목 데이터 로드 완료")
        return data
    
    def run_compact_backtest(self) -> pd.DataFrame:
        """컴팩트 백테스트 실행"""
        print("🚀 컴팩트 백테스트 시작")
        start_time = time.time()
        
        # 데이터 로드
        data = self.load_data_batch()
        
        results = []
        total_tests = len(data) * len(self.strategies)
        current_test = 0
        
        print(f"🔄 총 {total_tests}개 테스트 실행...")
        
        for symbol, df in data.items():
            for strategy_name, strategy_func in self.strategies.items():
                current_test += 1
                
                try:
                    # 신호 생성
                    signals = strategy_func(df)
                    
                    # 백테스트 실행
                    result = self.backtester.run_simple_backtest(df['Close'], signals)
                    
                    # 결과 저장
                    results.append({
                        'Symbol': symbol,
                        'Strategy': strategy_name,
                        'Total_Return': round(result['total_return'], 2),
                        'Sharpe_Ratio': round(result['sharpe_ratio'], 3),
                        'Max_Drawdown': round(result['max_drawdown'], 2),
                        'Volatility': round(result['volatility'], 2),
                        'Win_Rate': round(result['win_rate'], 1),
                        'Total_Trades': result['total_trades']
                    })
                    
                    # 진행률 표시 (10% 단위)
                    if current_test % max(1, total_tests // 10) == 0:
                        progress = (current_test / total_tests) * 100
                        print(f"   진행률: {progress:.0f}% ({current_test}/{total_tests})")
                
                except Exception as e:
                    print(f"❌ {symbol} - {strategy_name} 실패: {str(e)[:50]}...")
                    continue
        
        # 결과 DataFrame 생성
        results_df = pd.DataFrame(results)
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ 백테스트 완료! 소요시간: {elapsed_time:.1f}초")
        print(f"📊 총 {len(results_df)}개 결과 생성")
        
        return results_df
    
    def analyze_results(self, results_df: pd.DataFrame) -> None:
        """결과 분석 및 출력"""
        print("\n" + "="*80)
        print("📈 S&P 500 컴팩트 백테스트 결과 분석")
        print("="*80)
        
        # 전략별 요약
        strategy_summary = results_df.groupby('Strategy').agg({
            'Total_Return': ['count', 'mean', 'std', 'min', 'max'],
            'Sharpe_Ratio': ['mean', 'std'],
            'Max_Drawdown': ['mean', 'std'],
            'Win_Rate': ['mean', 'std'],
            'Total_Trades': ['mean', 'std']
        }).round(3)
        
        print("\n🎯 전략별 성과 요약:")
        print("-" * 80)
        
        for strategy in results_df['Strategy'].unique():
            data = results_df[results_df['Strategy'] == strategy]
            
            # 성과 지표
            avg_return = data['Total_Return'].mean()
            std_return = data['Total_Return'].std()
            avg_sharpe = data['Sharpe_Ratio'].mean()
            avg_win_rate = data['Win_Rate'].mean()
            avg_trades = data['Total_Trades'].mean()
            win_rate_from_returns = (data['Total_Return'] > 0).mean() * 100  # 양수 수익률 비율
            
            print(f"\n📊 {strategy}:")
            print(f"   테스트 수: {len(data)}개")
            print(f"   평균 수익률: {avg_return:.2f}% (±{std_return:.2f}%)")
            print(f"   평균 샤프비율: {avg_sharpe:.3f}")
            print(f"   평균 승률: {avg_win_rate:.1f}% (거래기준)")
            print(f"   양수수익률 비율: {win_rate_from_returns:.1f}% (종목기준)")
            print(f"   평균 거래횟수: {avg_trades:.1f}회")
            
            # 상위 종목
            top3 = data.nlargest(3, 'Total_Return')
            print(f"   🏆 상위 3개:")
            for _, row in top3.iterrows():
                print(f"      {row['Symbol']}: {row['Total_Return']}% (샤프: {row['Sharpe_Ratio']}, 승률: {row['Win_Rate']}%)")
        
        # 전체 베스트
        print(f"\n🏆 전체 최고 성과 TOP 10:")
        print("-" * 60)
        top_performers = results_df.nlargest(10, 'Total_Return')
        for i, (_, row) in enumerate(top_performers.iterrows(), 1):
            print(f"   {i:2d}. {row['Symbol']} ({row['Strategy']}): {row['Total_Return']}%")
        
        # 요약 통계
        print(f"\n📋 전체 통계:")
        print(f"   평균 수익률: {results_df['Total_Return'].mean():.2f}%")
        print(f"   중간값 수익률: {results_df['Total_Return'].median():.2f}%")
        print(f"   양수 수익률 비율: {(results_df['Total_Return'] > 0).mean()*100:.1f}%")
        print(f"   최고 수익률: {results_df['Total_Return'].max():.2f}%")
        print(f"   최저 수익률: {results_df['Total_Return'].min():.2f}%")

def main():
    """메인 실행"""
    print("🚀 S&P 500 컴팩트 백테스팅 시스템")
    print("="*60)
    
    # 설정
    sample_size = 30  # 테스트할 종목 수 (기본 30개)
    
    # 사용자 입력
    try:
        user_input = input(f"테스트할 종목 수 (기본 {sample_size}개, Enter=기본값): ").strip()
        if user_input:
            sample_size = min(int(user_input), 40)  # 최대 40개
    except:
        pass
    
    print(f"📊 {sample_size}개 종목으로 테스트 시작...")
    
    # 테스터 생성 및 실행
    tester = CompactSP500Tester(sample_size)
    results = tester.run_compact_backtest()
    
    # 결과 분석
    tester.analyze_results(results)
    
    # 간단한 CSV 저장 (선택사항)
    save_csv = input(f"\n결과를 CSV로 저장하시겠습니까? (y/N): ").lower().strip()
    if save_csv == 'y':
        filename = f"compact_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        results.to_csv(f"results/{filename}", index=False)
        print(f"📁 결과 저장: results/{filename}")
    
    print(f"\n🎉 모든 분석이 완료되었습니다!")

if __name__ == "__main__":
    main()
