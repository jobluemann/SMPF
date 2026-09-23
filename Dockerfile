FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY app/ ./app/
COPY frontend/ ./frontend/

# Create data directory (will be mounted as persistent volume)
RUN mkdir -p /data

# Run the app (Render sets $PORT dynamically)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
