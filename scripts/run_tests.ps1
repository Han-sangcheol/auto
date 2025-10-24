# CleonAI 테스트 실행 스크립트

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   CleonAI 테스트 실행" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Backend 테스트
Write-Host "[1/2] Backend 테스트 실행..." -ForegroundColor Yellow
Write-Host ""

Push-Location backend

# pytest 설치 확인
$pytestExists = Get-Command pytest -ErrorAction SilentlyContinue
if (-not $pytestExists) {
    Write-Host "pytest가 설치되지 않았습니다. 설치 중..." -ForegroundColor Yellow
    pip install pytest pytest-cov pytest-asyncio httpx
}

# 단위 테스트
Write-Host "단위 테스트 실행..." -ForegroundColor Cyan
pytest tests/unit -v -m unit

$backendUnitResult = $LASTEXITCODE

# 통합 테스트
Write-Host ""
Write-Host "통합 테스트 실행..." -ForegroundColor Cyan
pytest tests/integration -v -m integration

$backendIntResult = $LASTEXITCODE

Pop-Location

Write-Host ""

# 2. Trading Engine 테스트
Write-Host "[2/2] Trading Engine 테스트 실행..." -ForegroundColor Yellow
Write-Host ""

Push-Location trading-engine

# 단위 테스트
Write-Host "전략 및 지표 테스트 실행..." -ForegroundColor Cyan
pytest tests/unit -v -m unit

$engineUnitResult = $LASTEXITCODE

Pop-Location

Write-Host ""

# 결과 요약
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   테스트 결과 요약" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$allSuccess = $true

if ($backendUnitResult -eq 0) {
    Write-Host "✅ Backend 단위 테스트: 통과" -ForegroundColor Green
} else {
    Write-Host "❌ Backend 단위 테스트: 실패" -ForegroundColor Red
    $allSuccess = $false
}

if ($backendIntResult -eq 0) {
    Write-Host "✅ Backend 통합 테스트: 통과" -ForegroundColor Green
} else {
    Write-Host "❌ Backend 통합 테스트: 실패" -ForegroundColor Red
    $allSuccess = $false
}

if ($engineUnitResult -eq 0) {
    Write-Host "✅ Trading Engine 단위 테스트: 통과" -ForegroundColor Green
} else {
    Write-Host "❌ Trading Engine 단위 테스트: 실패" -ForegroundColor Red
    $allSuccess = $false
}

Write-Host ""

if ($allSuccess) {
    Write-Host "🎉 모든 테스트 통과!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️ 일부 테스트 실패" -ForegroundColor Yellow
    exit 1
}

