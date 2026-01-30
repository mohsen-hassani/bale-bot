# Use Python 3.14 slim image for smaller size
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create directory for persistent session file
RUN mkdir -p /app/sessions

# Set environment variables (override these when running the container)
ENV PYTHONUNBUFFERED=1

# Volume for persistent Telegram session
VOLUME ["/app/sessions"]

# Run the bot
CMD ["python", "src/main.py"]
