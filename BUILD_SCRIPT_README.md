# Enhanced Frappe Docker Image Builder

A robust, feature-rich Python script for building custom Frappe/ERPNext Docker images with enhanced capabilities.

## 🚀 Features

- **Multiple Build Methods**: Choose between `layered` (faster) or `custom` (more control) builds
- **Configuration Management**: Support for CLI arguments, environment variables, and config files
- **Interactive Mode**: Guided configuration with prompts
- **Comprehensive Validation**: Prerequisites checking and input validation
- **Beautiful Output**: Colored, formatted output with progress indicators
- **Error Handling**: Robust error handling with detailed logging
- **Dry Run Mode**: See what would be executed without actually building
- **Logging**: Comprehensive logging to file and console
- **Cleanup**: Automatic cleanup of temporary files

## 📋 Prerequisites

- Docker installed and running
- Python 3.6+ 
- Required Containerfiles in `images/layered/` and `images/custom/` directories
- Valid `apps.json` file with your app configurations

## 🎯 Quick Start

1. **Basic build with default settings:**
   ```bash
   ./build_custom_image.py
   ```

2. **Interactive mode (recommended for first-time users):**
   ```bash
   ./build_custom_image.py --interactive
   ```

3. **Dry run to see what would be executed:**
   ```bash
   ./build_custom_image.py --dry-run
   ```

## 📖 Usage Examples

### Basic Usage
```bash
# Build with defaults
./build_custom_image.py

# Custom tag and apps file
./build_custom_image.py --tag mycompany/frappe:v15 --apps-file custom_apps.json

# Custom build method with specific versions
./build_custom_image.py --build-method custom --python-version 3.11.9 --node-version 20.19.2
```

### Advanced Usage
```bash
# Production build
./build_custom_image.py \
  --build-method custom \
  --tag mycompany/frappe:v15.0.0 \
  --python-version 3.11.9 \
  --node-version 20.19.2 \
  --frappe-branch version-15

# Development build
./build_custom_image.py \
  --tag frappe_custom:dev \
  --frappe-branch develop

# Using environment variables
FRAPPE_BRANCH=version-14 DOCKER_TAG=frappe_custom:v14 ./build_custom_image.py
```

### Utility Commands
```bash
# Show help
./build_custom_image.py --help

# Verbose output
./build_custom_image.py --verbose

# Quiet mode
./build_custom_image.py --quiet

# See examples
./build_examples.sh
```

## ⚙️ Configuration Options

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--apps-file` | `-a` | `apps.json` | Path to apps JSON file |
| `--tag` | `-t` | `frappe_custom:latest` | Docker image tag |
| `--build-method` | `-m` | `layered` | Build method: layered or custom |
| `--frappe-path` | | `https://github.com/frappe/frappe` | Frappe repository URL |
| `--frappe-branch` | | `version-15` | Frappe branch |
| `--python-version` | | `3.11.6` | Python version (custom builds) |
| `--node-version` | | `20.19.2` | Node.js version (custom builds) |
| `--debian-base` | | `bookworm` | Debian base version |
| `--interactive` | `-i` | | Interactive configuration mode |
| `--dry-run` | `-n` | | Show commands without executing |
| `--verbose` | `-v` | | Enable verbose output |
| `--quiet` | `-q` | | Minimal output mode |

### Environment Variables

You can override any configuration using environment variables:

- `FRAPPE_PATH` - Frappe repository URL
- `FRAPPE_BRANCH` - Frappe branch
- `PYTHON_VERSION` - Python version
- `NODE_VERSION` - Node.js version
- `DOCKER_TAG` - Docker image tag
- `APPS_FILE` - Apps JSON file path

### Apps Configuration

Create an `apps.json` file with your desired apps:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/frappe/payments",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/your-org/custom-app",
    "branch": "main"
  }
]
```

## 🔧 Build Methods

### Layered Build (Recommended)
- **Faster**: Uses pre-built base images
- **Efficient**: Leverages Docker layer caching
- **Use case**: Most common scenarios

### Custom Build
- **Flexible**: Full control over Python/Node versions
- **Slower**: Builds everything from scratch
- **Use case**: Specific version requirements

## 📁 Files Created

- `build_custom_image.log` - Build logs (or `/tmp/build_custom_image.log` if permission denied)
- `build_config.yaml` - Sample configuration file
- `build_examples.sh` - Usage examples script

## 🎨 Output Features

- **Colored output** with status indicators
- **Progress tracking** with timestamps
- **Build summary** with timing information
- **Error details** with helpful suggestions
- **Interactive prompts** for guided configuration

## 🔍 Troubleshooting

### Common Issues

1. **Permission denied for log file**
   - The script automatically falls back to `/tmp/` for logging
   - Or run with appropriate permissions

2. **Docker daemon not running**
   - Start Docker: `sudo systemctl start docker`
   - Check status: `docker info`

3. **Invalid apps.json**
   - Validate syntax: `jq empty apps.json`
   - Check required fields: `url` and `branch`

4. **Build failures**
   - Check logs in `build_custom_image.log`
   - Use `--verbose` for detailed output
   - Try `--dry-run` first to validate configuration

### Getting Help

1. **View all options**: `./build_custom_image.py --help`
2. **See examples**: `./build_examples.sh`
3. **Check logs**: `cat build_custom_image.log`
4. **Validate apps**: `jq empty apps.json`

## 🚀 Next Steps After Building

1. **Test your image:**
   ```bash
   docker run --rm your-tag:latest --version
   ```

2. **Push to registry:**
   ```bash
   docker push your-tag:latest
   ```

3. **Use in docker-compose:**
   ```bash
   export CUSTOM_IMAGE=your-image
   export CUSTOM_TAG=your-tag
   docker-compose up
   ```

## 📝 Examples of Complete Workflows

### Development Workflow
```bash
# 1. Edit apps for development
vim apps.json

# 2. Build development image
./build_custom_image.py --tag frappe_dev:latest --frappe-branch develop

# 3. Test the image
docker run --rm frappe_dev:latest bench --version
```

### Production Workflow
```bash
# 1. Create production apps config
cp apps.json apps_production.json
# Edit apps_production.json for production apps

# 2. Build production image
./build_custom_image.py \
  --build-method custom \
  --apps-file apps_production.json \
  --tag mycompany/frappe:v15.0.0 \
  --python-version 3.11.9

# 3. Push to registry
docker push mycompany/frappe:v15.0.0
```

## 🤝 Contributing

Feel free to enhance this script with additional features:
- YAML configuration file support
- Multi-architecture builds
- Build caching options
- Integration with CI/CD pipelines
- Additional validation checks

---

**Happy Building! 🐳**
