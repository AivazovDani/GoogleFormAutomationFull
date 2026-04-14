#!/bin/bash

# Start Xvfb first and wait for it to be ready
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# Wait until Xvfb is actually ready
echo "Waiting for Xvfb to start..."
for i in $(seq 1 10); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "Xvfb is ready!"
        break
    fi
    sleep 1
done

export DISPLAY=:99

# Start x11vnc
x11vnc -display :99 -nopw -listen localhost -xkb -forever &

# Start noVNC
websockify --web /usr/share/novnc 6080 localhost:5900 &

# Start Flask app
echo "Starting Flask..."
python app.py
