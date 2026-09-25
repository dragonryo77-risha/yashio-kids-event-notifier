$ErrorActionPreference = "Stop"

# 八潮こどもイベント通知(毎週水曜朝にタスクスケジューラから実行)
#  1) 地域サイトを巡回して新着を集める(Python)
#  2) Claude Codeが「子どもが本当に楽しめる・規模の大きい」ものを厳選＋Web検索で大型イベントを追加
#  3) 厳選結果をLINEに縦1枚のランキングで通知し、カレンダーページ用データをGitHubへ反映

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "last_run.log"
Start-Transcript -Path $logFile -Force | Out-Null

try {
    # スリープ解除直後はネットワークがまだ繋がっていないことがあるため、最大60秒待つ
    for ($i = 0; $i -lt 12; $i++) {
        if (Test-Connection -ComputerName "www.google.com" -Count 1 -Quiet -ErrorAction SilentlyContinue) { break }
        Start-Sleep -Seconds 5
    }

    Set-Location $root
    $env:PYTHONIOENCODING = "utf-8"

    $tokenFile = Join-Path $root "line_token.txt"
    if (-not (Test-Path $tokenFile)) { throw "line_token.txt がありません(LINEのチャネルアクセストークンを保存してください)" }
    $env:LINE_CHANNEL_ACCESS_TOKEN = (Get-Content -Path $tokenFile -Raw -Encoding UTF8).Trim()

    git pull --quiet
    if ($LASTEXITCODE -ne 0) { throw "git pull に失敗しました" }

    python src/main.py collect
    if ($LASTEXITCODE -ne 0) { throw "イベント収集に失敗しました" }

    $prompt = (Get-Content -Path (Join-Path $root "prompt.md") -Raw -Encoding UTF8)
    $claudeExe = "C:\Users\【経営管理部】龍首 凌\.local\bin\claude.exe"
    & $claudeExe -p $prompt --permission-mode bypassPermissions --tools "Read,Write,WebSearch,WebFetch"
    if ($LASTEXITCODE -ne 0) { throw "Claude Codeによる厳選に失敗しました" }

    python src/main.py notify
    if ($LASTEXITCODE -ne 0) { throw "LINE通知に失敗しました" }

    git add data/events.json docs/events.json
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit --quiet -m "chore: update events data"
        git push --quiet
    }
    Write-Output "完了"
}
catch {
    Write-Output "[ERROR] $_"
    exit 1
}
finally {
    Stop-Transcript | Out-Null
}
