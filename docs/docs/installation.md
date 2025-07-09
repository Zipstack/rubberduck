# Installation

Get Rubberduck up and running in just a few minutes with this step-by-step installation guide.

## Prerequisites

Before installing Rubberduck, ensure you have:

- **Python 3.11+** - Required for the backend server
- **Node.js 18+** - Required for the frontend interface
- **Git** - For cloning the repository

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/rubberduck.git
cd rubberduck
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

#### Initialize Database

```bash
# Initialize the SQLite database
python -c "
import asyncio
from src.rubberduck.database import init_db
asyncio.run(init_db())
"
```

### 3. Start Backend Server

```bash
# Start the backend server
python run.py

# Or with custom host/port
python run.py --host 0.0.0.0 --port 8000
```

The backend will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### 4. Frontend Setup

Open a new terminal window/tab and navigate to the frontend directory:

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

## First Login

Once both servers are running:

1. Open your browser and navigate to **http://localhost:5173**
2. You'll see the login page
3. Use the default admin credentials:
   - **Email**: `admin@example.com`
   - **Password**: `admin`

<div className="screenshot">

![Dashboard Overview](/img/dashboard-overview.png)

</div>

After logging in, you'll see the main dashboard with real-time metrics and proxy status.

## Verification

To verify your installation is working correctly:

### Check Backend Health

```bash
curl http://localhost:8000/healthz
```

You should receive a response like:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "connected",
  "running_proxies": 0
}
```

### Check Frontend Access

Navigate to http://localhost:5173 and verify you can:
- Log in with the default credentials
- See the dashboard with metrics cards
- Navigate between different pages (Dashboard, Proxies, Logs, Settings)

## Environment Configuration

### Backend Configuration

The backend can be configured using environment variables:

```bash
# Optional: Set custom database path
export DATABASE_URL="sqlite:///./data/rubberduck.db"

# Optional: Configure CORS settings
export FRONTEND_URL="http://localhost:5173"

# Optional: Set custom port
export PORT="8000"
```

### Frontend Configuration

For frontend configuration, you can modify settings in the frontend directory:

```bash
# frontend/.env.local (create if needed)
VITE_API_BASE_URL=http://localhost:8000
```

## Production Deployment

For production deployments, consider:

### Backend Production Setup

```bash
# Install production ASGI server
pip install gunicorn[gevent]

# Run with gunicorn
gunicorn src.rubberduck.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Production Build

```bash
cd frontend

# Build for production
npm run build

# Serve static files (or use your preferred web server)
npm run preview
```

## Docker Setup (Optional)

If you prefer using Docker, you can use the provided `docker-compose.yml`:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

This will start both backend and frontend services with proper networking configured.

## Troubleshooting

### Common Issues

**Port conflicts**: If ports 8000 or 5173 are already in use, you can:
- Change the backend port: `python run.py --port 8001`
- Change the frontend port: `npm run dev -- --port 5174`

**Database permissions**: Ensure the `data/` directory is writable:
```bash
mkdir -p data
chmod 755 data
```

**Python version**: Verify you're using Python 3.11+:
```bash
python --version
```

**Node.js version**: Verify you're using Node.js 18+:
```bash
node --version
```

### Getting Help

If you encounter issues:
1. Check the troubleshooting section in our advanced docs
2. Review the backend logs for error messages
3. Ensure all prerequisites are installed correctly
4. Verify firewall settings aren't blocking the required ports

## Next Steps

Now that Rubberduck is installed, you're ready to:

1. **[Create your first proxy](/usage/creating-proxies)** - Set up a connection to your favorite LLM provider
2. **[Learn about proxy management](/usage/managing-proxies)** - Start, stop, and configure your proxies
3. **[Explore the monitoring features](/logging)** - Track requests and analyze performance

---

🎉 **Congratulations!** You now have Rubberduck running locally. Time to create your first LLM proxy!