# Synology NAS Shutdown Docker Container

A Docker container that safely shuts down a Synology NAS without requiring UI login, featuring both a web interface and command-line operation.

## Features

- **🌐 Web Interface**: Simple web UI with one-click shutdown button
- **💻 Command Line**: Direct CLI operation for scripts and automation
- **🔒 Multiple shutdown methods**: DSM Web API and SSH fallback
- **🛡️ Secure authentication**: Uses admin credentials for proper shutdown
- **🐳 Docker-ready**: Containerized for easy deployment
- **⚙️ Configurable**: Environment variables or JSON config file
- **📝 Logging**: Detailed logs for troubleshooting
- **📊 Real-time status**: Live updates during shutdown process

## Prerequisites

- Synology NAS with DSM 6.x or 7.x
- Admin account credentials
- Network access to the NAS
- (Optional) SSH enabled on NAS for fallback method

## Quick Start

### Method 1: Web Interface (Recommended)

1. Clone or download this repository
2. Edit `docker-compose.yml` with your NAS details:
   ```yaml
   environment:
     - SYNOLOGY_HOST=192.168.1.100  # Your NAS IP
     - SYNOLOGY_USERNAME=admin      # Admin username
     - SYNOLOGY_PASSWORD=yourpassword # Admin password
   ```
3. Start the web interface:
   ```bash
   docker-compose up --build
   ```
4. Open your browser to `http://localhost:8080`
5. Click the "🔴 Shutdown NAS" button

### Method 2: Command Line Interface

For direct shutdown (no web interface):
```bash
# Build the image
docker build -t synology-shutdown .

# Run CLI version
docker run --rm \
  -e SYNOLOGY_HOST=192.168.1.100 \
  -e SYNOLOGY_USERNAME=admin \
  -e SYNOLOGY_PASSWORD=yourpassword \
  synology-shutdown python synology_shutdown.py

# Or use CLI profile with docker-compose
docker-compose --profile cli up synology-shutdown-cli
```

### Method 3: Web Interface with Docker Run

```bash
# Build and run web interface
docker build -t synology-shutdown .

docker run --rm -p 8080:8080 \
  -e SYNOLOGY_HOST=192.168.1.100 \
  -e SYNOLOGY_USERNAME=admin \
  -e SYNOLOGY_PASSWORD=yourpassword \
  synology-shutdown
```

Then open `http://localhost:8080` in your browser.

### Method 4: Config File

1. Create a config file:
   ```bash
   mkdir -p config
   cp config.example.json config/config.json
   ```
2. Edit `config/config.json` with your NAS details
3. Run with volume mount:
   ```bash
   # Web interface
   docker run --rm -p 8080:8080 -v $(pwd)/config:/app/config synology-shutdown
   
   # CLI version
   docker run --rm -v $(pwd)/config:/app/config synology-shutdown python synology_shutdown.py
   ```

## Configuration Options

| Environment Variable | Config File Key | Default | Description |
|---------------------|-----------------|---------|-------------|
| `SYNOLOGY_HOST` | `host` | - | NAS IP address or hostname |
| `SYNOLOGY_USERNAME` | `username` | - | Admin username |
| `SYNOLOGY_PASSWORD` | `password` | - | Admin password |
| `SYNOLOGY_PORT` | `port` | `5000` | DSM web interface port |
| `SYNOLOGY_HTTPS` | `use_https` | `true` | Use HTTPS for API calls |
| `SYNOLOGY_SSH_PORT` | `ssh_port` | `22` | SSH port (if using SSH method) |
| `USE_SSH` | `use_ssh` | `false` | Use SSH method instead of API |
| `WEB_PORT` | - | `8080` | Web interface port |
| `WEB_HOST` | - | `0.0.0.0` | Web interface bind address |
| `FLASK_SECRET_KEY` | - | auto-generated | Secret key for web sessions |

## Usage Modes

### Web Interface Mode (Default)

The container runs a Flask web application on port 8080 by default:

```bash
docker-compose up
# Open http://localhost:8080
```

**Web Interface Features:**
- 🔴 One-click shutdown button
- 📊 Real-time status updates
- ⚙️ Configuration viewer
- 🛡️ Confirmation dialogs
- 📱 Mobile-responsive design

### Command Line Mode

For direct CLI operation:

```bash
# CLI with arguments
docker run --rm synology-shutdown python synology_shutdown.py \
  --host 192.168.1.100 \
  --username admin \
  --password yourpassword \
  --use-ssh

# View CLI help
docker run --rm synology-shutdown python synology_shutdown.py --help
```

## Shutdown Methods

### 1. DSM Web API (Default)
- Uses Synology's official DSM Web API
- Requires admin credentials
- More secure and reliable
- Works with most DSM versions

### 2. SSH Fallback
- Uses SSH to execute shutdown command
- Requires SSH to be enabled on NAS
- Fallback when API method fails
- Requires `sshpass` (included in container)

## Security Considerations

- **Use strong passwords**: Admin credentials are required
- **Network security**: Run on trusted networks only
- **Container security**: Runs as non-root user
- **Credential storage**: Use Docker secrets in production

## Troubleshooting

### Common Issues

1. **Login fails**: Check credentials and network connectivity
2. **API method not available**: Try SSH method with `--use-ssh`
3. **SSH connection fails**: Ensure SSH is enabled on NAS
4. **Permission denied**: Verify admin user has shutdown permissions

### Logs

The container provides detailed logging:
```bash
docker logs synology-shutdown
```

### Testing Connection

Test without shutdown:
```bash
# Check if you can reach the NAS
ping 192.168.1.100

# Test DSM web interface
curl -k https://192.168.1.100:5000
```

## Examples

### Web Interface Shutdown
```bash
# Start web interface
docker-compose up -d
# Open http://localhost:8080 and click shutdown button
```

### One-time CLI shutdown
```bash
docker run --rm \
  -e SYNOLOGY_HOST=192.168.1.100 \
  -e SYNOLOGY_USERNAME=admin \
  -e SYNOLOGY_PASSWORD=secret \
  synology-shutdown python synology_shutdown.py
```

### Scheduled shutdown (with cron)
```bash
# Add to crontab for daily 2 AM shutdown
0 2 * * * docker run --rm -e SYNOLOGY_HOST=192.168.1.100 -e SYNOLOGY_USERNAME=admin -e SYNOLOGY_PASSWORD=secret synology-shutdown python synology_shutdown.py
```

### With SSH fallback
```bash
docker run --rm \
  -e SYNOLOGY_HOST=192.168.1.100 \
  -e SYNOLOGY_USERNAME=admin \
  -e SYNOLOGY_PASSWORD=secret \
  -e USE_SSH=true \
  synology-shutdown python synology_shutdown.py
```

### Remote web access
```bash
# Bind to all interfaces for remote access
docker run --rm -p 0.0.0.0:8080:8080 \
  -e SYNOLOGY_HOST=192.168.1.100 \
  -e SYNOLOGY_USERNAME=admin \
  -e SYNOLOGY_PASSWORD=secret \
  synology-shutdown
# Access from any device at http://your-docker-host:8080
```

## Building from Source

```bash
git clone <this-repository>
cd synology-shutdown
docker build -t synology-shutdown .
```

## License

This project is provided as-is for educational and personal use.

## Disclaimer

Use at your own risk. Always test in a safe environment before using in production. The authors are not responsible for any data loss or system damage.