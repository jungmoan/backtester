#!/usr/bin/env python3
"""
간단한 백테스팅 예제 - 삼성전자 이동평균 전략
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.moving_average import MovingAverageStrategy
from backtester.engine import BacktestEngine

def simple_backtest_example():
    """간단한 백테스트 예제"""
    print("🎯 간단한 백테스트 예제")
    print("=" * 40)
    
    # 1. 전략 생성 (5일 단기, 20일 장기 이동평균)
    strategy = MovingAverageStrategy(short_window=5, long_window=20)
    
    # 2. 백테스트 엔진 생성
    engine = BacktestEngine(strategy, initial_capital=5_000_000)  # 500만원
    
    # 3. 백테스트 실행
    print("삼성전자(005930.KS)에 대한 이동평균 전략 백테스트를 실행합니다...")
    results = engine.run_backtest(
        symbol='005930.KS',
        start_date='2024-01-01',
        end_date='2024-12-31',
        position_size=0.2  # 자본의 20%씩 투자
    )
    
    if results:
        # 4. 결과 출력
        engine.print_results()
        
        # 5. CSV 파일로 저장
        engine.save_results_to_csv("simple_example")
        
        print("\n✅ 백테스트 완료!")
        print("results 폴더에서 결과를 확인하세요.")
    else:
        print("❌ 백테스트 실패!")

if __name__ == "__main__":
    try:
        simple_backtest_example()
    except Exception as e:
        import traceback
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("상세 오류:")
        traceback.print_exc()
