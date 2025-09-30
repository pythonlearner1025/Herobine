#!/bin/bash
# Start ngrok tunnel for JarvisVLA vLLM server
# For static domains, get one at: https://dashboard.ngrok.com/domains
# Then set the NGROK_DOMAIN environment variable

set -e

PORT=${PORT:-8000}

echo "🌐 Starting ngrok tunnel for port $PORT..."
echo ""

if [ -n "$NGROK_DOMAIN" ]; then
    echo "📍 Using static domain: $NGROK_DOMAIN"
    echo ""
    ngrok http --url="$NGROK_DOMAIN" "$PORT"
else
    echo "📍 Using dynamic URL (changes on restart)"
    echo "   To use a static domain, set: export NGROK_DOMAIN=your-domain.ngrok-free.dev"
    echo ""
    ngrok http "$PORT"
fi