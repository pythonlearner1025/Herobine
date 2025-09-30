#!/bin/bash
# Quick verification script to check if installation was successful

echo "🔍 Verifying JarvisVLA Installation..."
echo ""

ERRORS=0

# Check Java
echo -n "Checking Java... "
if java -version 2>&1 | grep -q "1.8"; then
    echo "✅ OK ($(java -version 2>&1 | head -n 1))"
else
    echo "❌ FAILED"
    ((ERRORS++))
fi

# Check vLLM
echo -n "Checking vLLM... "
if python -c "import vllm" 2>/dev/null; then
    VERSION=$(python -c "import vllm; print(vllm.__version__)" 2>/dev/null)
    echo "✅ OK (version $VERSION)"
else
    echo "❌ FAILED - vLLM cannot be imported"
    ((ERRORS++))
fi

# Check transformers
echo -n "Checking transformers... "
if python -c "import transformers" 2>/dev/null; then
    VERSION=$(python -c "import transformers; print(transformers.__version__)" 2>/dev/null)
    echo "✅ OK (version $VERSION)"
else
    echo "❌ FAILED"
    ((ERRORS++))
fi

# Check PyTorch
echo -n "Checking PyTorch... "
if python -c "import torch" 2>/dev/null; then
    VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null)
    CUDA=$(python -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null)
    echo "✅ OK (version $VERSION, $CUDA available)"
else
    echo "❌ FAILED"
    ((ERRORS++))
fi

# Check qwen-vl-utils
echo -n "Checking qwen-vl-utils... "
if python -c "import qwen_vl_utils" 2>/dev/null; then
    echo "✅ OK"
else
    echo "⚠️  WARNING - Not critical for serving"
fi

# Check JarvisVLA (optional)
echo -n "Checking JarvisVLA package... "
if python -c "import jarvisvla" 2>/dev/null; then
    echo "✅ OK"
else
    echo "⚠️  WARNING - vLLM can still serve the model"
fi

# Check ngrok
echo -n "Checking ngrok... "
if command -v ngrok &> /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
    ((ERRORS++))
fi

# Check scripts
echo -n "Checking start_vllm_server.sh... "
if [ -x "start_vllm_server.sh" ]; then
    echo "✅ OK"
else
    echo "❌ FAILED - Not executable"
    ((ERRORS++))
fi

echo -n "Checking start_ngrok_tunnel.sh... "
if [ -x "start_ngrok_tunnel.sh" ]; then
    echo "✅ OK"
else
    echo "❌ FAILED - Not executable"
    ((ERRORS++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ]; then
    echo "🎉 All critical checks passed!"
    echo ""
    echo "✅ Ready to serve JarvisVLA"
    echo ""
    echo "Next steps:"
    echo "  1. Start server: ./start_vllm_server.sh"
    echo "  2. In new terminal: ./start_ngrok_tunnel.sh"
    exit 0
else
    echo "❌ $ERRORS critical check(s) failed"
    echo ""
    echo "Please review the errors above and re-run install.sh"
    exit 1
fi


