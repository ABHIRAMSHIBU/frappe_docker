#!/bin/bash

# Frappe Docker Build Examples
# This script demonstrates various ways to use the build_custom_image.py script

set -e

echo "🚀 Frappe Docker Build Examples"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_example() {
    echo -e "\n${BLUE}📋 Example: $1${NC}"
    echo -e "${YELLOW}Command:${NC} $2"
    echo -e "${GREEN}Description:${NC} $3"
}

print_example "Basic Build" \
    "./build_custom_image.py" \
    "Build with default settings using apps.json file"

print_example "Custom Tag and Apps File" \
    "./build_custom_image.py --tag mycompany/frappe:v15 --apps-file custom_apps.json" \
    "Build with custom Docker tag and different apps configuration"

print_example "Custom Build Method" \
    "./build_custom_image.py --build-method custom --python-version 3.11.9 --node-version 20.19.2" \
    "Build using custom method with specific Python and Node.js versions"

print_example "Interactive Mode" \
    "./build_custom_image.py --interactive" \
    "Interactive configuration mode with prompts"

print_example "Dry Run" \
    "./build_custom_image.py --dry-run" \
    "Show what would be executed without actually building"

print_example "Verbose Output" \
    "./build_custom_image.py --verbose" \
    "Enable detailed logging output"

print_example "Quiet Mode" \
    "./build_custom_image.py --quiet" \
    "Minimal output mode"

print_example "Development Build" \
    "./build_custom_image.py --tag frappe_custom:dev --frappe-branch develop" \
    "Build development version with develop branch"

print_example "Production Build" \
    "./build_custom_image.py --build-method custom --tag mycompany/frappe:v15.0.0 --python-version 3.11.9" \
    "Production build with custom versions and proper tagging"

print_example "Environment Variables" \
    "FRAPPE_BRANCH=version-14 DOCKER_TAG=frappe_custom:v14 ./build_custom_image.py" \
    "Using environment variables to override defaults"

print_example "Help" \
    "./build_custom_image.py --help" \
    "Show all available options and detailed help"

echo -e "\n${GREEN}💡 Tips:${NC}"
echo "• Use --dry-run first to see what will be executed"
echo "• Check apps.json syntax with: jq empty apps.json"
echo "• Use --interactive mode for guided configuration"
echo "• Log files are saved to build_custom_image.log"
echo "• Environment variables can override any setting"

echo -e "\n${YELLOW}📁 Files:${NC}"
echo "• apps.json - Default apps configuration"
echo "• build_config.yaml - Sample configuration file"
echo "• build_custom_image.log - Build logs"

echo -e "\n${BLUE}🔧 Quick Start:${NC}"
echo "1. Edit apps.json with your desired apps"
echo "2. Run: ./build_custom_image.py --interactive"
echo "3. Follow the prompts to configure your build"
echo "4. Wait for the build to complete"
echo "5. Test your image: docker run --rm <your-tag> --version"
