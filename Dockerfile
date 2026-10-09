FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port for Streamlit web server
EXPOSE 8080

# Environment defaults
ENV PORT=8080
ENV AWS_DEFAULT_REGION=us-east-1

# Launch Streamlit web app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
