#!/bin/bash
#
# Cribl Stream Leader Installation Script
# This script installs and configures Cribl Stream Leader
#
# Usage: ./install_leader.sh [options]
# Options:
#   --version VERSION       Cribl Stream version (default: 3.4.1)
#   --install-dir DIR       Installation directory (default: /opt/cribl)
#   --run-user USER         User to run Cribl as (default: cribl)
#   --admin-password PASS   Admin password (default: admin)
#   --port PORT             Web UI port (default: 9000)
#   --dry-run               Simulate installation without making changes

set -e

# Default values
VERSION="3.4.1"
INSTALL_DIR="/opt/cribl"
RUN_USER="cribl"
ADMIN_PASSWORD="admin123"
PORT="9000"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --run-user)
      RUN_USER="$2"
      shift 2
      ;;
    --admin-password)
      ADMIN_PASSWORD="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Log function
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
  log "This script must be run as root"
  exit 1
fi

# Display installation parameters
log "Cribl Stream Leader Installation"
log "------------------------------------"
log "Version:          $VERSION"
log "Installation Dir: $INSTALL_DIR"
log "Run User:         $RUN_USER"
log "Web UI Port:      $PORT"
if [[ "$DRY_RUN" == true ]]; then
  log "DRY RUN MODE: No changes will be made"
fi
log "------------------------------------"

# Exit if dry run
if [[ "$DRY_RUN" == true ]]; then
  log "Dry run complete. Exiting."
  exit 0
fi

# Create run user if it doesn't exist
if ! id -u "$RUN_USER" &>/dev/null; then
  log "Creating user $RUN_USER"
  useradd -m -s /bin/bash "$RUN_USER"
fi

# Download Cribl Stream
DOWNLOAD_DIR="/tmp"
CRIBL_FILENAME="cribl-${VERSION}-linux-x64.tgz"
DOWNLOAD_URL="https://cdn.cribl.io/dl/$(echo $VERSION | cut -d. -f1).x/${CRIBL_FILENAME}"

log "Downloading Cribl Stream ${VERSION}"
if [[ ! -f "${DOWNLOAD_DIR}/${CRIBL_FILENAME}" ]]; then
  wget -q -O "${DOWNLOAD_DIR}/${CRIBL_FILENAME}" "$DOWNLOAD_URL" || {
    log "Failed to download Cribl Stream"
    exit 1
  }
else
  log "Installation file already exists, skipping download"
fi

# Extract Cribl Stream
log "Installing Cribl Stream to $INSTALL_DIR"
if [[ -d "$INSTALL_DIR" ]]; then
  log "Installation directory already exists. Removing..."
  rm -rf "$INSTALL_DIR"
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
tar -xzf "${DOWNLOAD_DIR}/${CRIBL_FILENAME}" -C "$(dirname "$INSTALL_DIR")"

# Rename directory if needed
if [[ ! -d "$INSTALL_DIR" ]]; then
  mv "$(dirname "$INSTALL_DIR")/cribl" "$INSTALL_DIR"
fi

# Set ownership
log "Setting ownership to $RUN_USER"
chown -R "$RUN_USER":"$RUN_USER" "$INSTALL_DIR"

# Configure Cribl Stream
log "Configuring Cribl Stream Leader"

# Set admin password
log "Setting admin password"
sudo -u "$RUN_USER" "$INSTALL_DIR/bin/cribl" hash-passwd "$ADMIN_PASSWORD" > "$INSTALL_DIR/local/cribl/auth/credentials.json"

# Configure as leader
log "Configuring as Leader mode"
cat > "$INSTALL_DIR/local/cribl/cribl.yml" << EOF
api:
  host: 0.0.0.0
  port: $PORT
  disabled : false
auth:
  type: local
  tokenTTL: 24h
  tokenRefresh: 12h
distributed:
  mode: master
  master:
    host: 0.0.0.0
    port: 4200
    tls:
      disabled: true
EOF

# Set proper permissions
chown "$RUN_USER":"$RUN_USER" "$INSTALL_DIR/local/cribl/cribl.yml"

# Create systemd service
log "Creating systemd service"
cat > /etc/systemd/system/cribl.service << EOF
[Unit]
Description=Cribl Stream
After=network.target

[Service]
Type=forking
User=$RUN_USER
ExecStart=$INSTALL_DIR/bin/cribl start
ExecStop=$INSTALL_DIR/bin/cribl stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable cribl.service

# Start Cribl
log "Starting Cribl Stream"
systemctl start cribl.service

log "Installation complete!"
log "Cribl Stream Leader is available at http://$(hostname -f):$PORT"
exit 0 