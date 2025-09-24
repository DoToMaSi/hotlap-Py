@echo off
echo Building Hot LapY executable...
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "hot_lap.spec" del "hot_lap.spec"

REM Build the executable with PyInstaller
echo Building executable with PyInstaller...
pyinstaller --onefile --windowed --name "HotLapY" hot_lap.py

REM Check if build was successful
if not exist "dist\HotLapY.exe" (
    echo.
    echo ERROR: Build failed! HotLapY.exe not found in dist folder.
    pause
    exit /b 1
)

REM Copy assets folder to dist
echo Copying assets folder...
xcopy /e /i "assets" "dist\assets"

REM Create a final distribution folder
echo Creating final distribution...
if not exist "release" mkdir "release"
if exist "release\HotLapY" rmdir /s /q "release\HotLapY"
mkdir "release\HotLapY"

REM Copy executable and assets to release folder
copy "dist\HotLapY.exe" "release\HotLapY\"
xcopy /e /i "dist\assets" "release\HotLapY\assets"

echo.
echo ========================================
echo Build completed successfully!
echo.
echo Executable location: release\HotLapY\HotLapY.exe
echo Assets copied to: release\HotLapY\assets\
echo.
echo You can now distribute the entire "release\HotLapY" folder
echo ========================================
echo.
pause