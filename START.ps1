# CleonAI Trading Platform - 통합 런처 (PowerShell)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CleonAI Trading Platform" -ForegroundColor Cyan
Write-Host "  통합 런처 시작" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

python launcher.py

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")




