# CleonAI Trading Platform - 프로덕션 배포 스크립트

param(
    [switch]$SkipBackup,
    [switch]$NoConfirm
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform" -ForegroundColor Cyan
Write-Host "  Production Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 환경 변수 확인
function Test-EnvironmentVariables {
    Write-Host "1. 환경 변수 확인..." -ForegroundColor Yellow
    
    $required_vars = @(
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "SECRET_KEY"
    )
    
    $missing = @()
    foreach ($var in $required_vars) {
        if (-not (Test-Path env:$var)) {
            $missing += $var
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "❌ 필수 환경 변수가 설정되지 않았습니다:" -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "다음 명령으로 환경 변수를 설정하세요:" -ForegroundColor Yellow
        Write-Host '  $env:POSTGRES_PASSWORD="your_password"' -ForegroundColor Gray
        Write-Host '  $env:REDIS_PASSWORD="your_password"' -ForegroundColor Gray
        Write-Host '  $env:SECRET_KEY="your_secret_key"' -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "✅ 환경 변수 확인 완료" -ForegroundColor Green
    Write-Host ""
}

# Docker 확인
function Test-Docker {
    Write-Host "2. Docker 확인..." -ForegroundColor Yellow
    
    try {
        $dockerVersion = docker --version
        Write-Host "   Docker: $dockerVersion" -ForegroundColor Gray
        
        $composeVersion = docker-compose --version
        Write-Host "   Docker Compose: $composeVersion" -ForegroundColor Gray
        
        Write-Host "✅ Docker 확인 완료" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker가 설치되지 않았거나 실행 중이 아닙니다" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# 데이터베이스 백업
function Backup-Database {
    if ($SkipBackup) {
        Write-Host "3. 데이터베이스 백업 건너뛰기..." -ForegroundColor Yellow
        return
    }
    
    Write-Host "3. 데이터베이스 백업..." -ForegroundColor Yellow
    
    # PostgreSQL 컨테이너 확인
    $postgresRunning = docker ps --filter "name=cleonai_postgres" --format "{{.Names}}"
    
    if ($postgresRunning) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "database/backups/backup_prod_$timestamp.sql"
        
        # 백업 디렉토리 생성
        if (-not (Test-Path "database/backups")) {
            New-Item -ItemType Directory -Path "database/backups" | Out-Null
        }
        
        Write-Host "   백업 파일: $backupFile" -ForegroundColor Gray
        
        docker exec cleonai_postgres pg_dump -U cleonai trading_db > $backupFile
        
        if ($?) {
            $fileSize = (Get-Item $backupFile).Length / 1MB
            Write-Host "✅ 백업 완료 (크기: $([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "❌ 백업 실패" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   기존 PostgreSQL 컨테이너 없음 (백업 건너뛰기)" -ForegroundColor Gray
    }
    Write-Host ""
}

# 기존 컨테이너 중지
function Stop-ExistingContainers {
    Write-Host "4. 기존 컨테이너 중지..." -ForegroundColor Yellow
    
    $runningContainers = docker ps --filter "name=cleonai" --format "{{.Names}}"
    
    if ($runningContainers) {
        Write-Host "   중지할 컨테이너:" -ForegroundColor Gray
        $runningContainers | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
        
        docker-compose -f docker-compose.prod.yml down
        Write-Host "✅ 컨테이너 중지 완료" -ForegroundColor Green
    } else {
        Write-Host "   실행 중인 컨테이너 없음" -ForegroundColor Gray
    }
    Write-Host ""
}

# Docker 이미지 빌드
function Build-DockerImages {
    Write-Host "5. Docker 이미지 빌드..." -ForegroundColor Yellow
    
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    if ($?) {
        Write-Host "✅ 이미지 빌드 완료" -ForegroundColor Green
    } else {
        Write-Host "❌ 이미지 빌드 실패" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# 컨테이너 시작
function Start-Containers {
    Write-Host "6. 컨테이너 시작..." -ForegroundColor Yellow
    
    docker-compose -f docker-compose.prod.yml up -d
    
    if ($?) {
        Write-Host "✅ 컨테이너 시작 완료" -ForegroundColor Green
    } else {
        Write-Host "❌ 컨테이너 시작 실패" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# 헬스 체크
function Test-Health {
    Write-Host "7. 헬스 체크..." -ForegroundColor Yellow
    Write-Host "   Backend 준비 대기 중..." -ForegroundColor Gray
    
    $maxAttempts = 30
    $attempt = 0
    $healthy = $false
    
    while ($attempt -lt $maxAttempts -and -not $healthy) {
        Start-Sleep -Seconds 2
        $attempt++
        
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
            if ($response.status -eq "healthy") {
                $healthy = $true
                Write-Host "✅ Backend 정상 작동" -ForegroundColor Green
            }
        } catch {
            Write-Host "   시도 $attempt/$maxAttempts..." -ForegroundColor Gray
        }
    }
    
    if (-not $healthy) {
        Write-Host "❌ Backend 헬스 체크 실패" -ForegroundColor Red
        Write-Host "   로그 확인:" -ForegroundColor Yellow
        Write-Host "   docker logs cleonai_backend_prod" -ForegroundColor Gray
        exit 1
    }
    Write-Host ""
}

# 배포 확인
function Show-DeploymentInfo {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  배포 완료!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "실행 중인 서비스:" -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml ps
    Write-Host ""
    Write-Host "접속 정보:" -ForegroundColor Yellow
    Write-Host "  - API: http://localhost:8000" -ForegroundColor Gray
    Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Gray
    Write-Host "  - Redis: localhost:6379" -ForegroundColor Gray
    Write-Host ""
    Write-Host "로그 확인:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Gray
    Write-Host ""
    Write-Host "중지:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.prod.yml down" -ForegroundColor Gray
    Write-Host ""
}

# 메인 실행
try {
    if (-not $NoConfirm) {
        Write-Host "⚠️  프로덕션 배포를 시작합니다." -ForegroundColor Yellow
        Write-Host "   계속하시겠습니까? (Y/N): " -NoNewline
        $confirm = Read-Host
        if ($confirm -ne "Y" -and $confirm -ne "y") {
            Write-Host "배포 취소됨" -ForegroundColor Yellow
            exit 0
        }
        Write-Host ""
    }
    
    Test-EnvironmentVariables
    Test-Docker
    Backup-Database
    Stop-ExistingContainers
    Build-DockerImages
    Start-Containers
    Test-Health
    Show-DeploymentInfo
    
    Write-Host "🎉 배포가 성공적으로 완료되었습니다!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ 배포 중 오류 발생:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "로그 확인:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Gray
    exit 1
}

