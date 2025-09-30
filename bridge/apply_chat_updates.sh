#!/bin/bash
# Apply Chat-Based Interaction Updates
# This script updates the necessary files for chat-based JarvisAI interaction

set -e

echo "========================================="
echo "Applying Chat-Based Interaction Updates"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "server_mineflayer.py" ]; then
    echo "Error: Must run from /workspace/Herobine/bridge directory"
    exit 1
fi

echo "Step 1: Installing prismarine-viewer for POV screenshots..."
if npm list prismarine-viewer &>/dev/null; then
    echo "  ✓ prismarine-viewer already installed"
else
    npm install prismarine-viewer
    echo "  ✓ Installed prismarine-viewer"
fi

echo ""
echo "Step 2: Installing Python dependencies..."
pip install -q Pillow requests numpy
echo "  ✓ Python dependencies ready"

echo ""
echo "Step 3: Backing up original files..."
cp mineflayer_bridge.js mineflayer_bridge.js.backup
cp mineflayer_env.py mineflayer_env.py.backup
cp server_mineflayer.py server_mineflayer.py.backup
echo "  ✓ Backups created (.backup files)"

echo ""
echo "Step 4: File updates needed..."
echo ""
echo "The following updates need to be applied manually:"
echo ""
echo "1. mineflayer_bridge.js:"
echo "   - Add chat listener (bot.on('chat', ...))"
echo "   - Add viewer initialization (initViewer, captureScreenshot)"
echo "   - Add new endpoints (/chat/instructions, /screenshot)"
echo ""
echo "2. mineflayer_env.py:"
echo "   - Add get_pov_image() method"
echo "   - Add get_chat_instructions() method"
echo "   - Add start_chat_instruction() method"
echo "   - Add clear_chat_instruction() method"
echo ""
echo "3. server_mineflayer.py:"
echo "   - Replace run() method with chat-aware version"
echo ""
echo "See CHAT_INTERACTION_GUIDE.md for complete code snippets!"
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Read CHAT_INTERACTION_GUIDE.md for detailed instructions"
echo "2. Apply the code changes listed above"
echo "3. Start VLLM server on GPU machine"
echo "4. Run: python server_mineflayer.py --vllm-url <url> --checkpoint <path>"
echo ""



