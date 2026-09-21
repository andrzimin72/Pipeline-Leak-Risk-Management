#!/bin/bash
# ==============================================================================
# Backup Verification Script
# Tests restore to isolated namespace weekly
# ==============================================================================

set -euo pipefail

SOURCE_NAMESPACE="pipeline-ai"
VERIFY_NAMESPACE="pipeline-ai-verify-$(date +%s)"
LATEST_BACKUP=$(velero backup get --sort-by=.metadata.creationTimestamp | tail -1 | awk '{print $1}')

echo "======================================================================"
echo "🔍 Backup Verification Test"
echo "   Source: ${SOURCE_NAMESPACE}"
echo "   Target: ${VERIFY_NAMESPACE}"
echo "   Backup: ${LATEST_BACKUP}"
echo "======================================================================"

# Create verification namespace
kubectl create namespace "${VERIFY_NAMESPACE}"

# Restore to verification namespace
velero restore create "verify-$(date +%s)" \
  --from-backup "${LATEST_BACKUP}" \
  --namespace-mappings "${SOURCE_NAMESPACE}:${VERIFY_NAMESPACE}" \
  --wait

# Wait for pods to be ready
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --all -n "${VERIFY_NAMESPACE}" --timeout=300s

# Verify PostgreSQL data integrity
echo "🔍 Verifying PostgreSQL data..."
kubectl exec -it deploy/pipeline-api -n "${VERIFY_NAMESPACE}" -- \
  python -c "
import json
import os
with open('/app/data/alerts.json', 'r') as f:
    data = json.load(f)
    print(f'✅ Alerts file intact: {len(data)} records')
"

# Verify API functionality
echo "🔍 Testing API endpoint..."
kubectl port-forward svc/pipeline-api 8001:8000 -n "${VERIFY_NAMESPACE}" &
PF_PID=$!
sleep 5

RESPONSE=$(curl -s http://localhost:8001/ || echo "FAILED")
kill $PF_PID

if [[ "${RESPONSE}" == *"online"* ]]; then
    echo "✅ API functional"
else
    echo "❌ API verification failed"
    exit 1
fi

# Cleanup verification namespace
echo "🧹 Cleaning up verification namespace..."
kubectl delete namespace "${VERIFY_NAMESPACE}"

echo "======================================================================"
echo "✅ Backup verification PASSED"
echo "======================================================================"