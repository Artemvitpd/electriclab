# HybridCache PowerShell Launcher
# Запускает HybridCache с правильной активацией виртуального окружения

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HybridCache PowerShell Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Переходим в директорию скрипта
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Рабочая директория: $ScriptDir" -ForegroundColor Yellow

# Проверяем существование виртуального окружения
$VenvPath = Join-Path $ScriptDir "hybridcache_env"
if (!(Test-Path $VenvPath)) {
    Write-Host "[ERROR] Виртуальное окружение не найдено: $VenvPath" -ForegroundColor Red
    Write-Host "Запустите сначала install.bat для создания виртуального окружения" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем существование основного файла
$MainFile = Join-Path $ScriptDir "hybridcache_symlink_hotcache_project_Version10.py"
if (!(Test-Path $MainFile)) {
    Write-Host "[ERROR] Основной файл не найден: $MainFile" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "[INFO] Активация виртуального окружения..." -ForegroundColor Green

# Активируем виртуальное окружение через batch файл (более надежно)
$ActivateBat = Join-Path $VenvPath "Scripts\activate.bat"
if (Test-Path $ActivateBat) {
    # Запускаем активацию через cmd
    cmd /c "call `"$ActivateBat`" && python `"$MainFile`""
} else {
    Write-Host "[ERROR] Файл активации не найден: $ActivateBat" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "`nНажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
