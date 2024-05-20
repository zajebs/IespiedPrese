$root = $PWD
$excludePaths = @("static\images", "__pycache__")

function Get-Tree {
    param (
        [string]$path,
        [string]$indent = ""
    )
    
    $items = Get-ChildItem -Path $path
    foreach ($item in $items) {
        $exclude = $false
        foreach ($excludePath in $excludePaths) {
            if ($item.FullName -match [regex]::Escape($excludePath)) {
                if ($item.FullName -notmatch [regex]::Escape("static\images")) {
                    $exclude = $true
                } elseif ($item.PSIsContainer) {
                    Write-Output "$indent|-- $($item.Name)"
                    $exclude = $true
                }
                break
            }
        }
        if (-not $exclude) {
            if ($item.PSIsContainer) {
                Write-Output "$indent|-- $($item.Name)"
                Get-Tree -path $item.FullName -indent "$indent|   "
            } else {
                Write-Output "$indent|-- $($item.Name)"
            }
        }
    }
}

Get-Tree -path $root
