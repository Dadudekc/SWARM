# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator"
    Write-Host "Right-click on PowerShell and select 'Run as Administrator'"
    exit 1
}

$tesseractPath = "C:\Program Files\Tesseract-OCR"

# Check if Tesseract exists
if (Test-Path $tesseractPath) {
    Write-Host "Found Tesseract at $tesseractPath"
    
    # Get current PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    
    # Check if Tesseract is already in PATH
    if ($currentPath -notlike "*$tesseractPath*") {
        # Add Tesseract to PATH
        $newPath = $currentPath + ";" + $tesseractPath
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Host "✓ Added Tesseract to system PATH"
    } else {
        Write-Host "✓ Tesseract is already in PATH"
    }
    
    Write-Host "`nTesseract has been added to PATH!"
    Write-Host "Please restart your terminal/PowerShell window for the changes to take effect."
} else {
    Write-Host "✗ Tesseract not found at $tesseractPath"
    exit 1
} 