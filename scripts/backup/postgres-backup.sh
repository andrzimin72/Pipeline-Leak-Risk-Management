#!/bin/bash
# ==============================================================================
# PostgreSQL Backup Script with WAL Archiving
# Runs hourly via CronJob in Kubernetes
# ==============================================================================

set -euo pipefail

BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30
S3_BUCKET="s3://pipeline-ai-backups/postgres"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "[$(date)] Starting PostgreSQL backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Full backup using pgBackRest
pgbackrest --stanza=pipeline-ai --type=full backup

# Verify backup integrity
pgbackrest --stanza=pipeline-ai verify

# Upload to S3 with encryption
aws s3 sync "${BACKUP_DIR}" "${S3_BUCKET}/${TIMESTAMP}/" \
  --sse aws:kms \
  --storage-class STANDARD_IA

# Cleanup old local backups
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -delete

# Cleanup old S3 backups
aws s3 ls "${S3_BUCKET}/" | \
  awk '{print $4}' | \
  grep -E '^[0-9]{8}-[0-9]{6}/$' | \
  sort -r | \
  tail -n +$((RETENTION_DAYS * 24 + 1)) | \
  xargs -I {} aws s3 rm "${S3_BUCKET}/{}" --recursive

echo "[$(date)] Backup completed successfully"
echo "  Location: ${S3_BUCKET}/${TIMESTAMP}/"
echo "  Size: $(du -sh "${BACKUP_DIR}" | cut -f1)"