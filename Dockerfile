FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create .env file for demo (Railway deployment)
RUN cp env_example.txt .env

# Set environment variables for Railway
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV DATAPLANE_HOST=localhost
ENV DATAPLANE_PORT=5555

# Expose port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"] 