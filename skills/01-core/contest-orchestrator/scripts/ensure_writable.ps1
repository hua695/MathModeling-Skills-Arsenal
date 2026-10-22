# ============================================================
# ensure_writable.ps1 — skill 目录"防锁/解锁"一键脚本
# 用法（用户自己的终端，普通权限即可）:
#   powershell -ExecutionPolicy Bypass -File scripts\ensure_writable.ps1
#   或指定目标:  powershell -ExecutionPolicy Bypass -File scripts\ensure_writable.ps1 "C:\Users\USER\.agents\skills"
#
# 背景（2026-08-15 实战教训）:
#   dsh/沙箱的文件工具在 Windows 上通过 ReplaceFileW 原子替换文件，
#   要求文件 ACL 显式授予 Administrators 与当前用户 FullControl（继承的不算）。
#   缺失时表现为"write failed (ReplaceFileW EACCES)"，且无法从沙箱内自修（令牌受限）。
#   本脚本以完整令牌给目录补【带继承标志】的显式授权：
#     - 现有文件/目录立即获得显式 FullControl
#     - 未来新建的文件自动继承，不再需要重复执行
# ============================================================
param(
    [string]$Root = "$env:USERPROFILE\.agents\skills"
)

if (-not (Test-Path $Root)) {
    Write-Host "[错误] 目录不存在: $Root" -ForegroundColor Red
    exit 1
}

# 当前用户的 SID（文件所有者身份，icacls 需要 *SID 形式）
$userSid = (New-Object System.Security.Principal.WindowsIdentity).User.Value
$targets = @('*S-1-5-32-544', "*$userSid")   # Administrators + 当前用户

Write-Host ">>> 解锁目标: $Root" -ForegroundColor Cyan
foreach ($sid in $targets) {
    & icacls $Root /grant "$sid`:(OI)(CI)(F)" /T 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] icacls 对 $sid 返回非零，请检查权限" -ForegroundColor Yellow
    }
}

Write-Host ">>> 完成。检查几个关键文件是否已可写:" -ForegroundColor Cyan
foreach ($rel in @('SKILL.md', 'manifest.yaml', 'token_policy.md', 'README.md')) {
    $p = Join-Path $Root 'contest-orchestrator' $rel
    if (Test-Path $p) {
        $explicit = @((Get-Acl -LiteralPath $p).Access | Where-Object {
            -not $_.IsInherited -and $_.AccessControlType -eq 'Allow'
        }).Count
        Write-Host "  $rel : 显式 Allow ACE = $explicit" -ForegroundColor $(if ($explicit -gt 0) { 'Green' } else { 'Red' })
    }
}
Write-Host ""
Write-Host "防锁守则:" -ForegroundColor Yellow
Write-Host "  1. 不要在 WorkBuddy/编辑器里打开 skill 文件（句柄会锁住 ReplaceFileW）"
Write-Host "  2. 新建 skill 目录后跑一次本脚本（父目录 .agents\skills 已带继承授权时无需）"
Write-Host "  3. 遇到 'ReplaceFileW EACCES' 写失败 → 关掉占用编辑器，再跑本脚本"
