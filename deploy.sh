#!/bin/bash
# deploy.sh — one-command deploy to Cloud Run
# Usage: bash deploy.sh

set -e

PROJECT_ID="worldcup-fantasy-agent"
REGION="us-central1"
SERVICE="worldcup-fantasy-agent"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE"

echo "🚀 Deploying WorldCup Fantasy Agent to Cloud Run..."
echo "Project: $PROJECT_ID | Region: $REGION"

# 1. Build image
echo "📦 Building Docker image..."
gcloud builds submit --tag $IMAGE --project $PROJECT_ID

# 2. Deploy to Cloud Run with secrets from Secret Manager
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars GCP_PROJECT=$PROJECT_ID,GCP_LOCATION=$REGION \
  --project $PROJECT_ID

echo ""
echo "✅ Deployed! Your app URL:"
gcloud run services describe $SERVICE \
  --region $REGION \
  --project $PROJECT_ID \
  --format "value(status.url)"
