# 🚌 MBTA Route 39 Bus Tracker

A modern, responsive Flask web application that provides real-time bus arrival predictions for MBTA Route 39 at Bynner Street. Features dual-direction tracking with visual emphasis on inbound buses, intelligent leave-time calculations, and a clean, mobile-friendly interface.

## 🌐 Live Demo

🚀 **View the live application running on Railway:** [https://bus-tracker-production-d668.up.railway.app/](https://bus-tracker-production-d668.up.railway.app/)

## ✨ Features

### 🚀 **Core Functionality**
- **Real-time Predictions**: Live bus arrival times using MBTA V3 API
- **Dual Direction Support**: Separate tracking for inbound and outbound buses
- **Smart Leave Times**: Optimized departure calculations based on 3-minute walk time and 5-minute max wait
- **30-Minute Timeline**: Visual status bars showing bus arrivals over the next 30 minutes
- **Bus Count Display**: Clear indication of how many buses are arriving in the next 30 minutes

### 🎨 **User Experience**
- **Visual Emphasis**: Inbound section prominently displayed, outbound section subtly muted
- **Color-Coded Timeline**: Gradient from green (immediate) to red (30 minutes) matching bus urgency
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Auto-Refresh**: Updates every 30 seconds for current information
- **Intuitive Status Messages**: "Leave Now!", "Leave Soon", or specific minute counts

### 🔧 **Technical Features**
- **RESTful API**: JSON endpoints for integration and development
- **Health Monitoring**: Built-in health checks and debugging endpoints
- **Docker Containerization**: Easy deployment with Docker Compose
- **Environment Configuration**: Flexible API key management
- **Error Handling**: Graceful fallbacks and user-friendly error messages

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone or download the project
git clone <repository-url>
cd bus_tracker

# (Optional) Get MBTA API key for higher rate limits
# Visit: https://api-v3.mbta.com/register
echo "MBTA_API_KEY=your_api_key_here" > .env

# Build and run in background
docker-compose up --build -d

# Access the application
open http://localhost:5000
```

### Option 2: Docker Build

```bash
# Build the image
docker build -t mbta-bus-tracker .

# Run with optional API key
docker run -p 5000:5000 \
  -e MBTA_API_KEY=your_key_here \
  -v $(pwd)/.env:/app/.env:ro \
  mbta-bus-tracker
```

### Option 3: Local Python Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable (optional)
export MBTA_API_KEY=your_api_key_here

# Run the application
python app.py

# Access at http://localhost:5000
```

## 📱 Usage

### Web Interface
- **Main Dashboard**: View real-time predictions for both directions
- **Status Bars**: Visual timeline showing bus positions over 30 minutes
- **Leave Times**: Smart calculations for when to depart
- **Bus Details**: Vehicle numbers and headsign information

### API Endpoints

#### `GET /` - Main Web Interface
Returns the full HTML dashboard with real-time predictions.

#### `GET /api/predictions` - JSON API
Returns structured prediction data:
```json
{
  "stop_name": "Bynner Street",
  "route": "39",
  "directions": {
    "inbound": {
      "stop_id": "1835",
      "stop_name": "S Huntington Ave @ Bynner St",
      "predictions": [...]
    },
    "outbound": {
      "stop_id": "51365",
      "stop_name": "S Huntington Ave @ Bynner St",
      "predictions": [...]
    }
  },
  "last_updated": "2024-01-15T10:30:00"
}
```

#### `GET /health` - Health Check
Returns service status for monitoring.

#### `GET /debug-predictions` - Debug Endpoint
Returns raw API data for troubleshooting (development only).

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MBTA_API_KEY` | MBTA V3 API key for higher rate limits | None | No |
| `MAX_PREDICTIONS` | Number of predictions to show per direction | 6 | No |

### Stop ID Configuration

The application automatically discovers the correct stop IDs for Bynner Street on Route 39. If you need to use different stops:

1. Find stop IDs: `https://api-v3.mbta.com/stops?filter[route]=39`
2. Update `BYNNER_STREET_STOP_ID` in `app.py`

## 🐳 Docker Management

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# Check status
docker-compose ps
```

## 🏗️ Architecture

### Application Structure
```
bus_tracker/
├── app.py                 # Flask application with MBTA API integration
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container build configuration
├── docker-compose.yml    # Multi-container orchestration
├── templates/
│   └── index.html        # Main dashboard template
├── static/
│   ├── style.css         # Responsive styling with visual emphasis
│   └── app.js           # Client-side functionality
└── README.md            # This file
```

### Key Components

#### Smart Leave Time Algorithm
```python
# User preferences
WALK_TIME_MINUTES = 3      # 3-minute walk to stop
MAX_WAIT_MINUTES = 5       # Maximum 5 minutes waiting
optimal_arrival_buffer = 2.5  # Arrive 2.5 min early

# Calculate optimal leave time
time_to_leave_minutes = max(0, minutes_away - WALK_TIME_MINUTES - optimal_arrival_buffer)
```

#### Visual Timeline System
- **30-minute window** with color gradient
- **Bus dots** positioned by arrival time
- **Radial gradients** matching timeline colors
- **Size differentiation** between inbound/outbound

## 🔌 MBTA API Integration

### API Details
- **Base URL**: `https://api-v3.mbta.com`
- **Rate Limits**: 1000/min (anonymous), higher with API key
- **Real-time Updates**: ~12-second intervals
- **Documentation**: [MBTA V3 API Docs](https://api-v3.mbta.com/docs/swagger)

### Data Sources
- **Predictions**: Real-time arrival/departure times
- **Stops**: Automatic stop ID discovery
- **Vehicles**: Bus numbers and status
- **Trips**: Route and headsign information

## 📊 Monitoring & Debugging

### Health Checks
```bash
# Health endpoint
curl http://localhost:5000/health

# API status
curl http://localhost:5000/api/predictions

# Debug information
curl http://localhost:5000/debug-predictions
```

### Logs
```bash
# View application logs
docker-compose logs -f mbta-bus-tracker

# Filter for errors
docker-compose logs | grep ERROR
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug mode
FLASK_ENV=development python app.py

# Test API endpoints
curl localhost:5000/api/predictions | jq
```

## 📄 License

This project is open source. Please check the license file for details.

## 🙏 Acknowledgments

- **MBTA** for providing the V3 API
- **Flask** framework for the web application
- **Docker** for containerization
- **Bootstrap/CSS Grid** for responsive design

## 🐛 Troubleshooting

### Common Issues

**"No predictions found"**
- Check MBTA API status
- Verify stop IDs are correct
- Ensure network connectivity

**"Container won't start"**
- Check Docker logs: `docker-compose logs`
- Verify port 5000 is available
- Ensure `.env` file permissions

**"Stale data"**
- Check auto-refresh is working
- Verify MBTA API key if using high-frequency updates
- Clear browser cache

### Support
- Check the [MBTA API status](https://www.mbta.com/developers/api-status)
- Review application logs for error details
- Test with the debug endpoint for raw API responses

---

**Last Updated**: April 3, 2026
**Version**: 2.0.0

## Troubleshooting

**No predictions showing?**
- Check if the Route 39 bus is currently running (service hours)
- Verify the stop ID is correct for your desired direction
- Check if there are any MBTA service alerts

**API errors?**
- The app works without an API key but has lower rate limits
- Get a free API key at https://api-v3.mbta.com/register for better reliability

**Wrong stop or direction?**
- The app searches for "Bynner" in stop names - you may need to adjust the search term
- Check the `direction_id` parameter (0=outbound, 1=inbound)

## Files Included

- `Dockerfile` - Container configuration
- `docker-compose.yml` - Easy deployment setup
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `.env` - Environment variables template
- `templates/index.html` - Main HTML template
- `static/style.css` - CSS styles
- `static/app.js` - JavaScript functionality
- `README.md` - This documentation

## License

MIT License - feel free to modify and use for your own transit tracking needs!