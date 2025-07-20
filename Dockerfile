# Use Ubuntu base image for better cgminer compatibility
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    git \
    build-essential \
    automake \
    autoconf \
    pkg-config \
    libtool \
    libcurl4-openssl-dev \
    libusb-1.0-0-dev \
    libjansson-dev \
    libncurses5-dev \
    curl \
    htop \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Create Python symlinks
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Build cgminer_zeus from vendored source
RUN chmod +x build_cgminer.sh && ./build_cgminer.sh

# Create user for mining (security best practice)
RUN useradd -m -s /bin/bash miner && \
    chown -R miner:miner /app

# Expose API port for cgminer
EXPOSE 4028

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from utils.cgminer_api import CGMinerAPI; api = CGMinerAPI(); print('OK' if api.is_connected() else exit(1))" || exit 1

# Switch to mining user
USER miner

# Set optimal environment for mining
ENV CGMINER_OPTS="--api-listen --api-allow W:127.0.0.1 --queue 2 --scan-time 15"

# Default command - can be overridden
CMD ["python3", "neurons/miner.py"] 