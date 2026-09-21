#!/bin/bash
# ==============================================================================
# Helm Rollback Script
# ==============================================================================

set -euo pipefail

RELEASE_NAME="pipeline-ai"
NAMESPACE="pipeline-ai"
REVISION=${1:-}

echo "======================================================================"
echo "🔄 Rolling back Pipeline AI Platform"
echo "======================================================================"

# List available revisions
echo ""
echo "📋 Available revisions:"
helm history "${RELEASE_NAME}" -n "${NAMESPACE}"

if [[ -z "${REVISION}" ]]; then
    echo ""
    read -p "Enter revision number to rollback to: " REVISION
fi

echo ""
echo "⚠️  Rolling back to revision ${REVISION}..."
read -p "   Confirm? (yes/no): " confirm

if [[ "${confirm}" != "yes" ]]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

helm rollback "${RELEASE_NAME}" "${REVISION}" -n "${NAMESPACE}" --wait

echo ""
echo "✅ Rollback complete!"
echo ""
helm history "${RELEASE_NAME}" -n "${NAMESPACE}"