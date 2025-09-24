#!/bin/bash

echo "Building Hot LapY executable..."
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist hot_lap.spec

# Build the executable with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller --onefile --windowed --name "HotLapY" hot_lap.py

# Check if build was successful
if [ ! -f "dist/HotLapY.exe" ] && [ ! -f "dist/HotLapY" ]; then
    echo
    echo "ERROR: Build failed! Executable not found in dist folder."
    exit 1
fi

# Copy assets folder to dist
echo "Copying assets folder..."
cp -r assets dist/

# Create a final distribution folder
echo "Creating final distribution..."
rm -rf release/HotLapY
mkdir -p release/HotLapY

# Copy executable and assets to release folder
if [ -f "dist/HotLapY.exe" ]; then
    cp dist/HotLapY.exe release/HotLapY/
    EXECUTABLE="HotLapY.exe"
else
    cp dist/HotLapY release/HotLapY/
    chmod +x release/HotLapY/HotLapY
    EXECUTABLE="HotLapY"
fi

cp -r dist/assets release/HotLapY/

echo
echo "========================================"
echo "Build completed successfully!"
echo
echo "Executable location: release/HotLapY/$EXECUTABLE"
echo "Assets copied to: release/HotLapY/assets/"
echo
echo "You can now distribute the entire 'release/HotLapY' folder"
echo "========================================"
echo