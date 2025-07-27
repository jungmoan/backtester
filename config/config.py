# 백테스팅 설정 파일

class Config:
    # 기본 설정
    INITIAL_CAPITAL = 10_000_000  # 초기 자본 (1천만원)
    COMMISSION_RATE = 0.003      # 수수료율 (0.3%)
    SLIPPAGE_RATE = 0.001        # 슬리피지 (0.1%)
    
    # 데이터 설정
    START_DATE = "2020-01-01"
    END_DATE = "2024-12-31"
    
    # 결과 저장 설정
    RESULTS_DIR = "results"
    
    # 백테스트 설정
    POSITION_SIZE = 0.1  # 포지션 크기 (총 자본의 10%)
    MAX_POSITIONS = 5    # 최대 보유 종목 수
