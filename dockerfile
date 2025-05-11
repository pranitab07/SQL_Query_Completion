# Base image
FROM python:3.11-slim
LABEL maintainer="querypilot"
LABEL version="1.0"
# Set working directory
WORKDIR /app

# System dependencies (pyautogui, clipboard, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    x11-utils \
    xclip \
    && rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Pre-warm sentence-transformers model (optional)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Set env var to reduce buffering (nice for real-time logging)
ENV PYTHONUNBUFFERED=1

# Default run command (can be overridden in docker-compose)
CMD ["python", "src/sql_mcp.py"]