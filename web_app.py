#!/usr/bin/env python3
"""
Synology NAS Shutdown Web Interface
A Flask web application with a simple shutdown button
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from synology_shutdown import SynologyShutdown, load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'synology-shutdown-secret-key')

# Global variables for tracking shutdown state
shutdown_status = {
    'in_progress': False,
    'success': None,
    'message': '',
    'timestamp': None
}


def shutdown_nas_async(config):
    """Perform NAS shutdown in background thread"""
    global shutdown_status
    
    try:
        shutdown_status['in_progress'] = True
        shutdown_status['message'] = 'Connecting to NAS...'
        shutdown_status['timestamp'] = datetime.now()
        
        nas = SynologyShutdown(
            host=config['host'],
            username=config['username'],
            password=config['password'],
            port=config['port'],
            use_https=config['use_https']
        )
        
        shutdown_status['message'] = 'Initiating shutdown...'
        success = nas.shutdown(
            use_ssh=config.get('use_ssh', False),
            ssh_port=config.get('ssh_port', 22)
        )
        
        shutdown_status['success'] = success
        shutdown_status['in_progress'] = False
        
        if success:
            shutdown_status['message'] = 'NAS shutdown initiated successfully'
        else:
            shutdown_status['message'] = 'Failed to shutdown NAS'
            
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        shutdown_status['success'] = False
        shutdown_status['in_progress'] = False
        shutdown_status['message'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Main page with shutdown button"""
    config = load_config()
    nas_host = config.get('host', 'Not configured')
    return render_template('index.html', nas_host=nas_host, status=shutdown_status)


@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Handle shutdown request"""
    global shutdown_status
    
    if shutdown_status['in_progress']:
        return jsonify({
            'success': False,
            'message': 'Shutdown already in progress'
        }), 400
    
    config = load_config()
    
    # Validate configuration
    required_fields = ['host', 'username', 'password']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f'Missing configuration: {", ".join(missing_fields)}'
        }), 400
    
    # Start shutdown in background thread
    shutdown_thread = threading.Thread(target=shutdown_nas_async, args=(config,))
    shutdown_thread.daemon = True
    shutdown_thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Shutdown initiated'
    })


@app.route('/status')
def status():
    """Get current shutdown status"""
    return jsonify(shutdown_status)


@app.route('/config')
def config_page():
    """Configuration page"""
    config = load_config()
    # Don't expose password in the config page
    safe_config = {k: v for k, v in config.items() if k != 'password'}
    if 'password' in config:
        safe_config['password'] = '••••••••' if config['password'] else ''
    
    return render_template('config.html', config=safe_config)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    config = load_config()
    
    # Validate configuration on startup
    required_fields = ['host', 'username', 'password']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        logger.warning(f"Missing configuration fields: {', '.join(missing_fields)}")
        logger.warning("Web interface will be available but shutdown will fail until configured")
    else:
        logger.info(f"Configured for NAS at {config['host']}:{config.get('port', 5000)}")
    
    # Run Flask app
    port = int(os.environ.get('WEB_PORT', 8080))
    host = os.environ.get('WEB_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting web interface on {host}:{port}")
    app.run(host=host, port=port, debug=debug)