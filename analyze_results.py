#!/usr/bin/env python3
"""
백테스트 결과 분석 및 시각화 스크립트
"""

import os
import sys
import glob

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from visualization.analyzer import ResultsAnalyzer

def main():
    """결과 분석 메인 함수"""
    print("📊 백테스트 결과 분석 및 시각화")
    print("=" * 50)
    
    # 결과 분석기 생성
    analyzer = ResultsAnalyzer("results")
    
    # results 폴더에서 파일들 찾기
    portfolio_files = glob.glob("results/*_portfolio.csv")
    report_files = glob.glob("results/*_report.csv")
    trade_files = glob.glob("results/*_trades.csv")
    
    if not portfolio_files:
        print("분석할 결과 파일이 없습니다.")
        print("먼저 main.py를 실행하여 백테스트를 수행하세요.")
        return
    
    print(f"발견된 파일들:")
    print(f"- 포트폴리오 파일: {len(portfolio_files)}개")
    print(f"- 보고서 파일: {len(report_files)}개")
    print(f"- 거래 파일: {len(trade_files)}개")
    print()
    
    # 1. 개별 포트폴리오 성과 차트
    print("1️⃣ 개별 포트폴리오 성과 차트 생성 중...")
    for portfolio_file in portfolio_files[:3]:  # 처음 3개만
        strategy_name = os.path.basename(portfolio_file).replace('_portfolio.csv', '')
        print(f"   📈 {strategy_name}")
        analyzer.plot_portfolio_performance(portfolio_file, f"Portfolio Performance - {strategy_name}")
    print()
    
    # 2. 전략 비교 차트
    if len(report_files) > 1:
        print("2️⃣ 전략 성과 비교 차트 생성 중...")
        comparison_df = analyzer.compare_strategies(report_files)
        if comparison_df is not None:
            print("전략 비교 완료!")
            print(comparison_df)
        print()
    
    # 3. 거래 분석
    print("3️⃣ 거래 분석 차트 생성 중...")
    for trade_file in trade_files[:3]:  # 처음 3개만
        strategy_name = os.path.basename(trade_file).replace('_trades.csv', '')
        print(f"   📊 {strategy_name}")
        analyzer.analyze_trades(trade_file, f"Trade Analysis - {strategy_name}")
    print()
    
    print("✅ 모든 분석이 완료되었습니다!")
    print("생성된 차트 파일들을 확인하세요.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
