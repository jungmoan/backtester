#!/usr/bin/env python3
"""
주식 백테스팅 시스템 메인 실행 파일

사용 예시:
    python main.py
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.moving_average import MovingAverageStrategy, MovingAverageTrendStrategy
from strategies.rsi_strategy import RSIStrategy, RSIMeanReversionStrategy
from backtester.engine import BacktestEngine
from config.config import Config

def main():
    """메인 실행 함수"""
    print("🚀 주식 백테스팅 시스템")
    print("=" * 50)
    
    # 테스트할 종목 (한국 주식)
    symbols = [
        '005930.KS',  # 삼성전자
        '000660.KS',  # SK하이닉스
    ]
    
    # 테스트할 전략들
    strategies = [
        MovingAverageStrategy(short_window=5, long_window=20),
        RSIStrategy(rsi_period=14, oversold=30, overbought=70),
        MovingAverageTrendStrategy(ma_window=20, trend_threshold=0.02),
    ]
    
    # 백테스트 기간
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    # 각 전략과 종목에 대해 백테스트 실행
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"종목: {symbol}")
        print(f"{'='*60}")
        
        for strategy in strategies:
            try:
                # 백테스트 엔진 생성
                engine = BacktestEngine(strategy, Config.INITIAL_CAPITAL)
                
                # 백테스트 실행
                results = engine.run_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    position_size=Config.POSITION_SIZE
                )
                
                if results:
                    # 결과 출력
                    engine.print_results()
                    
                    # CSV 파일로 저장
                    symbol_clean = symbol.replace('.KS', '')
                    engine.save_results_to_csv(symbol_clean, strategy.name)
                    
                    # 결과 저장
                    all_results.append(results)
                    
                    print(f"\n✅ {strategy.get_description()} 백테스트 완료")
                else:
                    print(f"\n❌ {strategy.get_description()} 백테스트 실패")
                    
            except Exception as e:
                import traceback
                print(f"\n❌ 오류 발생: {e}")
                print("상세 오류:")
                traceback.print_exc()
                continue
            
            print(f"\n{'-'*60}")
    
    # 전체 결과 요약
    print(f"\n{'='*60}")
    print("📊 전체 백테스트 결과 요약")
    print(f"{'='*60}")
    
    if all_results:
        print(f"총 {len(all_results)}개의 백테스트가 완료되었습니다.")
        print("\n주요 성과 지표 비교:")
        print("-" * 80)
        print(f"{'전략':<30} {'종목':<15} {'총수익률':<12} {'샤프비율':<10} {'최대낙폭':<10}")
        print("-" * 80)
        
        for result in all_results:
            strategy_name = result['strategy'][:28]
            symbol = result['symbol']
            report = result['performance_report']
            
            total_return = report.get('총수익률', 'N/A')
            sharpe_ratio = report.get('샤프비율', 'N/A')
            max_drawdown = report.get('최대낙폭', 'N/A')
            
            print(f"{strategy_name:<30} {symbol:<15} {total_return:<12} {sharpe_ratio:<10} {max_drawdown:<10}")
    else:
        print("완료된 백테스트가 없습니다.")
    
    print(f"\n{'='*60}")
    print("🎉 모든 백테스트가 완료되었습니다!")
    print(f"결과는 '{Config.RESULTS_DIR}' 폴더에서 확인할 수 있습니다.")

def run_single_backtest():
    """단일 백테스트 실행 (테스트용)"""
    print("🧪 단일 백테스트 테스트")
    
    # 전략 선택
    strategy = MovingAverageStrategy(short_window=5, long_window=20)
    
    # 백테스트 엔진 생성
    engine = BacktestEngine(strategy)
    
    # 백테스트 실행
    results = engine.run_backtest(
        symbol='005930.KS',  # 삼성전자
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    if results:
        # 결과 출력
        engine.print_results()
        
        # CSV 저장
        engine.save_results_to_csv("005930", "test_backtest")
        
        print("✅ 테스트 완료!")
    else:
        print("❌ 테스트 실패!")

if __name__ == "__main__":
    try:
        # 전체 백테스트 실행
        main()
        
        # 또는 단일 테스트 실행 (아래 주석 해제)
        # run_single_backtest()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
