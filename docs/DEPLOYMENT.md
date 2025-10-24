# CleonAI Trading Platform - 배포 가이드

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [개발 환경 설정](#개발-환경-설정)
3. [프로덕션 배포](#프로덕션-배포)
4. [모니터링 및 로깅](#모니터링-및-로깅)
5. [백업 및 복구](#백업-및-복구)
6. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 최소 요구사항

- **OS**: Windows 10/11 (64-bit)
- **CPU**: Intel Core i5 이상 또는 동급
- **RAM**: 8GB 이상
- **Storage**: 50GB 이상 여유 공간
- **Python**: 3.10+ (64-bit for Backend, 32-bit for Trading Engine)
- **Docker**: Docker Desktop for Windows (옵션)

### 권장 요구사항

- **CPU**: Intel Core i7 이상 또는 동급
- **RAM**: 16GB 이상
- **Storage**: SSD 100GB 이상
- **네트워크**: 안정적인 인터넷 연결

### 필수 소프트웨어

- Python 3.10+ (64-bit)
- Python 3.10 (32-bit for Kiwoom API)
- Docker Desktop
- PostgreSQL 15+
- Redis 7+
- Git

---

## 개발 환경 설정

### 1. 저장소 클론

```powershell
git clone https://github.com/yourusername/cleonai-trading-platform.git
cd cleonai-trading-platform
```

### 2. 환경 변수 설정

```powershell
# .env.example을 .env로 복사
cp env.template .env

# .env 파일 편집 (실제 값 입력)
notepad .env
```

**필수 환경 변수:**
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `SECRET_KEY`

### 3. Docker 서비스 시작

```powershell
# PostgreSQL과 Redis 시작
docker-compose up -d postgres redis
```

### 4. Backend 설정

```powershell
cd backend

# 가상환경 생성 (64-bit Python)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# Backend 시작
uvicorn app.main:app --reload
```

**확인:**
- http://localhost:8000/docs - API 문서
- http://localhost:8000/health - 헬스 체크

### 5. Trading Engine 설정

```powershell
cd trading-engine

# 가상환경 생성 (32-bit Python)
C:\Python310-32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# 설정 확인
python -c "from engine.core.config import Config; Config.print_config()"
```

### 6. Frontend 설정

```powershell
cd frontend

# 가상환경 생성 (64-bit Python)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# Frontend 시작
python main.py
```

---

## 프로덕션 배포

### 1. 프로덕션 환경 변수 설정

```powershell
# .env.prod 파일 생성
cp .env.example .env.prod
```

**프로덕션 필수 설정:**
```env
ENVIRONMENT=production
DEBUG=false

# 강력한 비밀번호 설정
POSTGRES_PASSWORD=<strong_password>
REDIS_PASSWORD=<strong_password>
SECRET_KEY=<generate_using_openssl>

# 실계좌 설정 (주의!)
USE_SIMULATION=false
KIWOOM_ACCOUNT_NUMBER=<your_account>

# 보안 설정
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

### 2. 비밀 키 생성

```powershell
# OpenSSL로 강력한 비밀 키 생성
openssl rand -hex 32
```

### 3. Docker Compose 프로덕션 실행

```powershell
# 환경 변수 로드
$env:POSTGRES_PASSWORD="your_password"
$env:REDIS_PASSWORD="your_password"
$env:SECRET_KEY="your_secret_key"

# 프로덕션 환경 시작
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. 데이터베이스 초기화

```powershell
# PostgreSQL 컨테이너 접속
docker exec -it cleonai_postgres_prod psql -U cleonai -d trading_db

# 초기 데이터 확인
SELECT * FROM users;
SELECT * FROM accounts;
```

### 5. 헬스 체크

```powershell
# Backend 헬스 체크
Invoke-RestMethod http://localhost:8000/health

# 예상 출력:
# {
#   "status": "healthy",
#   "environment": "production"
# }
```

### 6. Nginx 설정 (옵션)

**nginx.conf 예시:**
```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 모니터링 및 로깅

### 1. 로그 확인

```powershell
# Backend 로그
docker logs cleonai_backend_prod -f

# PostgreSQL 로그
docker logs cleonai_postgres_prod -f

# Redis 로그
docker logs cleonai_redis_prod -f
```

### 2. 로그 파일 위치

- **Backend**: `backend/logs/`
- **Trading Engine**: `trading-engine/logs/`
- **PostgreSQL**: Docker 볼륨
- **Nginx**: `docker/nginx/logs/`

### 3. 로그 레벨 설정

**.env 파일:**
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### 4. 시스템 메트릭 모니터링

```powershell
# Docker 컨테이너 상태
docker stats

# 디스크 사용량
docker system df

# PostgreSQL 연결 수
docker exec cleonai_postgres_prod psql -U cleonai -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 백업 및 복구

### 1. 데이터베이스 백업

```powershell
# 수동 백업
docker exec cleonai_postgres_prod pg_dump -U cleonai trading_db > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# 백업 디렉토리로 이동
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec cleonai_postgres_prod pg_dump -U cleonai trading_db > database/backups/backup_$timestamp.sql
```

### 2. 자동 백업 스크립트

**scripts/backup_database.ps1:**
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "database/backups/backup_$timestamp.sql"

docker exec cleonai_postgres_prod pg_dump -U cleonai trading_db > $backupFile

if ($?) {
    Write-Host "✅ 백업 완료: $backupFile" -ForegroundColor Green
    
    # 30일 이상 된 백업 삭제
    Get-ChildItem "database/backups" -Filter "*.sql" | 
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
        Remove-Item
} else {
    Write-Host "❌ 백업 실패" -ForegroundColor Red
}
```

### 3. 데이터베이스 복구

```powershell
# 백업 파일에서 복구
Get-Content backup_20251024_120000.sql | 
    docker exec -i cleonai_postgres_prod psql -U cleonai trading_db
```

### 4. Redis 백업

```powershell
# Redis 데이터 저장
docker exec cleonai_redis_prod redis-cli SAVE

# 백업 파일 복사
docker cp cleonai_redis_prod:/data/dump.rdb redis_backup_$(Get-Date -Format "yyyyMMdd").rdb
```

---

## 문제 해결

### 1. Backend 연결 실패

**증상:** Frontend가 Backend에 연결할 수 없음

**해결:**
```powershell
# Backend 상태 확인
docker ps | findstr backend

# Backend 로그 확인
docker logs cleonai_backend_prod

# 포트 확인
netstat -ano | findstr 8000

# Backend 재시작
docker-compose restart backend
```

### 2. PostgreSQL 연결 오류

**증상:** `could not connect to server`

**해결:**
```powershell
# PostgreSQL 상태 확인
docker exec cleonai_postgres_prod pg_isready -U cleonai

# 연결 테스트
docker exec -it cleonai_postgres_prod psql -U cleonai -d trading_db -c "SELECT 1;"

# 재시작
docker-compose restart postgres
```

### 3. Redis 연결 오류

**증상:** `Connection refused`

**해결:**
```powershell
# Redis 상태 확인
docker exec cleonai_redis_prod redis-cli ping

# 재시작
docker-compose restart redis
```

### 4. Trading Engine 시작 실패

**증상:** Engine이 시작되지 않음

**해결:**
```powershell
# 32-bit Python 확인
python --version

# 키움 OpenAPI 설치 확인
# KOA Studio 실행 및 로그인 테스트

# 환경 변수 확인
python -c "from engine.core.config import Config; Config.print_config()"

# 로그 확인
Get-Content trading-engine/logs/trading.log -Tail 50
```

### 5. 메모리 부족

**증상:** 시스템이 느려지거나 서비스가 중지됨

**해결:**
```powershell
# Docker 메모리 사용량 확인
docker stats --no-stream

# 사용하지 않는 컨테이너 정리
docker system prune -a

# Docker Desktop 메모리 설정 증가 (Settings > Resources)
```

---

## 업데이트 및 롤백

### 1. 애플리케이션 업데이트

```powershell
# 코드 업데이트
git pull origin main

# 패키지 업데이트
cd backend
pip install -r requirements.txt --upgrade

# 데이터베이스 마이그레이션
alembic upgrade head

# 서비스 재시작
docker-compose restart backend
```

### 2. 롤백

```powershell
# Git으로 이전 버전 복구
git log --oneline
git checkout <commit_hash>

# 데이터베이스 롤백
alembic downgrade -1

# 서비스 재시작
docker-compose restart
```

---

## 보안 체크리스트

- [ ] 모든 기본 비밀번호 변경
- [ ] SECRET_KEY 강력한 값으로 설정
- [ ] CORS 설정 확인
- [ ] 실계좌 환경 변수 확인
- [ ] 로그에 민감 정보 없는지 확인
- [ ] 방화벽 설정 확인
- [ ] SSL/TLS 인증서 설정 (프로덕션)
- [ ] 정기 백업 설정
- [ ] 로그 로테이션 설정

---

## 성능 최적화

### 1. PostgreSQL 최적화

```sql
-- 인덱스 확인
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';

-- 느린 쿼리 찾기
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- VACUUM
VACUUM ANALYZE;
```

### 2. Redis 최적화

```redis
# 메모리 사용량 확인
INFO memory

# 키 개수 확인
DBSIZE

# 만료된 키 정리
FLUSHDB
```

### 3. Backend 워커 수 조정

**docker-compose.prod.yml:**
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**권장 워커 수:** `(CPU 코어 수 × 2) + 1`

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Docker 공식 문서](https://docs.docker.com/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation)
- [키움 OpenAPI 가이드](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)

---

**작성일**: 2025-10-24  
**버전**: 1.0  
**담당자**: CleonAI Development Team

