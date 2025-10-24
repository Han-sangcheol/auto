# CleonAI 통합 테스트 스크립트
# Phase 5: 통합 및 테스트

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   CleonAI 통합 테스트" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Backend 헬스 체크
Write-Host "[1/5] Backend 헬스 체크..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Backend 정상: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend 연결 실패. Backend를 먼저 실행하세요." -ForegroundColor Red
    Write-Host "   실행 방법: .\scripts\start_backend.ps1" -ForegroundColor Yellow
    exit 1
}

# 2. 데이터베이스 연결 테스트
Write-Host "[2/5] 데이터베이스 연결 테스트..." -ForegroundColor Yellow
try {
    $accounts = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/account/" -Method Get
    Write-Host "✅ 데이터베이스 연결 정상 (계좌 수: $($accounts.Count))" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 데이터베이스 연결 실패: $_" -ForegroundColor Yellow
}

# 3. API 엔드포인트 테스트
Write-Host "[3/5] API 엔드포인트 테스트..." -ForegroundColor Yellow

$endpoints = @(
    @{ Method = "GET"; Uri = "/api/v1/account/"; Name = "계좌 조회" },
    @{ Method = "GET"; Uri = "/api/v1/market/surge?limit=5"; Name = "급등주 조회" },
    @{ Method = "GET"; Uri = "/api/v1/logs?limit=10"; Name = "로그 조회" },
    @{ Method = "GET"; Uri = "/api/v1/engine/status"; Name = "Engine 상태" }
)

$successCount = 0
$failCount = 0

foreach ($endpoint in $endpoints) {
    try {
        $fullUri = "http://localhost:8000$($endpoint.Uri)"
        $response = Invoke-RestMethod -Uri $fullUri -Method $endpoint.Method -ErrorAction Stop
        Write-Host "  ✅ $($endpoint.Name)" -ForegroundColor Green
        $successCount++
    } catch {
        Write-Host "  ❌ $($endpoint.Name): $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "API 테스트 결과: $successCount 성공, $failCount 실패" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

# 4. WebSocket 연결 테스트 (간단히 체크)
Write-Host "[4/5] WebSocket 엔드포인트 확인..." -ForegroundColor Yellow
try {
    # WebSocket은 실제 연결 테스트가 어려우므로 API 문서로 확인
    $docs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/openapi.json" -Method Get -ErrorAction SilentlyContinue
    if ($docs) {
        Write-Host "✅ API 문서 접근 가능 (WebSocket 엔드포인트 확인 가능)" -ForegroundColor Green
        Write-Host "   WebSocket 경로: ws://localhost:8000/ws/*" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️ API 문서 접근 실패" -ForegroundColor Yellow
}

# 5. Frontend 실행 가능 여부 확인
Write-Host "[5/5] Frontend 환경 확인..." -ForegroundColor Yellow
if (Test-Path "frontend\main.py") {
    Write-Host "✅ Frontend 파일 존재" -ForegroundColor Green
    
    # requirements 확인
    if (Test-Path "frontend\requirements.txt") {
        Write-Host "✅ requirements.txt 존재" -ForegroundColor Green
    }
    
    Write-Host "   Frontend 실행 방법: .\scripts\start_frontend.ps1" -ForegroundColor Cyan
} else {
    Write-Host "❌ Frontend 파일 없음" -ForegroundColor Red
}

# 결과 요약
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   통합 테스트 완료" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "✅ 모든 테스트 통과!" -ForegroundColor Green
    Write-Host ""
    Write-Host "다음 단계:" -ForegroundColor Yellow
    Write-Host "  1. Frontend 실행: .\scripts\start_frontend.ps1" -ForegroundColor Cyan
    Write-Host "  2. GUI에서 'Engine 시작' 버튼 클릭" -ForegroundColor Cyan
    Write-Host "  3. 자동매매 테스트 시작" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ 일부 테스트 실패 ($failCount 개)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "문제 해결:" -ForegroundColor Yellow
    Write-Host "  1. Backend가 실행 중인지 확인" -ForegroundColor Cyan
    Write-Host "  2. PostgreSQL/Redis가 실행 중인지 확인" -ForegroundColor Cyan
    Write-Host "  3. 로그 확인: backend/app/logs/" -ForegroundColor Cyan
}

Write-Host ""

