#!/bin/bash
# ==============================================================================
# ExxonMobil Physical AI Platform - Automated Backup Script
# ==============================================================================

set -euo pipefail

# Configuration
BACKUP_DIR="./backups"
DATA_DIR="./data"
MODEL_DIR="./cloud/deployment/jetson_artifacts"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="pipeline-ai-backup-${TIMESTAMP}.tar.gz"
RETENTION_DAYS=30

echo "======================================================================"
echo "🔄 Starting Backup Process: ${TIMESTAMP}"
echo "======================================================================"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# 1. Backup Application Data (JSON logs, risk assessments)
echo "📦 Archiving application data..."
if [ -d "${DATA_DIR}" ]; then
    tar -czf "${BACKUP_DIR}/data-${TIMESTAMP}.tar.gz" -C . "${DATA_DIR}"
    echo "   ✅ Data archived."
else
    echo "   ️  Data directory not found. Skipping."
fi

# 2. Backup Model Artifacts (TensorRT engines, PyTorch weights)
echo "🧠 Archiving model artifacts..."
if [ -d "${MODEL_DIR}" ]; then
    tar -czf "${BACKUP_DIR}/models-${TIMESTAMP}.tar.gz" -C . "${MODEL_DIR}"
    echo "   ✅ Models archived."
else
    echo "   ⚠️  Model directory not found. Skipping."
fi

# 3. Backup PostgreSQL Database (If running locally)
echo "🗄️  Backing up PostgreSQL database..."
if command -v pg_dump &> /dev/null; then
    # Load .env variables if available
    if [ -f .env ]; then
        source .env
    fi
    
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-pipeline_ai}" -f "${BACKUP_DIR}/db-${TIMESTAMP}.sql"
    echo "   ✅ Database dumped."
else
    echo "   ️  pg_dump not found. Skipping database backup."
fi

# 4. Cleanup Old Backups
echo "🧹 Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -exec rm -f {} \;
echo "   ✅ Cleanup complete."

echo "======================================================================"
echo "✅ Backup Complete: ${BACKUP_DIR}/${BACKUP_NAME}"
echo "======================================================================"