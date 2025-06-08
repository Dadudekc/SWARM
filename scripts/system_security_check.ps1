# System Security Check Script
# Purpose: Verifies system compatibility for Tails OS and secure operations
# Author: Dream.OS Security Team
# Version: 1.0.0

# Requires admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator!"
    exit
}

# ANSI color codes for better visibility
$colors = @{
    Info = "Cyan"
    Warning = "Yellow"
    Error = "Red"
    Success = "Green"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color
    )
    Write-Host $Message -ForegroundColor $Color
}

function Get-SystemInfo {
    Write-ColorOutput "`n🔍 Running System Diagnostics..." $colors.Info
    
    # CPU Information
    $cpu = Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
    Write-ColorOutput "`n🧠 CPU Information:" $colors.Header
    $cpu | Format-List

    # RAM Information
    $ram = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB
    Write-ColorOutput "`n🧬 RAM: $([math]::Round($ram, 2)) GB" $colors.Header

    # Storage Information
    Write-ColorOutput "`n💽 Storage Devices:" $colors.Header
    Get-Volume | Where-Object {$_.DriveLetter} | Select-Object DriveLetter, FileSystemLabel, FileSystem, @{
        Name="FreeSpace(GB)";Expression={[math]::Round($_.SizeRemaining/1GB, 2)}
    }, @{
        Name="TotalSize(GB)";Expression={[math]::Round($_.Size/1GB, 2)}
    } | Format-Table -AutoSize

    # Security Features
    Write-ColorOutput "`n🛡️ Security Features:" $colors.Header
    
    # Secure Boot Status
    $secureBoot = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
    Write-ColorOutput "Secure Boot: $secureBoot" $colors.Info

    # TPM Status
    $tpm = Get-WmiObject -Namespace "Root\CIMv2\Security\MicrosoftTpm" -Class Win32_Tpm -ErrorAction SilentlyContinue
    if ($tpm) {
        Write-ColorOutput "TPM Version: $($tpm.SpecVersion)" $colors.Info
    } else {
        Write-ColorOutput "TPM: Not Available" $colors.Warning
    }

    # UEFI Status
    $firmware = (Get-CimInstance Win32_ComputerSystem).BootupState
    Write-ColorOutput "Boot Mode: $firmware" $colors.Info

    # Virtualization Status
    $vt = Get-WmiObject Win32_Processor | Select-Object -ExpandProperty VirtualizationFirmwareEnabled
    Write-ColorOutput "Virtualization: $vt" $colors.Info

    # USB Ports
    Write-ColorOutput "`n🔌 USB Ports:" $colors.Header
    Get-WmiObject Win32_USBController | Select-Object Name, Status | Format-Table -AutoSize

    # Tails Compatibility Check
    Write-ColorOutput "`n📋 Tails OS Compatibility Check:" $colors.Header
    $compatibility = @{
        RAM = $ram -ge 8
        SecureBoot = -not $secureBoot
        UEFI = $firmware -eq "Normal boot"
        Virtualization = $vt
    }

    $allCompatible = $true
    foreach ($check in $compatibility.GetEnumerator()) {
        $status = if ($check.Value) { "✅" } else { "❌" }
        $color = if ($check.Value) { $colors.Success } else { $colors.Error }
        Write-ColorOutput "$status $($check.Key): $($check.Value)" $color
        if (-not $check.Value) { $allCompatible = $false }
    }

    # Final Recommendation
    Write-ColorOutput "`n📊 System Readiness Assessment:" $colors.Header
    if ($allCompatible) {
        Write-ColorOutput "✅ Your system is READY for Tails OS and secure operations!" $colors.Success
    } else {
        Write-ColorOutput "⚠️ Your system needs some adjustments before running Tails OS:" $colors.Warning
        if (-not $compatibility.RAM) {
            Write-ColorOutput "  - Upgrade RAM to at least 8GB" $colors.Warning
        }
        if ($compatibility.SecureBoot) {
            Write-ColorOutput "  - Disable Secure Boot in BIOS/UEFI" $colors.Warning
        }
        if (-not $compatibility.UEFI) {
            Write-ColorOutput "  - Enable UEFI boot mode" $colors.Warning
        }
    }

    Write-ColorOutput "`n🔚 Diagnostics complete." $colors.Info
}

# Run the diagnostics
Get-SystemInfo 