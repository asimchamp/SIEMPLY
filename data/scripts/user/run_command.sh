#!/bin/bash
#
# Custom Command Runner Script
# This script executes custom commands or scripts provided by the user
#
# Usage: ./run_command.sh [options]
# Options:
#   --run-user USER         User to run command as (default: root)
#   --command CMD           Command to execute
#   --script-file FILE      Script file to execute
#   --dry-run               Simulate execution without running anything

set -e

# Default values
RUN_USER="root"
COMMAND=""
SCRIPT_FILE=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --run-user)
      RUN_USER="$2"
      shift 2
      ;;
    --command)
      COMMAND="$2"
      shift 2
      ;;
    --script-file)
      SCRIPT_FILE="$2"
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

# Check if command or script file is provided
if [[ -z "$COMMAND" && -z "$SCRIPT_FILE" ]]; then
  log "Error: Either --command or --script-file must be provided"
  exit 1
fi

# Display execution parameters
log "Custom Command Execution"
log "------------------------------------"
log "Run User:         $RUN_USER"
if [[ -n "$COMMAND" ]]; then
  log "Command:          $COMMAND"
fi
if [[ -n "$SCRIPT_FILE" ]]; then
  log "Script File:      $SCRIPT_FILE"
fi
if [[ "$DRY_RUN" == true ]]; then
  log "DRY RUN MODE: No commands will be executed"
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

# Execute command or script
if [[ -n "$COMMAND" ]]; then
  log "Executing command as user $RUN_USER"
  
  # Execute command as specified user
  if [[ "$RUN_USER" == "root" ]]; then
    log "Running: $COMMAND"
    eval "$COMMAND"
  else
    log "Running as $RUN_USER: $COMMAND"
    su - "$RUN_USER" -c "$COMMAND"
  fi
  
  log "Command execution completed"
elif [[ -n "$SCRIPT_FILE" ]]; then
  log "Executing script as user $RUN_USER"
  
  # Create a temporary script file
  TEMP_SCRIPT=$(mktemp)
  echo "$SCRIPT_FILE" > "$TEMP_SCRIPT"
  chmod +x "$TEMP_SCRIPT"
  
  # Execute script as specified user
  if [[ "$RUN_USER" == "root" ]]; then
    log "Running script"
    bash "$TEMP_SCRIPT"
  else
    log "Running script as $RUN_USER"
    chown "$RUN_USER":"$RUN_USER" "$TEMP_SCRIPT"
    su - "$RUN_USER" -c "$TEMP_SCRIPT"
  fi
  
  # Clean up
  rm -f "$TEMP_SCRIPT"
  log "Script execution completed"
fi

log "Execution completed successfully"
exit 0 