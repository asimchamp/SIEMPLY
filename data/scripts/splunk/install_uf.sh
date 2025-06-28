#!/bin/bash
#
# Splunk Universal Forwarder Installation Script
# This script installs and configures Splunk Universal Forwarder
#
# Usage: ./install_uf.sh [options]
# Options:
#   --version VERSION       Splunk UF version (default: 9.4.3)
#   --install-dir DIR       Installation directory (default: /opt/splunkforwarder)
#   --run-user USER         User to run Splunk as (default: splunk)
#   --deployment-server DS  Deployment server (optional)
#   --deployment-app APP    Deployment app (optional)
#   --dry-run               Simulate installation without making changes

set -e

# Default values
VERSION="9.4.3"
INSTALL_DIR="/opt/splunkforwarder"
RUN_USER="splunk"
DEPLOYMENT_SERVER=""
DEPLOYMENT_APP=""
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
    --deployment-server)
      DEPLOYMENT_SERVER="$2"
      shift 2
      ;;
    --deployment-app)
      DEPLOYMENT_APP="$2"
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
log "Splunk Universal Forwarder Installation"
log "------------------------------------"
log "Version:          $VERSION"
log "Installation Dir: $INSTALL_DIR"
log "Run User:         $RUN_USER"
if [[ -n "$DEPLOYMENT_SERVER" ]]; then
  log "Deployment Server: $DEPLOYMENT_SERVER"
fi
if [[ -n "$DEPLOYMENT_APP" ]]; then
  log "Deployment App:    $DEPLOYMENT_APP"
fi
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

# Download Splunk UF
DOWNLOAD_DIR="/tmp"
SPLUNK_FILENAME="splunkforwarder-${VERSION}-Linux-x86_64.tgz"
DOWNLOAD_URL="https://download.splunk.com/products/universalforwarder/releases/${VERSION}/linux/${SPLUNK_FILENAME}"

log "Downloading Splunk Universal Forwarder ${VERSION}"
if [[ ! -f "${DOWNLOAD_DIR}/${SPLUNK_FILENAME}" ]]; then
  wget -q -O "${DOWNLOAD_DIR}/${SPLUNK_FILENAME}" "$DOWNLOAD_URL" || {
    log "Failed to download Splunk UF"
    exit 1
  }
else
  log "Installation file already exists, skipping download"
fi

# Extract Splunk UF
log "Installing Splunk Universal Forwarder to $INSTALL_DIR"
if [[ -d "$INSTALL_DIR" ]]; then
  log "Installation directory already exists. Removing..."
  rm -rf "$INSTALL_DIR"
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
tar -xzf "${DOWNLOAD_DIR}/${SPLUNK_FILENAME}" -C "$(dirname "$INSTALL_DIR")"

# Set ownership
log "Setting ownership to $RUN_USER"
chown -R "$RUN_USER":"$RUN_USER" "$INSTALL_DIR"

# Configure Splunk UF
log "Configuring Splunk Universal Forwarder"

# Create user-seed.conf for first-time run
mkdir -p "$INSTALL_DIR/etc/system/local"
cat > "$INSTALL_DIR/etc/system/local/user-seed.conf" << EOF
[user_info]
USERNAME = admin
PASSWORD = changeme
EOF

# Configure deployment client if specified
if [[ -n "$DEPLOYMENT_SERVER" ]]; then
  log "Configuring deployment client for server: $DEPLOYMENT_SERVER"
  mkdir -p "$INSTALL_DIR/etc/system/local"
  cat > "$INSTALL_DIR/etc/system/local/deploymentclient.conf" << EOF
[deployment-client]
phoneHomeIntervalInSecs = 60

[target-broker:deploymentServer]
targetUri = $DEPLOYMENT_SERVER
EOF
fi

# Accept license and start Splunk
log "Accepting license and starting Splunk"
sudo -u "$RUN_USER" "$INSTALL_DIR/bin/splunk" start --accept-license --no-prompt --answer-yes

# Enable boot-start
log "Enabling boot-start with user $RUN_USER"
"$INSTALL_DIR/bin/splunk" enable boot-start -user "$RUN_USER" --accept-license --no-prompt --answer-yes

log "Installation complete!"
exit 0 