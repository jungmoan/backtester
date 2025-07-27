#!/usr/bin/env python3
"""
S&P 500 전체 백테스팅 실행 스크립트
"""

import os
import sys
import pandas as pd
from datetime import datetime
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 모듈 임포트 시도
try:
    from config.config import Config as BacktestConfig
    from data.sp500_manager import SP500DataManager
    from backtester.engine import BacktestEngine
    from strategies.moving_average import MovingAverageStrategy, MovingAverageTrendStrategy
    from strategies.rsi_strategy import RSIStrategy, RSIMeanReversionStrategy
except ImportError as e:
    import traceback
    print(f"모듈 임포트 오류: {e}")
    print("상세 오류:")
    traceback.print_exc()
    print("현재 디렉토리:", os.getcwd())
    print("프로젝트 루트:", project_root)
    print("Python 경로:", sys.path[:3])
    sys.exit(1)

def create_summary_report(results_dir: str):
    """전체 결과 요약 리포트 생성"""
    csv_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("생성된 결과 파일이 없습니다.")
        return
    
    summary_data = []
    
    for csv_file in csv_files:
        try:
            # trades 파일과 summary 파일 제외
            if '_trades.csv' in csv_file or 'Summary.csv' in csv_file:
                continue
                
            # 파일명에서 심볼과 전략 추출
            parts = csv_file.replace('.csv', '').split('_')
            if len(parts) >= 2:
                symbol = parts[0]
                strategy = '_'.join(parts[1:])
            else:
                continue
            
            # CSV 파일 읽기
            df = pd.read_csv(os.path.join(results_dir, csv_file))
            
            # CSV 파일 구조 확인
            if 'Metric' not in df.columns:
                print(f"Warning: {csv_file}에 'Metric' 컬럼이 없습니다. 건너뜁니다.")
                continue
            
            # 주요 메트릭 추출
            metrics = {}
            for _, row in df.iterrows():
                try:
                    metric_name = row['Metric']
                    value = row['Value']
                    
                    if metric_name == 'Total Return (%)':
                        metrics['Total_Return'] = float(value)
                    elif metric_name == 'Sharpe Ratio':
                        metrics['Sharpe_Ratio'] = float(value)
                    elif metric_name == 'Maximum Drawdown (%)':
                        metrics['Max_Drawdown'] = float(value)
                    elif metric_name == 'Win Rate (%)':
                        metrics['Win_Rate'] = float(value)
                    elif metric_name == 'Total Trades':
                        metrics['Total_Trades'] = int(value)
                except (ValueError, KeyError) as e:
                    print(f"Warning: {csv_file}의 메트릭 파싱 중 오류: {e}")
                    continue
                    metrics['Total_Trades'] = int(value)
            
            summary_data.append({
                'Symbol': symbol,
                'Strategy': strategy,
                **metrics
            })
            
        except Exception as e:
            import traceback
            print(f"파일 {csv_file} 처리 중 오류: {e}")
            print("상세 오류:")
            traceback.print_exc()
            continue
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # 전략별 요약
        print("\n" + "="*80)
        print("📊 S&P 500 백테스팅 종합 결과")
        print("="*80)
        
        strategies = summary_df['Strategy'].unique()
        
        for strategy in strategies:
            strategy_data = summary_df[summary_df['Strategy'] == strategy]
            
            print(f"\n🔹 {strategy} 전략 결과:")
            print(f"   테스트된 종목 수: {len(strategy_data)}")
            print(f"   평균 수익률: {strategy_data['Total_Return'].mean():.2f}%")
            print(f"   평균 샤프 비율: {strategy_data['Sharpe_Ratio'].mean():.4f}")
            print(f"   평균 최대낙폭: {strategy_data['Max_Drawdown'].mean():.2f}%")
            print(f"   평균 승률: {strategy_data['Win_Rate'].mean():.2f}%")
            
            # 상위 5개 종목
            top_performers = strategy_data.nlargest(5, 'Total_Return')
            print(f"   📈 상위 5개 종목:")
            for _, row in top_performers.iterrows():
                print(f"      {row['Symbol']}: {row['Total_Return']:.2f}% (샤프: {row['Sharpe_Ratio']:.3f})")
        
        # 전체 요약 저장
        summary_file = os.path.join(results_dir, 'SP500_Summary.csv')
        summary_df.to_csv(summary_file, index=False)
        print(f"\n📋 전체 요약이 저장되었습니다: {summary_file}")
        
        # 최고 성과 종목들
        print(f"\n🏆 전체 최고 성과 종목 TOP 10:")
        top_overall = summary_df.nlargest(10, 'Total_Return')
        for i, (_, row) in enumerate(top_overall.iterrows(), 1):
            print(f"   {i:2d}. {row['Symbol']} ({row['Strategy']}): {row['Total_Return']:.2f}%")

