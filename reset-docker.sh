#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Stop all containers
log_info "Stopping all containers..."
containers=$(sudo docker ps -aq)
if [ -n "$containers" ]; then
    sudo docker stop $containers
    log_success "All containers stopped."
else
    log_info "No containers to stop."
fi

# Remove all containers
log_info "Removing all containers..."
if [ -n "$containers" ]; then
    sudo docker rm $containers
    log_success "All containers removed."
else
    log_info "No containers to remove."
fi

# Remove all volumes
log_info "Removing all Docker volumes..."
volumes=$(sudo docker volume ls -q)
if [ -n "$volumes" ]; then
    sudo docker volume rm $volumes
    log_success "All volumes removed."
else
    log_info "No volumes to remove."
fi

# Remove all user-defined networks (ignore default bridge/host/none)
log_info "Removing all user-defined Docker networks..."
default_nets=(bridge host none)
user_nets=$(sudo docker network ls --format '{{.Name}}' | grep -v -E '^(bridge|host|none)$')
if [ -n "$user_nets" ]; then
    for net in $user_nets; do
        sudo docker network rm "$net"
    done
    log_success "All user-defined networks removed."
else
    log_info "No user-defined networks to remove."
fi

# Remove all images
log_info "Removing all Docker images..."
images=$(sudo docker image ls -q)
if [ -n "$images" ]; then
    sudo docker rmi $images --force
    log_success "All images removed."
else
    log_info "No images to remove."
fi

# Final prune
log_info "Running final system prune..."
sudo docker system prune -a --volumes -f
log_success "Docker system pruned."

# Verification
log_info "Verifying Docker is clean..."
remaining_containers=$(sudo docker ps -aq)
remaining_volumes=$(sudo docker volume ls -q)
remaining_images=$(sudo docker image ls -q)
remaining_networks=$(sudo docker network ls --format '{{.Name}}' | grep -v -E '^(bridge|host|none)$')

if [ -z "$remaining_containers" ]; then
    log_success "No containers remain."
else
    log_error "Some containers remain: $remaining_containers"
fi

if [ -z "$remaining_volumes" ]; then
    log_success "No volumes remain."
else
    log_error "Some volumes remain: $remaining_volumes"
fi

if [ -z "$remaining_images" ]; then
    log_success "No images remain."
else
    log_error "Some images remain: $remaining_images"
fi

if [ -z "$remaining_networks" ]; then
    log_success "No user-defined networks remain. Only default networks exist."
else
    log_warnibench get-app https://github.com/resilient-tech/india-compliance.git --branch version-15ng "Some user-defined networks remain: $remaining_networks"
fi

log_success "Docker reset complete!"


