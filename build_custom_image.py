#!/usr/bin/env python3
"""
Frappe Docker Custom Image Builder

A robust script for building custom Frappe/ERPNext Docker images with enhanced features:
- Configuration management (CLI args, env vars, config files)
- Multiple build methods (layered, custom)
- Comprehensive error handling and logging
- Progress tracking and timing
- Interactive mode with validation
- Cleanup and resource management
- Beautiful output formatting

Usage:
    python build_custom_image.py [OPTIONS]
    
Examples:
    # Basic build with default settings
    python build_custom_image.py
    
    # Build with custom tag and apps file
    python build_custom_image.py --tag mycompany/frappe:v15 --apps-file custom_apps.json
    
    # Custom build with specific versions
    python build_custom_image.py --build-method custom --python-version 3.11.9 --node-version 20.19.2
    
    # Interactive mode
    python build_custom_image.py --interactive
    
    # Dry run to see what would be executed
    python build_custom_image.py --dry-run
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class FrappeImageBuilder:
    """Main class for building Frappe Docker images"""
    
    def __init__(self):
        self.config = {}
        self.logger = self._setup_logging()
        self.start_time = None
        self.temp_files = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        handlers = [logging.StreamHandler()]
        
        # Try to add file handler, but don't fail if we can't create the log file
        try:
            handlers.append(logging.FileHandler('build_custom_image.log'))
        except PermissionError:
            # If we can't write to the current directory, try /tmp
            try:
                handlers.append(logging.FileHandler('/tmp/build_custom_image.log'))
            except PermissionError:
                # If we can't write anywhere, just use console logging
                pass
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        return logging.getLogger(__name__)
    
    def _print_banner(self):
        """Print a beautiful banner"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Frappe Docker Custom Image Builder                        ║
