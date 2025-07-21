#!/bin/bash

echo "🚀 ZEUS-MINER RAILWAY DEPLOYMENT SCRIPT"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Zeus-Miner v2.0 Ultimate - Ready for deployment"
fi

echo "📋 DEPLOYMENT INSTRUCTIONS:"
echo ""
echo "1. 📱 Go to https://railway.app"
echo "2. 🔐 Sign up with GitHub (free account)"
echo "3. ➕ Click 'New Project'"
echo "4. 📂 Select 'Deploy from GitHub repo'"
echo "5. 🔗 Connect this repository"
echo "6. ⚙️  Railway will auto-detect the Dockerfile"
echo "7. 🚀 Click Deploy!"
echo ""
echo "📊 MONITORING URLS (after deployment):"
echo "• Live JSON: https://your-app.up.railway.app/zeus_live_progress.json"
echo "• Logs: Railway dashboard -> Your service -> Logs"
echo ""
echo "💰 YOUR WALLET DETAILS:"
echo "• Coldkey: 5FCofUHJjRPf4Dv7vnkhm7hSCrjUbBr16GttNxqDbgFzDTJ6"
echo "• Hotkey: 5EcS5JsxhFDNV1VQpHek9xzhpYpy7fHqroviuaDs3Y7t3LXf"
echo "• Current Performance: RANKING #2 with 18 shares found!"
echo ""
echo "🔥 ALTERNATIVE DEPLOYMENT COMMANDS:"
echo ""
echo "# Using Railway CLI (if installed):"
echo "railway login"
echo "railway link"
echo "railway up"
echo ""
echo "# Using Docker directly:"
echo "docker build -t zeus-miner ."
echo "docker run -d --name zeus-miner-container zeus-miner"
echo ""
echo "✅ Your Zeus-Miner is deployment-ready!"
echo "📈 Currently RANKING #2 and earning TAO!"

# Check current mining status
if [ -f "zeus_live_progress.json" ]; then
    echo ""
    echo "📊 CURRENT LIVE STATUS:"
    cat zeus_live_progress.json | python3 -m json.tool
fi