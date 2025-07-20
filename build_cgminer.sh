#!/usr/bin/env bash
set -e

echo "Building cgminer_zeus from vendored source..."

# Install build dependencies if not already present
if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y \
        git build-essential automake autoconf pkg-config libtool \
        libcurl4-openssl-dev libusb-1.0-0-dev libjansson-dev libncurses5-dev \
        yasm || true
fi

# Use vendored cgminer_zeus source
CGMINER_DIR="./vendor/cgminer_zeus"

if [ ! -d "$CGMINER_DIR" ]; then
    echo "Error: vendored cgminer_zeus source not found at $CGMINER_DIR"
    exit 1
fi

cd "$CGMINER_DIR"

echo "Preparing cgminer_zeus build environment..."

# Initialize submodules if present
git submodule update --init --recursive || true

# Make scripts executable
chmod +x autogen.sh configure || true

# Generate build files
echo "Running autogen.sh..."
if [ -f "autogen.sh" ]; then
    ./autogen.sh || true
else
    autoreconf -fiv || true
fi

# Configure with Zeus-optimized settings
echo "Configuring cgminer_zeus with optimal settings..."
CFLAGS="-O3 -march=native -mtune=native -Wall -Wextra" \
CXXFLAGS="-O3 -march=native -mtune=native -Wall -Wextra" \
./configure \
    --enable-icarus \
    --enable-zeus \
    --disable-scrypt \
    --disable-opencl \
    --disable-adl \
    --disable-avalon \
    --disable-bfl \
    --disable-bitforce \
    --disable-modminer \
    --with-system-libusb \
    --prefix=/usr/local || \
./configure \
    --enable-icarus \
    --disable-scrypt \
    --disable-opencl \
    --disable-adl \
    --prefix=/usr/local

# Build with multiple cores
echo "Building cgminer_zeus..."
make clean || true
make -j$(nproc) || make -j1

# Install
echo "Installing cgminer_zeus..."
make install

# Verify installation
if command -v cgminer >/dev/null 2>&1; then
    echo "cgminer_zeus build successful!"
    cgminer --version || true
    
    # Create symlink for convenience
    ln -sf /usr/local/bin/cgminer /usr/local/bin/cgminer_zeus || true
    
    echo "cgminer_zeus installed at: $(which cgminer)"
else
    echo "Warning: cgminer not found in PATH after installation"
fi

# Return to original directory
cd - >/dev/null

echo "Build script completed." 