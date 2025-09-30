#!/bin/bash
# Test screenshot functionality with Xvfb

cd /workspace/Herobine/bridge

# Kill any existing bridge
pkill -9 -f "node.*mineflayer"
sleep 2

# Test with a short run
echo "Starting server with Xvfb enabled..."
echo "Look for '[Viewer] ✓ Screenshot support ready'"
echo "Screenshots should NOT be black anymore"
echo ""

timeout 30 python server_mineflayer.py \
    --mc-host 2.tcp.us-cal-1.ngrok.io \
    --mc-port 19335 \
    --vllm-url http://localhost:8000/v1 \
    --checkpoint CraftJarvis/JarvisVLA-Qwen2-VL-7B \
    --instruction "Look around" \
    --max-steps 15 \
    --verbos 2>&1 | tee xvfb_test.log

echo ""
echo "=== Checking latest screenshots ==="
ls -lh agent_logs/step_000*.jpg | tail -5
echo ""
echo "=== Check if images are real (not black) ==="
python3 << 'EOF'
from PIL import Image
import glob

# Check last few screenshots
files = sorted(glob.glob('agent_logs/step_*.jpg'))[-3:]
for f in files:
    img = Image.open(f)
    pixels = list(img.getdata())
    # Check if all pixels are black
    all_black = all(p == (0, 0, 0) for p in pixels)
    print(f"{f}: {'BLACK (failed)' if all_black else 'HAS CONTENT (success!)'}")
EOF