║                                                                              ║
║  🐳 Building custom Frappe/ERPNext Docker images with style                 ║
║  🚀 Enhanced with robust error handling and beautiful output                ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
        """
        print(banner)
    
    def _print_status(self, message: str, status: str = "INFO"):
        """Print formatted status messages"""
        color_map = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER
        }
        color = color_map.get(status, Colors.OKBLUE)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
        
    def _validate_prerequisites(self) -> bool:
        """Validate system prerequisites"""
        self._print_status("🔍 Validating prerequisites...", "INFO")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self._print_status("❌ Docker is not installed or not accessible", "ERROR")
                return False
            self._print_status(f"✅ Docker: {result.stdout.strip()}", "SUCCESS")
        except FileNotFoundError:
            self._print_status("❌ Docker command not found", "ERROR")
            return False
        
        # Check Docker daemon
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode != 0:
                self._print_status("❌ Docker daemon is not running", "ERROR")
                return False
        except Exception as e:
            self._print_status(f"❌ Docker daemon check failed: {e}", "ERROR")
            return False
        
        # Check required files
        required_files = [
            'images/layered/Containerfile',
            'images/custom/Containerfile'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self._print_status(f"❌ Required file missing: {file_path}", "ERROR")
                return False
        
        self._print_status("✅ All prerequisites validated", "SUCCESS")
        return True
    
    def _load_apps_config(self, apps_file: str) -> List[Dict]:
        """Load and validate apps configuration"""
        self._print_status(f"📄 Loading apps configuration from {apps_file}...", "INFO")
        
        try:
            with open(apps_file, 'r') as f:
                apps_config = json.load(f)
            
            # Validate apps configuration
            if not isinstance(apps_config, list):
                raise ValueError("Apps configuration must be a JSON array")
            
            for i, app in enumerate(apps_config):
                if not isinstance(app, dict):
                    raise ValueError(f"App {i} must be a JSON object")
                if 'url' not in app:
                    raise ValueError(f"App {i} missing required 'url' field")
                if 'branch' not in app:
                    raise ValueError(f"App {i} missing required 'branch' field")
            
            self._print_status(f"✅ Loaded {len(apps_config)} apps from configuration", "SUCCESS")
            for i, app in enumerate(apps_config, 1):
                self._print_status(f"   {i}. {app['url']} (branch: {app['branch']})", "INFO")
            
            return apps_config
            
        except FileNotFoundError:
            self._print_status(f"❌ Apps file not found: {apps_file}", "ERROR")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self._print_status(f"❌ Invalid JSON in apps file: {e}", "ERROR")
            sys.exit(1)
        except ValueError as e:
            self._print_status(f"❌ Invalid apps configuration: {e}", "ERROR")
            sys.exit(1)
    
    def _get_build_args(self) -> Dict[str, str]:
        """Generate build arguments based on configuration"""
        build_args = {
            'FRAPPE_PATH': self.config['frappe_path'],
            'FRAPPE_BRANCH': self.config['frappe_branch'],
            'APPS_JSON_BASE64': self.config['apps_json_base64']
        }
        
        if self.config['build_method'] == 'custom':
            build_args.update({
                'PYTHON_VERSION': self.config['python_version'],
                'NODE_VERSION': self.config['node_version'],
                'DEBIAN_BASE': self.config['debian_base'],
                'WKHTMLTOPDF_VERSION': self.config['wkhtmltopdf_version'],
                'WKHTMLTOPDF_DISTRO': self.config['wkhtmltopdf_distro']
            })
        
        return build_args
    
    def _build_docker_command(self) -> List[str]:
        """Build the Docker command"""
        build_args = self._get_build_args()
        
        cmd = ['docker', 'build']
        
        # Add build arguments
        for key, value in build_args.items():
            cmd.extend(['--build-arg', f'{key}={value}'])
        
        # Add tag
        cmd.extend(['--tag', self.config['tag']])
        
        # Add dockerfile
        dockerfile = f"images/{self.config['build_method']}/Containerfile"
        cmd.extend(['--file', dockerfile])
        
        # Add build context
        cmd.append('.')
        
        return cmd
    
    def _execute_build(self, cmd: List[str]) -> bool:
        """Execute the Docker build command"""
        if self.config['dry_run']:
            self._print_status("🔍 DRY RUN - Would execute:", "WARNING")
            self._print_status(f"   {' '.join(cmd)}", "INFO")
            return True
        
        self._print_status("🔨 Starting Docker build...", "INFO")
        self._print_status(f"Command: {' '.join(cmd)}", "INFO")
        
        try:
            # Use subprocess.run with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output in real-time
            for line in iter(process.stdout.readline, ''):
                print(f"{Colors.OKCYAN}[BUILD] {line.rstrip()}{Colors.ENDC}")
            
            process.wait()
            
            if process.returncode == 0:
                self._print_status("✅ Docker build completed successfully!", "SUCCESS")
                return True
            else:
                self._print_status(f"❌ Docker build failed with exit code {process.returncode}", "ERROR")
                return False
                
        except KeyboardInterrupt:
            self._print_status("⚠️  Build interrupted by user", "WARNING")
            return False
        except Exception as e:
            self._print_status(f"❌ Build failed with error: {e}", "ERROR")
            return False
    
    def _cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    os.remove(temp_file)
                    self._print_status(f"🧹 Cleaned up temporary file: {temp_file}", "INFO")
            except Exception as e:
                self._print_status(f"⚠️  Failed to clean up {temp_file}: {e}", "WARNING")
    
    def _interactive_config(self):
        """Interactive configuration mode"""
        self._print_status("🎯 Interactive configuration mode", "HEADER")
        
        # Build method
        print(f"\n{Colors.BOLD}Build Method:{Colors.ENDC}")
        print("1. layered (faster, uses pre-built base images)")
        print("2. custom (slower, allows custom Python/Node versions)")
        choice = input(f"{Colors.OKBLUE}Choose build method (1-2) [1]: {Colors.ENDC}").strip()
        self.config['build_method'] = 'custom' if choice == '2' else 'layered'
        
        # Apps file
        apps_file = input(f"{Colors.OKBLUE}Apps JSON file path [apps.json]: {Colors.ENDC}").strip()
        self.config['apps_file'] = apps_file if apps_file else 'apps.json'
        
        # Tag
        tag = input(f"{Colors.OKBLUE}Docker image tag [frappe_custom:latest]: {Colors.ENDC}").strip()
        self.config['tag'] = tag if tag else 'frappe_custom:latest'
        
        # Frappe branch
        branch = input(f"{Colors.OKBLUE}Frappe branch [version-15]: {Colors.ENDC}").strip()
        self.config['frappe_branch'] = branch if branch else 'version-15'
        
        if self.config['build_method'] == 'custom':
            # Python version
            python_ver = input(f"{Colors.OKBLUE}Python version [3.11.6]: {Colors.ENDC}").strip()
            self.config['python_version'] = python_ver if python_ver else '3.11.6'
            
            # Node version
            node_ver = input(f"{Colors.OKBLUE}Node.js version [20.19.2]: {Colors.ENDC}").strip()
            self.config['node_version'] = node_ver if node_ver else '20.19.2'
    
    def _parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Build custom Frappe/ERPNext Docker images",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --tag mycompany/frappe:v15
  %(prog)s --build-method custom --python-version 3.11.9
  %(prog)s --interactive
  %(prog)s --dry-run
            """
        )
        
        parser.add_argument(
            '--apps-file', '-a',
            default='apps.json',
            help='Path to apps JSON file (default: apps.json)'
        )
        
        parser.add_argument(
            '--tag', '-t',
            default='frappe_custom:latest',
            help='Docker image tag (default: frappe_custom:latest)'
        )
        
        parser.add_argument(
            '--build-method', '-m',
            choices=['layered', 'custom'],
            default='layered',
            help='Build method: layered (faster) or custom (more control)'
        )
        
        parser.add_argument(
            '--frappe-path',
            default='https://github.com/frappe/frappe',
            help='Frappe repository URL'
        )
        
        parser.add_argument(
            '--frappe-branch',
            default='version-15',
            help='Frappe branch (default: version-15)'
        )
        
        parser.add_argument(
            '--python-version',
            default='3.11.6',
            help='Python version for custom builds (default: 3.11.6)'
        )
        
        parser.add_argument(
            '--node-version',
            default='20.19.2',
            help='Node.js version for custom builds (default: 20.19.2)'
        )
        
        parser.add_argument(
            '--debian-base',
            default='bookworm',
            help='Debian base version (default: bookworm)'
        )
        
        parser.add_argument(
            '--wkhtmltopdf-version',
            default='0.12.6.1-3',
            help='wkhtmltopdf version (default: 0.12.6.1-3)'
        )
        
        parser.add_argument(
            '--wkhtmltopdf-distro',
            default='bookworm',
            help='wkhtmltopdf distro (default: bookworm)'
        )
        
        parser.add_argument(
            '--interactive', '-i',
            action='store_true',
            help='Interactive configuration mode'
        )
        
        parser.add_argument(
            '--dry-run', '-n',
            action='store_true',
            help='Show what would be executed without running'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Quiet mode (minimal output)'
        )
        
        return parser.parse_args()
    
    def _load_config(self, args: argparse.Namespace):
        """Load configuration from arguments and environment variables"""
        self.config = {
            'apps_file': args.apps_file,
            'tag': args.tag,
            'build_method': args.build_method,
            'frappe_path': args.frappe_path,
            'frappe_branch': args.frappe_branch,
            'python_version': args.python_version,
            'node_version': args.node_version,
            'debian_base': args.debian_base,
            'wkhtmltopdf_version': args.wkhtmltopdf_version,
            'wkhtmltopdf_distro': args.wkhtmltopdf_distro,
            'interactive': args.interactive,
            'dry_run': args.dry_run,
            'verbose': args.verbose,
            'quiet': args.quiet
        }
        
        # Override with environment variables if present
        env_mappings = {
            'FRAPPE_PATH': 'frappe_path',
            'FRAPPE_BRANCH': 'frappe_branch',
            'PYTHON_VERSION': 'python_version',
            'NODE_VERSION': 'node_version',
            'DOCKER_TAG': 'tag',
            'APPS_FILE': 'apps_file'
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                self.config[config_key] = os.environ[env_var]
                self._print_status(f"📝 Using {config_key} from environment: {os.environ[env_var]}", "INFO")
    
    def _print_config_summary(self):
        """Print configuration summary"""
        self._print_status("📋 Configuration Summary", "HEADER")
        
        config_items = [
            ("Build Method", self.config['build_method']),
            ("Apps File", self.config['apps_file']),
            ("Docker Tag", self.config['tag']),
            ("Frappe Path", self.config['frappe_path']),
            ("Frappe Branch", self.config['frappe_branch'])
        ]
        
        if self.config['build_method'] == 'custom':
            config_items.extend([
                ("Python Version", self.config['python_version']),
                ("Node.js Version", self.config['node_version']),
                ("Debian Base", self.config['debian_base'])
            ])
        
        for key, value in config_items:
            print(f"  {Colors.OKBLUE}{key:15}: {Colors.ENDC}{value}")
    
    def _print_build_summary(self, success: bool, duration: float):
        """Print build summary"""
        if success:
            self._print_status("🎉 Build Summary", "SUCCESS")
            print(f"  {Colors.OKGREEN}✅ Status: SUCCESS{Colors.ENDC}")
            print(f"  {Colors.OKGREEN}⏱️  Duration: {duration:.2f} seconds{Colors.ENDC}")
            print(f"  {Colors.OKGREEN}🏷️  Tag: {self.config['tag']}{Colors.ENDC}")
            print(f"  {Colors.OKGREEN}📦 Method: {self.config['build_method']}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
            print(f"  • Test the image: {Colors.OKCYAN}docker run --rm {self.config['tag']} --version{Colors.ENDC}")
            print(f"  • Push to registry: {Colors.OKCYAN}docker push {self.config['tag']}{Colors.ENDC}")
            print(f"  • Use in compose: {Colors.OKCYAN}CUSTOM_IMAGE={self.config['tag'].split(':')[0]} CUSTOM_TAG={self.config['tag'].split(':')[1]}{Colors.ENDC}")
        else:
            self._print_status("💥 Build Failed", "ERROR")
            print(f"  {Colors.FAIL}❌ Status: FAILED{Colors.ENDC}")
            print(f"  {Colors.FAIL}⏱️  Duration: {duration:.2f} seconds{Colors.ENDC}")
            print(f"  {Colors.FAIL}📝 Check logs: build_custom_image.log{Colors.ENDC}")
    
    def build(self):
        """Main build method"""
        try:
            self.start_time = time.time()
            
            # Parse arguments
            args = self._parse_arguments()
            
            # Setup quiet mode
            if args.quiet:
                self.logger.setLevel(logging.ERROR)
            elif args.verbose:
                self.logger.setLevel(logging.DEBUG)
            
            if not args.quiet:
                self._print_banner()
            
            # Load configuration
            self._load_config(args)
            
            # Interactive mode
            if self.config['interactive']:
                self._interactive_config()
            
            # Validate prerequisites
            if not self._validate_prerequisites():
                sys.exit(1)
            
            # Load apps configuration
            apps_config = self._load_apps_config(self.config['apps_file'])
            
            # Encode apps JSON
            apps_json_str = json.dumps(apps_config, indent=2)
            self.config['apps_json_base64'] = b64encode(apps_json_str.encode()).decode()
            
            # Print configuration summary
            if not self.config['quiet']:
                self._print_config_summary()
            
            # Build Docker command
            cmd = self._build_docker_command()
            
            # Execute build
            success = self._execute_build(cmd)
            
            # Calculate duration
            duration = time.time() - self.start_time
            
            # Print summary
            if not self.config['quiet']:
                self._print_build_summary(success, duration)
            
            # Exit with appropriate code
            sys.exit(0 if success else 1)
            
        except KeyboardInterrupt:
            self._print_status("⚠️  Build interrupted by user", "WARNING")
            sys.exit(130)
        except Exception as e:
            self._print_status(f"💥 Unexpected error: {e}", "ERROR")
            self.logger.exception("Unexpected error occurred")
            sys.exit(1)
        finally:
            self._cleanup()

def main():
    """Main entry point"""
    builder = FrappeImageBuilder()
    builder.build()

if __name__ == "__main__":
    main()