param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectDir
)

$results = @()
function Add-Result([string]$name, [bool]$pass, [string]$detail = "") {
    $script:results += [pscustomobject]@{ Item = $name; Pass = $pass; Detail = $detail }
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    Write-Output "Fail: 项目文件夹不存在 -> $ProjectDir"
    exit 1
}

# 1. 汇报大纲.md：存在 + 三节齐全 + 无残留占位符
$outline = Join-Path $ProjectDir "汇报大纲.md"
if (Test-Path -LiteralPath $outline) {
    $oc = Get-Content -LiteralPath $outline -Raw -Encoding UTF8
    Add-Result "汇报大纲.md 存在" $true
    foreach ($sec in @("## 1 背景", "## 2 最终要回答的问题", "## 3 核心假设")) {
        Add-Result "大纲含「$sec」" ($oc.Contains($sec))
    }
    $leftover = ([regex]::Matches($oc, "\{\{")).Count
    Add-Result "无残留占位符" ($leftover -eq 0) ("残留 $leftover 处 {{ }}" )
} else {
    Add-Result "汇报大纲.md 存在" $false
}

# 2. 数据BRD.md
$brd = Join-Path $ProjectDir "数据BRD.md"
Add-Result "数据BRD.md 存在" (Test-Path -LiteralPath $brd)

# 3. 产出数据结构
$pd = Join-Path $ProjectDir "产出数据"
Add-Result "产出数据/ 目录存在" (Test-Path -LiteralPath $pd)
if (Test-Path -LiteralPath $pd) {
    $xlsx = Get-ChildItem -LiteralPath $pd -Filter *.xlsx -File -ErrorAction SilentlyContinue
    Add-Result "产出数据/ 根目录有最终 xlsx" ($xlsx.Count -gt 0) ("发现 $($xlsx.Count) 个")
    Add-Result "产出数据/过程数据/ 存在" (Test-Path -LiteralPath (Join-Path $pd "过程数据"))
    Add-Result "产出数据/Script/ 存在" (Test-Path -LiteralPath (Join-Path $pd "Script"))
}

# 4. set / 配套文档
Add-Result "set/ 存在" (Test-Path -LiteralPath (Join-Path $ProjectDir "set"))
Add-Result "配套文档/ 存在" (Test-Path -LiteralPath (Join-Path $ProjectDir "配套文档"))

# 5. 汇报.html（提醒级，不计入失败）
$hasHtml = Test-Path -LiteralPath (Join-Path $ProjectDir "汇报.html")
Add-Result "汇报.html（S6 后应有，提醒级）" $true $(if ($hasHtml) { "存在" } else { "尚未生成（S6 产出）" })

$failed = $results | Where-Object { -not $_.Pass }
foreach ($r in $results) {
    $tag = if ($r.Pass) { "Success" } else { "Fail  " }
    $d = if ($r.Detail) { " | " + $r.Detail } else { "" }
    Write-Output "$tag : $($r.Item)$d"
}
if ($failed.Count -gt 0) {
    Write-Output "Result: $($failed.Count) 项未通过，修复后重跑。"
    exit 1
}
Write-Output "Result: 全部通过。"
exit 0
