#!/usr/bin/env python3
"""
S&P 500 백테스팅 결과 분석 및 시각화
SP500_Summary.csv 파일을 읽어서 각 전략의 평균 성능을 분석합니다.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

def load_and_analyze_data():
    """CSV 데이터 로드 및 전처리"""
    # CSV 파일 로드
    csv_path = Path("results/SP500_Summary.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} 파일을 찾을 수 없습니다.")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"총 {len(df)} 개의 백테스트 결과를 로드했습니다.")
    print(f"테스트된 종목 수: {df['Symbol'].nunique()}개")
    print(f"테스트된 전략 수: {df['Strategy'].nunique()}개")
    print(f"전략 목록: {df['Strategy'].unique().tolist()}")
    
    return df

def calculate_strategy_statistics(df):
    """각 전략별 통계 계산"""
    stats = df.groupby('Strategy').agg({
        'Total_Return': ['mean', 'std', 'count'],
        'Sharpe_Ratio': ['mean', 'std'],
        'Max_Drawdown': ['mean', 'std'],
        'Win_Rate': ['mean', 'std'],
        'Total_Trades': ['mean', 'std']
    }).round(4)
    
    # 컬럼명 정리
    stats.columns = ['_'.join(col).strip() for col in stats.columns]
    stats = stats.reset_index()
    
    print("\n=== 전략별 통계 요약 ===")
    print(stats)
    
    return stats

def create_performance_charts(df, stats):
    """성능 분석 차트 생성"""
    # 한글 폰트 설정
    plt.rcParams['font.family'] = ['Arial Unicode MS', 'AppleGothic', 'Malgun Gothic']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 전략명 간소화
    strategy_names = {
        'Moving_Average_Strategy': 'MA Strategy',
        'Moving_Average_Trend_Strategy': 'MA Trend',
        'RSI_Strategy': 'RSI Strategy', 
        'RSI_Mean_Reversion_Strategy': 'RSI Mean Rev'
    }
    
    df['Strategy_Short'] = df['Strategy'].map(strategy_names)
    
    # 2x2 서브플롯 생성
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('S&P 500 백테스팅 전략별 성능 비교', fontsize=16, fontweight='bold')
    
    # 1. 총 수익률 (평균 + 에러바)
    ax1 = axes[0, 0]
    strategy_groups = df.groupby('Strategy_Short')
    means = strategy_groups['Total_Return'].mean()
    stds = strategy_groups['Total_Return'].std()
    
    bars1 = ax1.bar(means.index, means.values, yerr=stds.values, 
                    capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax1.set_title('총 수익률 (%)', fontweight='bold')
    ax1.set_ylabel('수익률 (%)')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # 수치 표시
    for bar, mean, std in zip(bars1, means.values, stds.values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std + 0.1,
                f'{mean:.2f}%\n±{std:.2f}', ha='center', va='bottom', fontsize=9)
    
    # 2. 샤프 비율 (평균 + 에러바)  
    ax2 = axes[0, 1]
    means_sharpe = strategy_groups['Sharpe_Ratio'].mean()
    stds_sharpe = strategy_groups['Sharpe_Ratio'].std()
    
    bars2 = ax2.bar(means_sharpe.index, means_sharpe.values, yerr=stds_sharpe.values,
                    capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax2.set_title('샤프 비율', fontweight='bold')
    ax2.set_ylabel('샤프 비율')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # 수치 표시
    for bar, mean, std in zip(bars2, means_sharpe.values, stds_sharpe.values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + std + 0.02,
                f'{mean:.3f}\n±{std:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 3. 최대 낙폭 (평균 + 에러바)
    ax3 = axes[1, 0]
    means_dd = strategy_groups['Max_Drawdown'].mean()
    stds_dd = strategy_groups['Max_Drawdown'].std()
    
    bars3 = ax3.bar(means_dd.index, means_dd.values, yerr=stds_dd.values,
                    capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax3.set_title('최대 낙폭 (%)', fontweight='bold')
    ax3.set_ylabel('낙폭 (%)')
    ax3.grid(True, alpha=0.3)
    
    # 수치 표시
    for bar, mean, std in zip(bars3, means_dd.values, stds_dd.values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height - std - 0.1,
                f'{mean:.2f}%\n±{std:.2f}', ha='center', va='top', fontsize=9)
    
    # 4. 승률 (평균 + 에러바)
    ax4 = axes[1, 1]
    means_wr = strategy_groups['Win_Rate'].mean()
    stds_wr = strategy_groups['Win_Rate'].std()
    
    bars4 = ax4.bar(means_wr.index, means_wr.values, yerr=stds_wr.values,
                    capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax4.set_title('승률 (%)', fontweight='bold')
    ax4.set_ylabel('승률 (%)')
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 100)
    
    # 수치 표시
    for bar, mean, std in zip(bars4, means_wr.values, stds_wr.values):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + std + 1,
                f'{mean:.1f}%\n±{std:.1f}', ha='center', va='bottom', fontsize=9)
    
    # x축 레이블 회전
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # 이미지 저장
    output_path = Path("results/strategy_performance_analysis.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n차트가 저장되었습니다: {output_path}")
    
    return fig

def create_detailed_box_plots(df):
    """상세한 박스플롯 생성"""
    # 전략명 간소화
    strategy_names = {
        'Moving_Average_Strategy': 'MA Strategy',
        'Moving_Average_Trend_Strategy': 'MA Trend',
        'RSI_Strategy': 'RSI Strategy', 
        'RSI_Mean_Reversion_Strategy': 'RSI Mean Rev'
    }
    
    df['Strategy_Short'] = df['Strategy'].map(strategy_names)
    
    # 2x2 박스플롯
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('S&P 500 백테스팅 전략별 성능 분포', fontsize=16, fontweight='bold')
    
    # 1. 총 수익률 박스플롯
    ax1 = axes[0, 0]
    df.boxplot(column='Total_Return', by='Strategy_Short', ax=ax1)
    ax1.set_title('총 수익률 분포 (%)')
    ax1.set_xlabel('전략')
    ax1.set_ylabel('수익률 (%)')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    
    # 2. 샤프 비율 박스플롯
    ax2 = axes[0, 1]
    df.boxplot(column='Sharpe_Ratio', by='Strategy_Short', ax=ax2)
    ax2.set_title('샤프 비율 분포')
    ax2.set_xlabel('전략')
    ax2.set_ylabel('샤프 비율')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    
    # 3. 최대 낙폭 박스플롯
    ax3 = axes[1, 0]
    df.boxplot(column='Max_Drawdown', by='Strategy_Short', ax=ax3)
    ax3.set_title('최대 낙폭 분포 (%)')
    ax3.set_xlabel('전략')
    ax3.set_ylabel('낙폭 (%)')
    ax3.grid(True, alpha=0.3)
    
    # 4. 승률 박스플롯
    ax4 = axes[1, 1]
    df.boxplot(column='Win_Rate', by='Strategy_Short', ax=ax4)
    ax4.set_title('승률 분포 (%)')
    ax4.set_xlabel('전략')
    ax4.set_ylabel('승률 (%)')
    ax4.grid(True, alpha=0.3)
    
    # x축 레이블 회전
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlabel('')  # 개별 subplot 제목 제거
    
    plt.tight_layout()
    
    # 이미지 저장
    output_path = Path("results/strategy_performance_boxplots.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"박스플롯이 저장되었습니다: {output_path}")
    
    return fig

def create_correlation_heatmap(df):
    """성능 지표 간 상관관계 히트맵"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 수치형 컬럼만 선택
    numeric_cols = ['Total_Return', 'Sharpe_Ratio', 'Max_Drawdown', 'Win_Rate', 'Total_Trades']
    corr_matrix = df[numeric_cols].corr()
    
    # 히트맵 생성
    sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
                square=True, linewidths=0.5, ax=ax, fmt='.3f')
    
    ax.set_title('성능 지표 간 상관관계', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # 이미지 저장
    output_path = Path("results/performance_correlation_heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"상관관계 히트맵이 저장되었습니다: {output_path}")
    
    return fig

def print_summary_statistics(df):
    """요약 통계 출력"""
    print("\n" + "="*80)
    print("📊 S&P 500 백테스팅 전략별 성능 요약")
    print("="*80)
    
    strategy_stats = df.groupby('Strategy').agg({
        'Total_Return': ['count', 'mean', 'std', 'min', 'max'],
        'Sharpe_Ratio': ['mean', 'std'],
        'Win_Rate': ['mean', 'std'],
        'Max_Drawdown': ['mean', 'std']
    }).round(4)
    
    strategies = df['Strategy'].unique()
    
    for strategy in strategies:
        strategy_data = df[df['Strategy'] == strategy]
        print(f"\n🔹 {strategy}:")
        print(f"   테스트 종목 수: {len(strategy_data)}개")
        print(f"   평균 수익률: {strategy_data['Total_Return'].mean():.2f}% (±{strategy_data['Total_Return'].std():.2f}%)")
        print(f"   평균 샤프비율: {strategy_data['Sharpe_Ratio'].mean():.3f} (±{strategy_data['Sharpe_Ratio'].std():.3f})")
        print(f"   평균 승률: {strategy_data['Win_Rate'].mean():.1f}% (±{strategy_data['Win_Rate'].std():.1f}%)")
        print(f"   평균 최대낙폭: {strategy_data['Max_Drawdown'].mean():.2f}% (±{strategy_data['Max_Drawdown'].std():.2f}%)")
        
        # 상위 3개 종목
        top_performers = strategy_data.nlargest(3, 'Total_Return')
        print(f"   📈 상위 3개 종목:")
        for _, row in top_performers.iterrows():
            print(f"      {row['Symbol']}: {row['Total_Return']:.2f}% (샤프: {row['Sharpe_Ratio']:.3f})")

def main():
    """메인 실행 함수"""
    print("🚀 S&P 500 백테스팅 결과 분석 시작")
    print("="*60)
    
    # 데이터 로드
    df = load_and_analyze_data()
    if df is None:
        return
    
    # 통계 계산
    stats = calculate_strategy_statistics(df)
    
    # 요약 통계 출력
    print_summary_statistics(df)
    
    # 차트 생성
    print(f"\n📊 성능 분석 차트 생성 중...")
    fig1 = create_performance_charts(df, stats)
    
    print(f"📊 상세 분포 박스플롯 생성 중...")
    fig2 = create_detailed_box_plots(df)
    
    print(f"📊 상관관계 히트맵 생성 중...")
    fig3 = create_correlation_heatmap(df)
    
    print(f"\n🎉 모든 분석이 완료되었습니다!")
    print(f"📁 결과는 'results' 폴더에서 확인할 수 있습니다.")

if __name__ == "__main__":
    main()
