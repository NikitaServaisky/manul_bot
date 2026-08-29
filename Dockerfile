# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python path so it can import from src/ and root
ENV PYTHONPATH=/app

# Install system dependencies (including sqlite3 for debugging)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Command to run the bot using python module mode
CMD ["python", "-m", "src.main"]