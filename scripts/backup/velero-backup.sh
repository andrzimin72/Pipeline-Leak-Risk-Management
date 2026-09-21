#!/bin/bash
# ==============================================================================
# Velero Kubernetes Cluster Backup
# Runs every 6 hours via CronJob
# ==============================================================================

set -euo pipefail

NAMESPACE="pipeline-ai"
BACKUP_NAME="pipeline-ai-$(date +%Y%m%d-%H%M%S)"
RETENTION_DAYS=90

echo "[$(date)] Starting Velero backup: ${BACKUP_NAME}"

# Create backup with volume snapshots
velero backup create "${BACKUP_NAME}" \
  --include-namespaces "${NAMESPACE}" \
  --snapshot-volumes \
  --volume-snapshot-locations nebius \
  --ttl ${RETENTION_DAYS}d \
  --wait

# Verify backup
velero backup describe "${BACKUP_NAME}"

# Check backup status
STATUS=$(velero backup get "${BACKUP_NAME}" -o json | jq -r '.status.phase')

if [[ "${STATUS}" != "Completed" ]]; then
    echo "❌ Backup failed with status: ${STATUS}"
    exit 1
fi

echo "✅ Backup completed: ${BACKUP_NAME}"
echo "   Size: $(velero backup describe ${BACKUP_NAME} -o json | jq -r '.status.progress')"