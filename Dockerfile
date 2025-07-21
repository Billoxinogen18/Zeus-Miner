FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir bittensor

# Copy the entire Zeus-Miner codebase
COPY . .

# Create wallet directory
RUN mkdir -p /root/.bittensor/wallets/zeus_miner/hotkeys

# Copy wallet files if they exist
COPY zeus_wallet_REAL.json /app/

# Make scripts executable
RUN chmod +x zeus_live_performance_monitor.py

# Expose ports for miner API and web dashboard
EXPOSE 8080 8091

# Set environment variables
ENV PYTHONPATH=/app
ENV BITTENSOR_WALLET_NAME=zeus_miner
ENV BITTENSOR_HOTKEY=default
ENV NETUID=17

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import json; data=json.load(open('zeus_live_progress.json')); exit(0 if data['connection_status'] == 'Connected - Mining Active' else 1)" || exit 1

# Start the Zeus-Miner with live monitoring and web dashboard
CMD ["sh", "-c", "python3 zeus_live_performance_monitor.py & python3 web_monitor.py & python3 -m neurons.miner --logging.info --netuid 17 --wallet.name zeus_miner --wallet.hotkey default; wait"] 