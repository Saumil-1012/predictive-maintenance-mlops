FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model files and API
COPY model/ ./model/
COPY ml/api.py ./ml/api.py

# Expose port
EXPOSE 8000

# Start the API
CMD ["uvicorn", "ml.api:app", "--host", "0.0.0.0", "--port", "8000"]