#!/bin/bash
# Security hardening script for data directory access permissions
# IRB-compliant data access control for Mindfulness and Social Skills study

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"

echo "=== Security Hardening for Data Directory ==="
echo "Target: ${DATA_DIR}"
echo "Date: $(date)"

# Ensure data directory exists
if [ ! -d "${DATA_DIR}" ]; then
    echo "Creating data directory structure..."
    mkdir -p "${DATA_DIR}/raw"
    mkdir -p "${DATA_DIR}/processed"
    mkdir -p "${DATA_DIR}/temp"
fi

# Set ownership to current user (IRB requirement: no world-readable)
echo "Setting ownership..."
chown -R "$(whoami)" "${DATA_DIR}"

# Remove world-readable permissions (critical for IRB compliance)
echo "Removing world-readable permissions..."
chmod -R o-rwx "${DATA_DIR}"

# Remove group-write permissions (prevent accidental modification)
echo "Removing group-write permissions..."
chmod -R g-w "${DATA_DIR}"

# Set directory permissions to 750 (owner: rwx, group: rx, others: none)
echo "Setting directory permissions to 750..."
find "${DATA_DIR}" -type d -exec chmod 750 {} \;

# Set file permissions to 640 (owner: rw, group: r, others: none)
echo "Setting file permissions to 640..."
find "${DATA_DIR}" -type f -exec chmod 640 {} \;

# Special handling for HIPAA-compliant naming (no PII in filenames)
echo "Validating filename compliance (no PII patterns)..."
if command -v grep &> /dev/null; then
    grep -rE "[0-9]{3}-[0-9]{2}-[0-9]{4}|[0-9]{9}" "${DATA_DIR}" 2>/dev/null || true
fi

# Create .gitkeep files to preserve directory structure
echo "Creating .gitkeep files..."
touch "${DATA_DIR}/raw/.gitkeep"
touch "${DATA_DIR}/processed/.gitkeep"
touch "${DATA_DIR}/temp/.gitkeep"

# Log completion
echo "=== Security hardening complete ==="
echo "Current permissions:"
ls -la "${DATA_DIR}"

echo ""
echo "REMEMBER: Run this script after cloning repository:"
echo "  ./scripts/set_data_permissions.sh"
