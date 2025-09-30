#!/bin/bash
# VirtualGL entrypoint script for GPU-accelerated rendering

# Start X server on display :1 in the background
Xvfb :1 -screen 0 1024x768x24 &
XVFB_PID=$!

# Wait for X server to be ready
sleep 2

# Start VirtualGL fake X server
export DISPLAY=:1
/opt/VirtualGL/bin/vglserver_config -config +t

echo "VirtualGL server started successfully"
echo "XVFB_PID: $XVFB_PID"
echo "DISPLAY: $DISPLAY"

# Keep the script running
wait $XVFB_PID

