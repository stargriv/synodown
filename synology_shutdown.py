#!/usr/bin/env python3
"""
Synology NAS Shutdown Tool
A Docker-ready application to safely shutdown a Synology NAS without login UI
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from typing import Optional, Dict, Any
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SynologyShutdown:
    def __init__(self, host: str, username: str, password: str, port: int = 5000, use_https: bool = True):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_https = use_https
        self.session_id = None
        self.base_url = f"{'https' if use_https else 'http'}://{host}:{port}"
        
    def _make_request(self, api: str, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make API request to Synology DSM"""
        if api == 'SYNO.API.Auth':
            url = f"{self.base_url}/webapi/auth.cgi"
        else:
            url = f"{self.base_url}/webapi/{api}"
        params.update({
            'api': api,
            'method': method,
            'version': 3 if api == 'SYNO.API.Auth' else 1
        })
        
        try:
            response = requests.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def _make_request_with_endpoint(self, endpoint: str, api: str, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make API request to Synology DSM with specific endpoint"""
        url = f"{self.base_url}/webapi/{endpoint}"
        params.update({
            'api': api,
            'method': method,
            'version': 1
        })
        
        try:
            response = requests.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def login(self) -> bool:
        """Authenticate with Synology DSM"""
        logger.info("Attempting to login to Synology DSM...")
        
        params = {
            'account': self.username,
            'passwd': self.password,
            'session': 'DSM',
            'format': 'sid'
        }
        
        result = self._make_request('SYNO.API.Auth', 'login', params)
        if result and result.get('success'):
            self.session_id = result.get('data', {}).get('sid')
            logger.info("Successfully logged in to Synology DSM")
            return True
        
        logger.error("Failed to login to Synology DSM")
        return False
    
    def shutdown_via_api(self) -> bool:
        """Attempt shutdown via DSM Web API"""
        if not self.session_id:
            logger.error("Not logged in")
            return False
        
        logger.info("Attempting shutdown via DSM Web API...")
        
        params = {
            '_sid': self.session_id
        }
        
        # Try different API endpoints for shutdown
        api_endpoints = [
            ('entry.cgi', 'SYNO.Core.System', 'shutdown'),
            ('entry.cgi', 'SYNO.Core.System.Utilization', 'shutdown'),
            ('entry.cgi', 'SYNO.DSM.System', 'shutdown')
        ]
        
        for endpoint, api, method in api_endpoints:
            result = self._make_request_with_endpoint(endpoint, api, method, params)
            if result and result.get('success'):
                logger.info("Shutdown command sent successfully via API")
                return True
            elif result:
                logger.warning(f"API {api} failed: {result}")
        
        logger.error("All API shutdown methods failed")
        return False
    
    def shutdown_via_ssh(self, ssh_port: int = 22) -> bool:
        """Attempt shutdown via SSH (requires SSH enabled on NAS)"""
        logger.info("Attempting shutdown via SSH...")
        
        try:
            cmd = [
                'sshpass', '-p', self.password,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-p', str(ssh_port),
                f'{self.username}@{self.host}',
                'sudo shutdown -h now'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Shutdown command sent successfully via SSH")
                return True
            else:
                logger.error(f"SSH shutdown failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("SSH shutdown timed out")
            return False
        except FileNotFoundError:
            logger.error("sshpass not found. SSH method requires sshpass to be installed.")
            return False
        except Exception as e:
            logger.error(f"SSH shutdown failed: {e}")
            return False
    
    def logout(self):
        """Logout from DSM session"""
        if self.session_id:
            params = {'_sid': self.session_id}
            self._make_request('auth.cgi', 'logout', params)
            logger.info("Logged out from Synology DSM")
    
    def shutdown(self, use_ssh: bool = False, ssh_port: int = 22) -> bool:
        """Main shutdown method"""
        success = False
        
        try:
            if self.login():
                if not use_ssh:
                    success = self.shutdown_via_api()
                
                if not success and use_ssh:
                    success = self.shutdown_via_ssh(ssh_port)
                
                self.logout()
            
            return success
        
        except KeyboardInterrupt:
            logger.info("Shutdown cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during shutdown: {e}")
            return False


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables or config file"""
    config = {}
    
    # Try to load from config file
    config_file = os.environ.get('CONFIG_FILE', '/app/config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    # Environment variables override config file
    config.update({
        'host': os.environ.get('SYNOLOGY_HOST', config.get('host', '')),
        'username': os.environ.get('SYNOLOGY_USERNAME', config.get('username', '')),
        'password': os.environ.get('SYNOLOGY_PASSWORD', config.get('password', '')),
        'port': int(os.environ.get('SYNOLOGY_PORT', config.get('port', 5000))),
        'use_https': os.environ.get('SYNOLOGY_HTTPS', str(config.get('use_https', True))).lower() == 'true',
        'ssh_port': int(os.environ.get('SYNOLOGY_SSH_PORT', config.get('ssh_port', 22))),
        'use_ssh': os.environ.get('USE_SSH', str(config.get('use_ssh', False))).lower() == 'true'
    })
    
    return config


def main():
    parser = argparse.ArgumentParser(description='Shutdown Synology NAS')
    parser.add_argument('--host', help='Synology NAS IP address or hostname')
    parser.add_argument('--username', help='Admin username')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--port', type=int, default=5000, help='DSM port (default: 5000)')
    parser.add_argument('--ssh-port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--use-ssh', action='store_true', help='Use SSH method for shutdown')
    parser.add_argument('--no-https', action='store_true', help='Use HTTP instead of HTTPS')
    parser.add_argument('--config', help='Path to JSON config file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Command line arguments override config
    host = args.host or config.get('host')
    username = args.username or config.get('username')
    password = args.password or config.get('password')
    port = args.port if args.port != 5000 else config.get('port', 5000)
    use_https = not args.no_https and config.get('use_https', True)
    ssh_port = args.ssh_port if args.ssh_port != 22 else config.get('ssh_port', 22)
    use_ssh = args.use_ssh or config.get('use_ssh', False)
    
    if not all([host, username, password]):
        logger.error("Missing required configuration: host, username, and password must be provided")
        sys.exit(1)
    
    logger.info(f"Connecting to Synology NAS at {host}:{port}")
    
    nas = SynologyShutdown(host, username, password, port, use_https)
    
    if nas.shutdown(use_ssh, ssh_port):
        logger.info("NAS shutdown initiated successfully")
        sys.exit(0)
    else:
        logger.error("Failed to shutdown NAS")
        sys.exit(1)


if __name__ == '__main__':
    main()