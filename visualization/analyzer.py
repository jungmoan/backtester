import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List
import os

class ResultsAnalyzer:
    """백테스트 결과 분석 및 시각화 클래스"""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = results_dir
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
    def plot_portfolio_performance(self, portfolio_file: str, title: str = "Portfolio Performance"):
        """포트폴리오 성과 차트 그리기"""
        try:
            df = pd.read_csv(portfolio_file)
            df['date'] = pd.to_datetime(df['date'])
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(title, fontsize=16)
            
            # 1. 포트폴리오 가치 변화
            axes[0, 0].plot(df['date'], df['total_value'], linewidth=2, color='blue')
            axes[0, 0].set_title('Portfolio Value Over Time')
            axes[0, 0].set_ylabel('Portfolio Value (KRW)')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 2. 누적 수익률
            axes[0, 1].plot(df['date'], df['return'], linewidth=2, color='green')
            axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
            axes[0, 1].set_title('Cumulative Return (%)')
            axes[0, 1].set_ylabel('Return (%)')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # 3. 현금 vs 포지션 가치
            axes[1, 0].plot(df['date'], df['cash'], label='Cash', linewidth=2)
            axes[1, 0].plot(df['date'], df['positions_value'], label='Positions', linewidth=2)
            axes[1, 0].set_title('Cash vs Positions Value')
            axes[1, 0].set_ylabel('Value (KRW)')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # 4. 드로우다운
            portfolio_values = df['total_value']
            rolling_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - rolling_max) / rolling_max * 100
            
            axes[1, 1].fill_between(df['date'], drawdown, 0, alpha=0.7, color='red')
            axes[1, 1].set_title('Drawdown (%)')
            axes[1, 1].set_ylabel('Drawdown (%)')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 파일 저장
            chart_file = portfolio_file.replace('.csv', '_chart.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            print(f"차트가 저장되었습니다: {chart_file}")
            
            plt.show()
            
        except Exception as e:
            import traceback
            print(f"차트 생성 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
    
    def compare_strategies(self, report_files: List[str]):
        """여러 전략 성과 비교"""
        try:
            data = []
            
            for file in report_files:
                if os.path.exists(file):
                    df = pd.read_csv(file)
                    strategy_name = os.path.basename(file).split('_')[1:-1]
                    strategy_name = '_'.join(strategy_name)
                    
                    metrics = {}
                    for _, row in df.iterrows():
                        metric = row['지표']
                        value = row['값']
                        
                        # 수치 값 추출
                        if '수익률' in metric and '%' in str(value):
                            metrics[metric] = float(str(value).replace('%', ''))
                        elif '비율' in metric:
                            try:
                                metrics[metric] = float(value)
                            except:
                                metrics[metric] = 0
                        elif '거래횟수' in metric:
                            metrics[metric] = int(value)
                    
                    metrics['전략'] = strategy_name
                    data.append(metrics)
            
            if not data:
                print("비교할 데이터가 없습니다.")
                return
            
            comparison_df = pd.DataFrame(data)
            
            # 비교 차트 생성
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Strategy Comparison', fontsize=16)
            
            # 1. 총수익률 비교
            if '총수익률' in comparison_df.columns:
                bars = axes[0, 0].bar(comparison_df['전략'], comparison_df['총수익률'])
                axes[0, 0].set_title('Total Return Comparison')
                axes[0, 0].set_ylabel('Return (%)')
                axes[0, 0].tick_params(axis='x', rotation=45)
                
                # 막대 색상 설정 (양수: 녹색, 음수: 빨간색)
                for bar, value in zip(bars, comparison_df['총수익률']):
                    bar.set_color('green' if value >= 0 else 'red')
            
            # 2. 샤프비율 비교
            if '샤프비율' in comparison_df.columns:
                bars = axes[0, 1].bar(comparison_df['전략'], comparison_df['샤프비율'])
                axes[0, 1].set_title('Sharpe Ratio Comparison')
                axes[0, 1].set_ylabel('Sharpe Ratio')
                axes[0, 1].tick_params(axis='x', rotation=45)
                axes[0, 1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # 3. 승률 비교
            if '승률' in comparison_df.columns:
                axes[1, 0].bar(comparison_df['전략'], comparison_df['승률'])
                axes[1, 0].set_title('Win Rate Comparison')
                axes[1, 0].set_ylabel('Win Rate (%)')
                axes[1, 0].tick_params(axis='x', rotation=45)
                axes[1, 0].set_ylim(0, 100)
            
            # 4. 총거래횟수 비교
            if '총거래횟수' in comparison_df.columns:
                axes[1, 1].bar(comparison_df['전략'], comparison_df['총거래횟수'])
                axes[1, 1].set_title('Total Trades Comparison')
                axes[1, 1].set_ylabel('Number of Trades')
                axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 파일 저장
            chart_file = os.path.join(self.results_dir, 'strategy_comparison.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            print(f"비교 차트가 저장되었습니다: {chart_file}")
            
            plt.show()
            
            return comparison_df
            
        except Exception as e:
            import traceback
            print(f"전략 비교 차트 생성 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
    
    def analyze_trades(self, trades_file: str, title: str = "Trade Analysis"):
        """거래 분석"""
        try:
            if not os.path.exists(trades_file):
                print(f"거래 파일이 존재하지 않습니다: {trades_file}")
                return
            
            df = pd.read_csv(trades_file)
            
            if df.empty:
                print("거래 데이터가 없습니다.")
                return
            
            # 매수-매도 쌍 매칭
            buy_orders = df[df['action'] == 'BUY'].copy()
            sell_orders = df[df['action'] == 'SELL'].copy()
            
            trades = []
            for _, sell in sell_orders.iterrows():
                # 해당 매도보다 이전의 매수 찾기
                matching_buys = buy_orders[
                    (buy_orders['symbol'] == sell['symbol']) & 
                    (pd.to_datetime(buy_orders['date']) < pd.to_datetime(sell['date']))
                ]
                
                if not matching_buys.empty:
                    buy = matching_buys.iloc[-1]  # 가장 최근 매수
                    
                    profit = (sell['price'] - buy['price']) * sell['quantity']
                    return_pct = (sell['price'] / buy['price'] - 1) * 100
                    
                    trades.append({
                        'buy_date': buy['date'],
                        'sell_date': sell['date'],
                        'buy_price': buy['price'],
                        'sell_price': sell['price'],
                        'quantity': sell['quantity'],
                        'profit': profit,
                        'return_pct': return_pct,
                        'holding_days': (pd.to_datetime(sell['date']) - pd.to_datetime(buy['date'])).days
                    })
            
            if not trades:
                print("완료된 거래가 없습니다.")
                return
            
            trades_df = pd.DataFrame(trades)
            
            # 차트 생성
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(title, fontsize=16)
            
            # 1. 거래별 수익률
            colors = ['green' if x >= 0 else 'red' for x in trades_df['return_pct']]
            axes[0, 0].bar(range(len(trades_df)), trades_df['return_pct'], color=colors)
            axes[0, 0].set_title('Return per Trade')
            axes[0, 0].set_ylabel('Return (%)')
            axes[0, 0].set_xlabel('Trade Number')
            axes[0, 0].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # 2. 수익률 분포
            axes[0, 1].hist(trades_df['return_pct'], bins=10, alpha=0.7, edgecolor='black')
            axes[0, 1].set_title('Return Distribution')
            axes[0, 1].set_xlabel('Return (%)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].axvline(x=0, color='red', linestyle='--', alpha=0.7)
            
            # 3. 보유기간 분포
            axes[1, 0].hist(trades_df['holding_days'], bins=10, alpha=0.7, edgecolor='black')
            axes[1, 0].set_title('Holding Period Distribution')
            axes[1, 0].set_xlabel('Days')
            axes[1, 0].set_ylabel('Frequency')
            
            # 4. 수익 vs 보유기간
            colors = ['green' if x >= 0 else 'red' for x in trades_df['return_pct']]
            axes[1, 1].scatter(trades_df['holding_days'], trades_df['return_pct'], c=colors, alpha=0.7)
            axes[1, 1].set_title('Return vs Holding Period')
            axes[1, 1].set_xlabel('Holding Days')
            axes[1, 1].set_ylabel('Return (%)')
            axes[1, 1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.tight_layout()
            
            # 파일 저장
            chart_file = trades_file.replace('.csv', '_analysis.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            print(f"거래 분석 차트가 저장되었습니다: {chart_file}")
            
            plt.show()
            
            # 거래 통계 출력
            print(f"\n📊 거래 분석 결과")
            print(f"총 거래 수: {len(trades_df)}")
            print(f"승리 거래: {len(trades_df[trades_df['return_pct'] > 0])}")
            print(f"패배 거래: {len(trades_df[trades_df['return_pct'] < 0])}")
            print(f"승률: {len(trades_df[trades_df['return_pct'] > 0]) / len(trades_df) * 100:.1f}%")
            print(f"평균 수익률: {trades_df['return_pct'].mean():.2f}%")
            print(f"최대 수익률: {trades_df['return_pct'].max():.2f}%")
            print(f"최대 손실률: {trades_df['return_pct'].min():.2f}%")
            print(f"평균 보유기간: {trades_df['holding_days'].mean():.1f}일")
            
        except Exception as e:
            import traceback
            print(f"거래 분석 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
