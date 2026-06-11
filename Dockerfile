FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .
COPY seed_data.py .

# Streamlit config
RUN mkdir -p .streamlit
COPY secrets.toml.example .streamlit/secrets.toml

EXPOSE 8080

# Cloud Run requires PORT env variable
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
