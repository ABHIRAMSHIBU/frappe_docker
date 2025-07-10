#!/bin/bash

# Docker Volume Backup and Restore Script
# Usage: ./docker_volume_backup.sh [backup|restore|list]

set -e  # Exit on any error

# Configuration
BACKUP_BASE_DIR="./docker_backups"
COMPOSE_FILE="pwd.yml"

# Named volumes to backup (adjust these based on your setup)
VOLUMES=(
    "frappe_docker_logs"
    "frappe_docker_sites"
    "frappe_docker_db-data"
    "frappe_docker_redis-queue-data"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running or not accessible. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if volume exists
volume_exists() {
    local volume_name="$1"
    if docker volume inspect "$volume_name" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to create backup
backup_volumes() {
    check_docker
    
    # Create timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="$BACKUP_BASE_DIR/$timestamp"
    
    log_info "Creating backup directory: $backup_dir"
    mkdir -p "$backup_dir"
    
    # Create a metadata file
    cat > "$backup_dir/backup_info.txt" << EOF
Backup Created: $(date)
Docker Compose File: $COMPOSE_FILE
Volumes Backed Up: ${VOLUMES[@]}
Host: $(hostname)
User: $(whoami)
EOF
    
    log_info "Starting backup process..."
    
    for volume in "${VOLUMES[@]}"; do
        if volume_exists "$volume"; then
            log_info "Backing up volume: $volume"
            
            # Create backup using busybox
            docker run --rm \
                -v "$volume":/volume \
                -v "$(pwd)/$backup_dir":/backup \
                busybox tar czf "/backup/${volume}.tar.gz" -C /volume .
            
            # Check if backup was successful
            if [[ -f "$backup_dir/${volume}.tar.gz" ]]; then
                local size=$(du -h "$backup_dir/${volume}.tar.gz" | cut -f1)
                log_success "✓ $volume backed up successfully ($size)"
            else
                log_error "✗ Failed to backup $volume"
                exit 1
            fi
        else
            log_warning "Volume '$volume' does not exist, skipping..."
        fi
    done
    
    # Create a summary
    local total_size=$(du -sh "$backup_dir" | cut -f1)
    log_success "Backup completed successfully!"
    log_info "Backup location: $backup_dir"
    log_info "Total backup size: $total_size"
    log_info "Files created:"
    ls -la "$backup_dir"
}

# Function to list available backups
list_backups() {
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        log_warning "No backup directory found at $BACKUP_BASE_DIR"
        return
    fi
    
    log_info "Available backups in $BACKUP_BASE_DIR:"
    echo
    
    for backup_dir in "$BACKUP_BASE_DIR"/*/; do
        if [[ -d "$backup_dir" ]]; then
            local dir_name=$(basename "$backup_dir")
            local backup_info="$backup_dir/backup_info.txt"
            local size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1 || echo "Unknown")
            
            echo -e "${GREEN}$dir_name${NC} (Size: $size)"
            
            if [[ -f "$backup_info" ]]; then
                echo "  Created: $(grep "Backup Created:" "$backup_info" | cut -d: -f2-)"
                echo "  Volumes: $(grep "Volumes Backed Up:" "$backup_info" | cut -d: -f2-)"
            fi
            echo
        fi
    done
}

# Function to restore volumes
restore_volumes() {
    check_docker
    
    if [[ $# -eq 0 ]]; then
        log_error "Please specify the backup timestamp to restore from."
        log_info "Usage: $0 restore <timestamp>"
        log_info "Available backups:"
        list_backups
        exit 1
    fi
    
    local timestamp="$1"
    local backup_dir="$BACKUP_BASE_DIR/$timestamp"
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        list_backups
        exit 1
    fi
    
    log_warning "This will restore volumes from backup: $timestamp"
    log_warning "This operation will OVERWRITE existing volume data!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled."
        exit 0
    fi
    
    log_info "Starting restore process..."
    
    for volume in "${VOLUMES[@]}"; do
        local backup_file="$backup_dir/${volume}.tar.gz"
        
        if [[ -f "$backup_file" ]]; then
            log_info "Restoring volume: $volume"
            
            # Create volume if it doesn't exist
            if ! volume_exists "$volume"; then
                log_info "Creating volume: $volume"
                docker volume create "$volume"
            fi
            
            # Restore volume
            docker run --rm \
                -v "$volume":/volume \
                -v "$(pwd)/$backup_dir":/backup \
                busybox sh -c "rm -rf /volume/* /volume/..?* /volume/.[!.]* 2>/dev/null || true; tar xzf /backup/${volume}.tar.gz -C /volume"
            
            log_success "✓ $volume restored successfully"
        else
            log_warning "Backup file not found for volume: $volume (${backup_file})"
        fi
    done
    
    log_success "Restore completed successfully!"
}

# Function to show usage
show_usage() {
    echo "Docker Volume Backup and Restore Script"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  backup          Create a backup of all configured volumes"
    echo "  restore <time>  Restore volumes from a specific backup"
    echo "  list            List all available backups"
    echo "  help            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 list"
    echo "  $0 restore 20240708_143022"
    echo
    echo "Configured volumes: ${VOLUMES[@]}"
    echo "Backup directory: $BACKUP_BASE_DIR"
}

# Main script logic
case "${1:-help}" in
    backup)
        backup_volumes
        ;;
    restore)
        restore_volumes "${2:-}"
        ;;
    list)
        list_backups
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo
        show_usage
        exit 1
        ;;
esac
