param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Normalize-FullExport {
    param(
        [string]$RawPath,
        [string]$NormalizedPath
    )

    if (-not (Test-Path -LiteralPath $RawPath)) {
        Write-Host "Raw full export not found, skipping: $RawPath"
        return
    }

    Write-Host "Normalizing full export:"
    Write-Host "  Raw:        $RawPath"
    Write-Host "  Normalized: $NormalizedPath"

    $content = Get-Content -LiteralPath $RawPath -Raw

    $content = $content -replace "`r?`n", "`r`n"

    $content = $content -replace '(?im)^(Export(Date|ed On| Time)?)\s*:\s*.*$', 'Exported: <normalized>'
    $content = $content -replace '(?im)^(Generated(Date| On| Time)?)\s*:\s*.*$', 'Generated: <normalized>'
    $content = $content -replace '(?im)^(Machine(Name)?)\s*:\s*.*$', 'Machine: <normalized>'
    $content = $content -replace '(?im)^(Computer(Name)?)\s*:\s*.*$', 'Computer: <normalized>'

    $lines = $content -split "`r`n" | ForEach-Object { $_.TrimEnd() }

    $cleanLines = New-Object System.Collections.Generic.List[string]
    $previousBlank = $false
    foreach ($line in $lines) {
        $isBlank = [string]::IsNullOrWhiteSpace($line)
        if ($isBlank) {
            if (-not $previousBlank) {
                $cleanLines.Add("")
            }
        } else {
            $cleanLines.Add($line)
        }
        $previousBlank = $isBlank
    }

    $normalized = ($cleanLines -join "`r`n").TrimEnd() + "`r`n"

    Ensure-Directory -Path ([System.IO.Path]::GetDirectoryName($NormalizedPath))
    Set-Content -LiteralPath $NormalizedPath -Value $normalized -Encoding UTF8
}

$fullRawDir = Join-Path $RepoRoot "exports\full\raw"
$fullNormDir = Join-Path $RepoRoot "exports\full\normalized"

$rawFullExport = Join-Path $fullRawDir "Historian_Full_Configuration_Export.txt"
$normalizedFullExport = Join-Path $fullNormDir "Historian_Full_Configuration_Export.normalized.txt"

Ensure-Directory -Path $fullNormDir
Normalize-FullExport -RawPath $rawFullExport -NormalizedPath $normalizedFullExport

Write-Host "Normalization complete."