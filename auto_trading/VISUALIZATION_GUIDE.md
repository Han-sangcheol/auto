# 데이터 시각화 가이드

CleonAI 자동매매 프로그램에서 수집한 데이터를 다양한 도구로 시각화하는 방법을 안내합니다.

## 목차

1. [개요](#개요)
2. [데이터 내보내기](#데이터-내보내기)
3. [Excel/Power BI 연동](#excelpower-bi-연동)
4. [Python 분석](#python-분석)
5. [Grafana 연동](#grafana-연동)
6. [자동 리포트](#자동-리포트)

---

## 개요

### 저장된 데이터 형식

- **데이터베이스**: DuckDB (`.duckdb` 파일)
- **Parquet 파일**: 일별 파티션 (`.parquet` 파일)
- **저장 위치**: `data/` 폴더
- **데이터 구조**: 1분봉 OHLCV (시가, 고가, 저가, 종가, 거래량)

### 데이터 스키마

```sql
CREATE TABLE candles (
    stock_code VARCHAR,      -- 종목 코드
    timestamp TIMESTAMP,     -- 날짜/시간 (1분 단위)
    open DOUBLE,            -- 시가
    high DOUBLE,            -- 고가
    low DOUBLE,             -- 저가
    close DOUBLE,           -- 종가
    volume BIGINT,          -- 거래량
    date DATE               -- 날짜 (파티션 키)
)
```

---

## 데이터 내보내기

### 1. CSV 내보내기

```python
from data_analyzer import DataAnalyzer
from database import StockDatabase
from datetime import datetime, timedelta

# 데이터베이스 연결
db = StockDatabase()
analyzer = DataAnalyzer(db)

# CSV 내보내기
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

analyzer.export_to_csv(
    stock_code='005930',
    start_date=start_date,
    end_date=end_date,
    output_path='output/samsung_week.csv'
)
```

**CSV 형식:**
```csv
timestamp,stock_code,open,high,low,close,volume
2025-10-28 09:00:00,005930,75000,75500,74800,75300,1000000
2025-10-28 09:01:00,005930,75300,75600,75200,75400,1050000
...
```

### 2. Excel 내보내기

```python
# Excel 내보내기 (통계 포함)
analyzer.export_to_excel(
    stock_code='005930',
    start_date=start_date,
    end_date=end_date,
    output_path='output/samsung_analysis.xlsx'
)
```

**생성되는 시트:**
- **1분봉 데이터**: 전체 OHLCV 데이터
- **통계**: 수익률, 변동성, 샤프 비율 등

### 3. HTML 리포트

```python
# 자동 리포트 생성
analyzer.generate_report(
    stock_code='005930',
    start_date=start_date,
    end_date=end_date,
    output_path='output/samsung_report.html'
)
```

브라우저에서 `samsung_report.html`을 열어 시각적인 리포트를 확인할 수 있습니다.

---

## Excel/Power BI 연동

### Excel에서 직접 읽기

#### 방법 1: CSV 가져오기

1. Excel 실행
2. **데이터** → **텍스트/CSV에서**
3. 내보낸 CSV 파일 선택
4. **로드** 클릭

#### 방법 2: Parquet 파일 읽기 (Power Query)

```powerquery
let
    Source = Parquet.Document(File.Contents("data/parquet/2025-10/005930_2025-10-28.parquet")),
    #"Changed Type" = Table.TransformColumnTypes(Source,{
        {"timestamp", type datetime}, 
        {"open", type number}, 
        {"close", type number}
    })
in
    #"Changed Type"
```

### Power BI 연동

1. **데이터 가져오기** → **Parquet**
2. `data/parquet/` 폴더 선택
3. 필요한 파일 선택 후 **로드**

**대시보드 예시:**

- 라인 차트: 시간별 종가 추이
- 캔들스틱 차트: OHLC
- KPI 카드: 최고가, 최저가, 수익률
- 슬라이서: 날짜 범위, 종목 선택

---

## Python 분석

### Pandas로 분석

```python
import pandas as pd
from database import StockDatabase
from datetime import datetime, timedelta

# DuckDB에서 직접 Pandas로 로드
db = StockDatabase()
conn = db._get_connection()

query = """
SELECT * 
FROM candles 
WHERE stock_code = '005930' 
  AND timestamp >= '2025-10-21'
ORDER BY timestamp
"""

df = conn.execute(query).df()

print(df.head())
print(f"\n총 {len(df)}개 레코드")
```

### 통계 분석

```python
# 기본 통계
print(df.describe())

# 일별 집계
daily = df.groupby(df['timestamp'].dt.date).agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})

print(daily)

# 수익률 계산
df['return'] = df['close'].pct_change() * 100
print(f"평균 수익률: {df['return'].mean():.2f}%")
print(f"변동성: {df['return'].std():.2f}%")
```

### 시각화

```python
import matplotlib.pyplot as plt

# 종가 차트
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['close'])
plt.title('삼성전자 주가 추이')
plt.xlabel('시간')
plt.ylabel('가격 (원)')
plt.grid(True)
plt.show()

# 거래량 차트
plt.figure(figsize=(12, 4))
plt.bar(df['timestamp'], df['volume'], width=0.0003)
plt.title('거래량')
plt.xlabel('시간')
plt.ylabel('거래량')
plt.show()
```

---

## Grafana 연동

### 설정 방법

#### 1. DuckDB를 PostgreSQL로 변환

DuckDB는 PostgreSQL wire protocol을 지원하지 않으므로, 데이터를 CSV로 내보내고 PostgreSQL/TimescaleDB로 임포트합니다.

```python
# 전체 데이터 CSV 내보내기
from database import StockDatabase

db = StockDatabase()
stocks = db.get_stock_list()

for stock in stocks:
    candles = db.get_candles(
        stock, 
        start_date=datetime(2025, 1, 1),
        end_date=datetime.now()
    )
    # CSV 저장
    ...
```

#### 2. Grafana 데이터 소스 추가

1. Grafana 웹 UI 접속
2. **Configuration** → **Data Sources** → **Add data source**
3. **PostgreSQL** 선택
4. 연결 정보 입력

#### 3. 대시보드 생성

**패널 1: 시계열 차트**

```sql
SELECT 
  timestamp as time,
  close as value,
  stock_code as metric
FROM candles
WHERE 
  stock_code = '005930'
  AND timestamp >= $__timeFrom()
  AND timestamp <= $__timeTo()
ORDER BY timestamp
```

**패널 2: 통계 테이블**

```sql
SELECT 
  stock_code,
  MIN(low) as 최저가,
  MAX(high) as 최고가,
  AVG(close) as 평균가,
  SUM(volume) as 총거래량
FROM candles
WHERE timestamp >= $__timeFrom()
GROUP BY stock_code
```

### 대체 방법: CSV + SimpleJSON

1. 데이터를 CSV로 주기적으로 내보내기
2. SimpleJSON 플러그인으로 CSV 읽기
3. Grafana에서 시각화

---

## 자동 리포트

### 일일 리포트 생성 스크립트

`generate_daily_report.py`:

```python
"""
일일 자동 리포트 생성 스크립트

사용법:
    python generate_daily_report.py

Windows 작업 스케줄러에 등록하여 매일 16:30에 자동 실행
"""

from data_analyzer import DataAnalyzer
from database import StockDatabase
from datetime import datetime, timedelta
from pathlib import Path

# 설정
OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)

# 데이터베이스 연결
db = StockDatabase()
analyzer = DataAnalyzer(db)

# 오늘 날짜
today = datetime.now().date()
start_date = datetime.combine(today, datetime.min.time())
end_date = datetime.now()

# 저장된 종목 목록
stocks = db.get_stock_list()

print(f"일일 리포트 생성 중... ({today})")

for stock_code in stocks:
    try:
        # Excel 리포트
        excel_path = OUTPUT_DIR / f"{stock_code}_{today}.xlsx"
        analyzer.export_to_excel(stock_code, start_date, end_date, str(excel_path))
        
        # HTML 리포트
        html_path = OUTPUT_DIR / f"{stock_code}_{today}.html"
        analyzer.generate_report(stock_code, start_date, end_date, str(html_path))
        
        print(f"✅ {stock_code} 리포트 생성 완료")
        
    except Exception as e:
        print(f"❌ {stock_code} 리포트 생성 실패: {e}")

print(f"\n모든 리포트가 {OUTPUT_DIR}에 저장되었습니다.")
```

### Windows 작업 스케줄러 등록

```powershell
# 매일 16:30에 실행
schtasks /create /tn "CleonAI Daily Report" /tr "D:\cleonAI\.venv\Scripts\python.exe D:\cleonAI\auto_trading\generate_daily_report.py" /sc daily /st 16:30
```

---

## 고급 분석 예제

### 상관관계 분석

```python
import pandas as pd

# 여러 종목 데이터 로드
stocks = ['005930', '000660', '035720']
dataframes = {}

for stock in stocks:
    candles = db.get_candles(stock, start_date, end_date)
    df = pd.DataFrame(candles)
    df = df.set_index('timestamp')
    dataframes[stock] = df['close']

# 데이터프레임 합치기
combined = pd.DataFrame(dataframes)

# 상관관계 행렬
correlation = combined.pct_change().corr()
print(correlation)

# 히트맵
import seaborn as sns
sns.heatmap(correlation, annot=True, cmap='coolwarm')
plt.show()
```

### 백테스팅

```python
# 단순 이동평균 전략 백테스트
df['SMA5'] = df['close'].rolling(window=5).mean()
df['SMA20'] = df['close'].rolling(window=20).mean()

# 매수/매도 신호
df['signal'] = 0
df.loc[df['SMA5'] > df['SMA20'], 'signal'] = 1  # 매수
df.loc[df['SMA5'] < df['SMA20'], 'signal'] = -1  # 매도

# 수익률 계산
df['returns'] = df['close'].pct_change()
df['strategy_returns'] = df['signal'].shift(1) * df['returns']

# 누적 수익률
cumulative_returns = (1 + df['strategy_returns']).cumprod()
print(f"최종 수익률: {(cumulative_returns.iloc[-1] - 1) * 100:.2f}%")

# 시각화
cumulative_returns.plot(figsize=(12, 6))
plt.title('백테스팅 결과')
plt.ylabel('누적 수익률')
plt.show()
```

---

## 문의 및 지원

데이터 시각화 관련 문의사항이 있으시면:

- GitHub Issues: [프로젝트 저장소]
- Email: [이메일 주소]

---

**참고 자료:**

- [DuckDB 공식 문서](https://duckdb.org/docs/)
- [Parquet 파일 포맷](https://parquet.apache.org/)
- [Grafana 문서](https://grafana.com/docs/)
- [Power BI 문서](https://docs.microsoft.com/power-bi/)

