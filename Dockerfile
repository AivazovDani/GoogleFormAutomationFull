FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Chrome dependencies
    wget \
    gnupg \
    unzip \
    curl \
    # Virtual display
    xvfb \
    x11vnc \
    # noVNC dependencies
    novnc \
    websockify \
    # misc
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Copy supervisor config (manages starting all services)
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
# 5015 = Flask app
# 6080 = noVNC web interface
EXPOSE 5015 6080

# Start everything via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