def main():
    print("🚀 S&P 500 백테스팅 시스템 시작")
    print("="*60)
    
    # 설정 및 데이터 관리자 초기화
    config = BacktestConfig()
    sp500_manager = SP500DataManager()
    
    # S&P 500 데이터 다운로드 (5년간)
    print("\n📊 S&P 500 데이터 준비 중...")
    all_data = sp500_manager.download_sp500_data(years=5)
    
    if not all_data:
        print("❌ 데이터를 불러올 수 없습니다.")
        return
    
    print(f"✅ {len(all_data)}개 종목 데이터 준비 완료")
    
    # 전략 설정
    strategies = [
        MovingAverageStrategy(short_window=20, long_window=50),
        MovingAverageTrendStrategy(ma_window=20, trend_threshold=0.02),
        RSIStrategy(rsi_period=14, oversold=30, overbought=70),
        RSIMeanReversionStrategy(rsi_period=14, extreme_oversold=20, extreme_overbought=80)
    ]
    
    print(f"\n📈 테스트할 전략 수: {len(strategies)}")
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy.name}")
    
    # 백테스팅 실행
    total_tests = len(all_data) * len(strategies)
    current_test = 0
    start_time = time.time()
    
    print(f"\n🔄 백테스팅 시작 (총 {total_tests}개 테스트)")
    print("-" * 60)
    
    successful_tests = 0
    failed_tests = 0
    
    test_symbols = list(all_data.keys())[:10]  # 상위 10개 종목만 테스트 (예시)
    for symbol in test_symbols:
        print(f"\n📊 {symbol} 테스트 중...")
        
        # 심볼 데이터 가져오기
        data = sp500_manager.get_symbol_data(symbol, all_data)
        
        if data.empty:
            print(f"   ⚠️ {symbol}: 데이터가 없습니다.")
            failed_tests += len(strategies)
            current_test += len(strategies)
            continue
        
        # 각 전략에 대해 백테스팅 실행
        for strategy in strategies:
            current_test += 1
            
            try:
                print(f"   [{current_test}/{total_tests}] {strategy.name} 실행 중...")
                # 백테스터 생성 및 실행
                engine = BacktestEngine(strategy)
                engine.run_backtest_with_data(symbol, data)
                # 결과 저장
                if hasattr(engine, 'results') and engine.results:
                    engine.save_results_to_csv(symbol, strategy.name)
                    successful_tests += 1
                    # 간단한 결과 출력
                    total_return = engine.results['performance_report'].get('Total Return (%)', 0)
                    sharpe = engine.results['performance_report'].get('Sharpe Ratio', 0)
                    print(f"      ✅ 수익률: {total_return:.2f}%, 샤프: {sharpe:.3f}")
                else:
                    print(f"      ❌ 결과 생성 실패")
                    failed_tests += 1
            except Exception as e:
                import traceback
                print(f"      ❌ 오류: {str(e)}")
                print(f"      📋 상세 오류:")
                traceback.print_exc()
                failed_tests += 1
                continue
        
        # 진행률 표시
        elapsed_time = time.time() - start_time
        if current_test > 0:
            avg_time_per_test = elapsed_time / current_test
            remaining_tests = total_tests - current_test
            estimated_time = remaining_tests * avg_time_per_test
            
            print(f"   진행률: {current_test}/{total_tests} ({current_test/total_tests*100:.1f}%)")
            print(f"   예상 남은 시간: {estimated_time/60:.1f}분")
    
    # 최종 결과
    total_time = time.time() - start_time
    print("\n" + "="*60)
    print("🎯 백테스팅 완료!")
    print(f"   총 소요 시간: {total_time/60:.1f}분")
    print(f"   성공한 테스트: {successful_tests}")
    print(f"   실패한 테스트: {failed_tests}")
    print(f"   성공률: {successful_tests/(successful_tests+failed_tests)*100:.1f}%")
    
    # 요약 리포트 생성
    create_summary_report(config.RESULTS_DIR)
    
    print(f"\n📁 모든 결과는 '{config.RESULTS_DIR}' 폴더에 저장되었습니다.")
    print("🎉 S&P 500 백테스팅이 완료되었습니다!")

if __name__ == "__main__":
    main()
