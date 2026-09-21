#!/bin/bash
# ==============================================================================
# Helm Deployment Script for Pipeline AI Platform
# ==============================================================================

set -euo pipefail

ENVIRONMENT=${1:-dev}
CHART_PATH="./helm/pipeline-ai-platform"
RELEASE_NAME="pipeline-ai"
NAMESPACE="pipeline-ai"

echo "======================================================================"
echo "🚀 Deploying Pipeline AI Platform"
echo "   Environment: ${ENVIRONMENT}"
echo "   Release: ${RELEASE_NAME}"
echo "   Namespace: ${NAMESPACE}"
echo "======================================================================"

# Validate environment
if [[ ! "${ENVIRONMENT}" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ Invalid environment: ${ENVIRONMENT}. Must be dev, staging, or prod."
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Build dependencies
echo ""
echo "📦 Building Helm dependencies..."
helm dependency build "${CHART_PATH}"

# Template validation (dry-run)
echo ""
echo "🔍 Validating templates..."
helm template "${RELEASE_NAME}" "${CHART_PATH}" \
    --namespace "${NAMESPACE}" \
    --values "${CHART_PATH}/values-${ENVIRONMENT}.yaml" > /dev/null

# Deploy
echo ""
echo "🚀 Deploying to Kubernetes..."
if [[ "${ENVIRONMENT}" == "prod" ]]; then
    echo "⚠️  PRODUCTION DEPLOYMENT - Confirm to proceed"
    read -p "   Type 'deploy' to confirm: " confirm
    if [[ "${confirm}" != "deploy" ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
    
    helm upgrade --install "${RELEASE_NAME}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --values "${CHART_PATH}/values-${ENVIRONMENT}.yaml" \
        --atomic \
        --timeout 10m \
        --wait \
        --set global.secrets.nebiusApiKey="${NEBIUS_API_KEY}" \
        --set global.secrets.sapAuthToken="${SAP_AUTH_TOKEN}"
else
    helm upgrade --install "${RELEASE_NAME}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --values "${CHART_PATH}/values-${ENVIRONMENT}.yaml" \
        --timeout 5m \
        --wait
fi

echo ""
echo "======================================================================"
echo "✅ Deployment complete!"
echo "======================================================================"
echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n ${NAMESPACE}"
echo "   kubectl get ingress -n ${NAMESPACE}"
echo ""
echo "🌐 Access URLs:"
echo "   API:       https://api.pipeline.${ENVIRONMENT}.exxonmobil.nebius.cloud"
echo "   Dashboard: https://dashboard.pipeline.${ENVIRONMENT}.exxonmobil.nebius.cloud"
echo "   Grafana:   https://grafana.pipeline.${ENVIRONMENT}.exxonmobil.nebius.cloud"
echo ""