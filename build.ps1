Write-Host "=== Building QRCodeGen ==="

# Ensure venv active
if (-not $env:VIRTUAL_ENV) {
    Write-Error "Activate venv first: .\.venv\Scripts\Activate.ps1"
    exit 1
}

# Paths
$ROOT = (Get-Location).Path
$BUILD_ROOT = Join-Path $ROOT "..\builds"
$DIST_PATH = Join-Path $BUILD_ROOT "QRCodeGen_dist"
$WORK_PATH = Join-Path $BUILD_ROOT "QRCodeGen_build"
$SPEC_PATH = Join-Path $BUILD_ROOT "QRCodeGen_spec"

# Normalize
$BUILD_ROOT = [IO.Path]::GetFullPath($BUILD_ROOT)
$DIST_PATH = [IO.Path]::GetFullPath($DIST_PATH)
$WORK_PATH = [IO.Path]::GetFullPath($WORK_PATH)
$SPEC_PATH = [IO.Path]::GetFullPath($SPEC_PATH)

# Clean old
Remove-Item -Recurse -Force ".\dist" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $DIST_PATH -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $WORK_PATH -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $SPEC_PATH -ErrorAction SilentlyContinue

# Recreate
New-Item -ItemType Directory -Force -Path $BUILD_ROOT | Out-Null
New-Item -ItemType Directory -Force -Path $DIST_PATH | Out-Null
New-Item -ItemType Directory -Force -Path $WORK_PATH | Out-Null
New-Item -ItemType Directory -Force -Path $SPEC_PATH | Out-Null

# Absolute folder paths
$ASSETS       = Join-Path $ROOT "assets"
$DATA         = Join-Path $ROOT "data"
$CONTROLLERS  = Join-Path $ROOT "controllers"
$VIEWS        = Join-Path $ROOT "views"
$UTILS        = Join-Path $ROOT "utils"
$DATABASE     = Join-Path $ROOT "database"

# Build args
$BuildArgs = @(
    "--windowed",
    "--onedir",
    "--clean",
    "--name", "QRCodeGen",
    "--distpath", $DIST_PATH,
    "--workpath", $WORK_PATH,
    "--specpath", $SPEC_PATH,
    "--add-data", "$ASSETS;assets",
    "--add-data", "$DATA;data",
    "--add-data", "$CONTROLLERS;controllers",
    "--add-data", "$VIEWS;views",
    "--add-data", "$UTILS;utils",
    "--add-data", "$DATABASE;database",
    "--hidden-import", "sqlalchemy",
    "--hidden-import", "sqlalchemy.orm",
    "--hidden-import", "sqlalchemy.ext.declarative",
    "--hidden-import", "pyodbc",
    "--hidden-import", "weasyprint",
    "--hidden-import", "jinja2",
    "--hidden-import", "qrcode",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "PIL._tkinter_finder",
    "--hidden-import", "markupsafe",
    "--hidden-import", "cssselect",
    "--hidden-import", "cairocffi",
    "--hidden-import", "cffi",
    "--hidden-import", "xml.parsers.expat",
    "--hidden-import", "collections.abc",
    "--hidden-import", "win32timezone",
    "main.py"
)

# Run
Write-Host "Running PyInstaller..."
pyinstaller @BuildArgs
Write-Host "Build completed. Output at:"
Write-Host $DIST_PATH
