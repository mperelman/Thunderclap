# PowerShell Script Best Practices

## Critical Rules (NEVER VIOLATE)

### 1. `param()` Block Must Be First
**RULE:** The `param()` block MUST be the very first executable statement in a PowerShell script (after comments only).

**WRONG:**
```powershell
# Script header
$someVariable = "value"  # ❌ NO - executable code before param()
param([string]$MyParam)
```

**CORRECT:**
```powershell
# Script header
param([string]$MyParam)  # ✅ YES - param() is first
$someVariable = "value"
```

**Why:** PowerShell requires `param()` to be at the top. Any executable code before it causes a parser error.

### 2. Path Resolution After Directory Changes
**RULE:** If you change directories with `Set-Location`, you MUST resolve relative paths AFTER the directory change, not before.

**WRONG:**
```powershell
param([string]$SourceFile = "data\file.txt")
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
# ❌ $SourceFile is still relative to original directory!
$fileBytes = [System.IO.File]::ReadAllBytes($SourceFile)
```

**CORRECT:**
```powershell
param([string]$SourceFile = "data\file.txt")
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
# ✅ Resolve path AFTER changing directory
$SourceFile = Join-Path $projectRoot $SourceFile
$fileBytes = [System.IO.File]::ReadAllBytes($SourceFile)
```

**Why:** Relative paths are resolved relative to the current working directory. If you change directories, relative paths from before the change are invalid.

### 3. Always Test Scripts from Different Directories
**RULE:** Scripts should work when run from ANY directory, not just the project root.

**Test from:**
- Project root: `C:\Users\perel\OneDrive\Apps\thunderclap-ai\`
- User home: `C:\Users\perel\`
- Different drive: `D:\`
- Subdirectory: `C:\Users\perel\OneDrive\Apps\thunderclap-ai\scripts\`

**Pattern to Use:**
```powershell
param(...)

# Get script location and project root
$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $scriptDir -Parent

# Change to project root
Set-Location $projectRoot

# Resolve all relative paths to absolute paths
$SourceFile = Join-Path $projectRoot "data\file.txt"
$ConfigFile = Join-Path $projectRoot "config.json"
```

### 4. Use `Join-Path` for Path Construction
**RULE:** Always use `Join-Path` to construct file paths, never string concatenation.

**WRONG:**
```powershell
$filePath = "$projectRoot\data\file.txt"  # ❌ Backslash issues on different systems
```

**CORRECT:**
```powershell
$filePath = Join-Path $projectRoot "data\file.txt"  # ✅ Works on all systems
```

### 5. Verify File Existence Before Use
**RULE:** Always check if files exist before trying to read them, and provide clear error messages.

**CORRECT:**
```powershell
$SourceFile = Join-Path $projectRoot "data\file.txt"
if (-not (Test-Path $SourceFile)) {
    Write-Host "ERROR: Source file not found: $SourceFile" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
    exit 1
}
```

## Common Mistakes to Avoid

### Mistake 1: Executable Code Before `param()`
**Error:** `The assignment expression is not valid`
**Fix:** Move all executable code after `param()` block

### Mistake 2: Relative Paths After Directory Change
**Error:** `Could not find a part of the path`
**Fix:** Resolve paths to absolute paths after `Set-Location`

### Mistake 3: Assuming Current Directory
**Error:** Script works in one directory, fails in another
**Fix:** Always change to project root and resolve paths explicitly

### Mistake 4: String Interpolation in Paths
**Error:** Path issues on different systems
**Fix:** Use `Join-Path` instead of string concatenation

## Template for New PowerShell Scripts

```powershell
# Script description
# Author: [Your name]
# Date: [Date]

# CRITICAL: param() MUST be first (after comments only)
param(
    [string]$Param1 = "default",
    [string]$Param2 = "relative\path"
)

# Get script location and project root
$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $scriptDir -Parent

# Change to project root
Set-Location $projectRoot
Write-Host "Working directory: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Resolve all relative paths to absolute paths
$Param2 = Join-Path $projectRoot $Param2

# Verify files exist
if (-not (Test-Path $Param2)) {
    Write-Host "ERROR: File not found: $Param2" -ForegroundColor Red
    exit 1
}

# Rest of script...
```

## Testing Checklist

Before committing a PowerShell script:

- [ ] Script has `param()` block at the top (after comments only)
- [ ] All relative paths are resolved after directory changes
- [ ] Script tested from project root directory
- [ ] Script tested from user home directory (`C:\Users\username\`)
- [ ] Script tested from a different directory
- [ ] All file paths use `Join-Path`, not string concatenation
- [ ] File existence checks with clear error messages
- [ ] Error messages include full paths for debugging

## Lessons Learned from Real Mistakes

### Case 1: upload_database_http.ps1
**Mistake:** Put `Set-Location` before `param()` block
**Error:** `The assignment expression is not valid`
**Lesson:** `param()` MUST be first executable statement

### Case 2: upload_database_http.ps1 (again)
**Mistake:** Used relative path before resolving it after directory change
**Error:** `Could not find a part of the path 'C:\Users\perel\data\...'`
**Lesson:** Always resolve paths AFTER changing directories

### Case 3: rebuild_and_upload_to_railway.ps1
**Mistake:** Script only worked when run from project root
**Error:** `Source file not found: data\vectordb\chroma.sqlite3`
**Lesson:** Scripts must work from any directory - always change to project root first

## Summary

1. **`param()` first** - Always, no exceptions
2. **Resolve paths after directory changes** - Relative paths break after `Set-Location`
3. **Test from multiple directories** - Scripts should work anywhere
4. **Use `Join-Path`** - Never string concatenation for paths
5. **Verify files exist** - Check before reading, with clear errors

**Remember:** If a script works in one directory but not another, you have a path resolution problem. Fix it by changing to project root and resolving all paths explicitly.
