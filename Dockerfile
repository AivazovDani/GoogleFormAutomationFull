FROM selenium/standalone-chrome:latest

USER root

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy all project files
COPY . .

# Expose ports
# 5015 = Flask app
# 7900 = noVNC (built into selenium/standalone-chrome)
EXPOSE 5015 7900

# Start Flask app (Xvfb and VNC are handled automatically by the base image)
CMD ["python3", "app.py"]
