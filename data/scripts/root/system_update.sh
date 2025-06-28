#!/bin/bash
#
# System Update Script
# This script performs system updates on Linux hosts
#
# Usage: ./system_update.sh [options]
# Options:
#   --upgrade-type TYPE    Type of upgrade: security, normal, full (default: normal)
#   --reboot               Reboot after update if needed
#   --dry-run              Simulate update without making changes

set -e

# Default values
UPGRADE_TYPE="normal"
REBOOT=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --upgrade-type)
      UPGRADE_TYPE="$2"
      shift 2
      ;;
    --reboot)
      REBOOT=true
      shift
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

# Display update parameters
log "System Update"
log "------------------------------------"
log "Upgrade Type:     $UPGRADE_TYPE"
log "Reboot if needed: $REBOOT"
if [[ "$DRY_RUN" == true ]]; then
  log "DRY RUN MODE: No changes will be made"
fi
log "------------------------------------"

# Detect OS
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$ID
  VERSION=$VERSION_ID
else
  log "Cannot detect OS, exiting"
  exit 1
fi

log "Detected OS: $OS $VERSION"

# Exit if dry run
if [[ "$DRY_RUN" == true ]]; then
  log "Dry run complete. Exiting."
  exit 0
fi

# Update package lists
log "Updating package lists"
case $OS in
  ubuntu|debian)
    apt-get update -y
    ;;
  centos|rhel|fedora)
    yum check-update || true
    ;;
  *)
    log "Unsupported OS: $OS"
    exit 1
    ;;
esac

# Perform upgrades based on type
case $UPGRADE_TYPE in
  security)
    log "Performing security updates only"
    case $OS in
      ubuntu|debian)
        unattended-upgrades --verbose -d
        ;;
      centos|rhel|fedora)
        yum -y update --security
        ;;
    esac
    ;;
    
  normal)
    log "Performing normal system update"
    case $OS in
      ubuntu|debian)
        apt-get upgrade -y
        ;;
      centos|rhel|fedora)
        yum -y update
        ;;
    esac
    ;;
    
  full)
    log "Performing full system upgrade"
    case $OS in
      ubuntu|debian)
        apt-get dist-upgrade -y
        ;;
      centos|rhel|fedora)
        yum -y upgrade
        ;;
    esac
    ;;
    
  *)
    log "Unknown upgrade type: $UPGRADE_TYPE"
    exit 1
    ;;
esac

# Check if reboot is needed
REBOOT_REQUIRED=false
if [ -f /var/run/reboot-required ]; then
  REBOOT_REQUIRED=true
  log "Reboot is required"
elif [ -f /usr/bin/needs-restarting ] && /usr/bin/needs-restarting -r > /dev/null; then
  REBOOT_REQUIRED=true
  log "Reboot is required"
else
  log "No reboot required"
fi

# Reboot if needed and requested
if [[ "$REBOOT_REQUIRED" == true && "$REBOOT" == true ]]; then
  log "Rebooting system in 1 minute..."
  shutdown -r +1 "System update completed, rebooting..."
fi

log "System update completed successfully"
exit 0 