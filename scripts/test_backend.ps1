# Backend API 테스트 스크립트

Write-Host "Testing CleonAI Backend API..." -ForegroundColor Green
Write-Host ""

$baseUrl = "http://localhost:8000"

# 1. Health Check
Write-Host "1. Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "   Status: $($response.status)" -ForegroundColor Green
    Write-Host "   Environment: $($response.environment)" -ForegroundColor Green
} catch {
    Write-Host "   Error: Backend not running" -ForegroundColor Red
    Write-Host "   Please start backend first: python app/main.py" -ForegroundColor Red
    exit 1
}

# 2. Root Endpoint
Write-Host ""
Write-Host "2. Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "   Message: $($response.message)" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. API Documentation
Write-Host ""
Write-Host "3. API Documentation..." -ForegroundColor Yellow
Write-Host "   Swagger UI: $baseUrl/docs" -ForegroundColor Cyan
Write-Host "   ReDoc: $baseUrl/redoc" -ForegroundColor Cyan
Write-Host "   OpenAPI JSON: $baseUrl/api/v1/openapi.json" -ForegroundColor Cyan

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green
Write-Host "You can now test API endpoints at: $baseUrl/docs" -ForegroundColor Cyan

