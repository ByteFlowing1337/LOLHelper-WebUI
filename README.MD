# LCU-UI

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-red.svg)](https://flask.palletsprojects.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern, lightweight web interface for League of Legends Client automation and match analysis.

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Usage](#usage) • [Contributing](#contributing)

</div>

---

## ✨ Features

### 🎮 **Auto-Accept Queue**

Automatically accept match queue pop-ups when enabled via the web interface.

### 📊 **Match History & Analysis**

- View detailed match history with rich statistics
- Champion performance breakdown (KDA, CS, gold, damage)
- Real-time rank information display
- Integration with official Data Dragon for champion metadata

### 🔴 **Live Game Monitoring**

- Real-time spectator view of ongoing matches
- Team composition analysis
- Player statistics and champion picks

### 🌐 **External Stats Integration**

- Fetches champion statistics from public APIs
- Displays win rates, pick rates, and tier rankings
- Cached data for improved performance

### ⚡ **WebSocket Real-time Updates**

- Live connection status monitoring
- Instant notifications for game state changes
- Server-client synchronization via Socket.IO

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 or higher**
- **League of Legends Client** (for LCU API access)
- **uv** (recommended) or pip for package management

### Installation with uv (Recommended)

```powershell
# Install uv if you haven't already
# Visit: https://github.com/astral-sh/uv

# Clone the repository
git clone https://github.com/ByteFlowing1337/LCU-UI.git
cd LCU-UI

# Install dependencies
uv sync

# Run the application
uv run app.py
```

### Installation with pip

```powershell
# Clone the repository
git clone https://github.com/ByteFlowing1337/LCU-UI.git
cd LCU-UI

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Run the application
python app.py
```

---

## 📖 Usage

### Starting the Server

```powershell
# With uv
uv run app.py

# Or with Python directly
python app.py
```

The server will automatically:

1. Detect your local IP address
2. Start on `http://0.0.0.0:5000`
3. Open your default browser to the interface

### Web Interface

Once running, navigate to the displayed URL (typically `http://localhost:5000`) to access:

- **Home Page**: Quick navigation to all features
- **Summoner Search**: Look up player profiles and match history
- **Live Game**: Monitor ongoing matches
- **Settings**: Enable/disable auto-accept and other features

### LCU Connection

The application automatically detects the League Client and establishes a connection when:

- League of Legends client is running
- You are logged into an account
- LCU API is accessible

Connection status is displayed in the web interface.

---

## 🛠️ Development

### Project Structure

```
LCU-UI/
├── app.py                 # Main Flask application
├── config.py              # Configuration and app state
├── constants.py           # Game constants and data loaders
├── pyproject.toml         # Project metadata and dependencies
├── core/                  # Core LCU integration
│   └── lcu/              # LCU API client modules
├── routes/                # Flask route blueprints
│   ├── api_routes.py     # API endpoints
│   ├── page_routes.py    # Page rendering routes
│   └── data_routes.py    # Data endpoints
├── services/              # Business logic services
│   ├── match_service.py  # Match processing
│   ├── opgg_service.py   # External stats integration
│   ├── auto_accept.py    # Auto-accept functionality
│   └── auto_analyze.py   # Player analysis
├── websocket/             # Socket.IO event handlers
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JS, images
└── data/                  # JSON data files
```

### Development Tools

Install development dependencies:

```powershell
pip install -e ".[dev]"
```

This includes:

- **black** - Code formatter
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

### Running Tests

```powershell
pip install -e ".[test]"
pytest
```

---

## 🔧 Configuration

### Environment Variables

- `HOST` - Server bind address (default: `0.0.0.0`)
- `PORT` - Server port (default: `5000`)
- `PUBLIC_HOST` - Override auto-detected public IP

### Data Dragon Integration

Champion metadata is automatically fetched from Riot's Data Dragon CDN:

- Latest version detection
- Champion information (names, titles, tags)
- Cached for performance

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Guidelines

- Follow PEP 8 style guidelines
- Use `black` for code formatting
- Add tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This project is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc.

Use at your own risk. This tool is for educational and personal use only.

---

<div align="center">

**Made with ❤️ by [ByteFlowing1337](https://github.com/ByteFlowing1337)**

[⬆ Back to Top](#lcu-ui)

</div>
