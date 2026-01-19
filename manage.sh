#!/bin/bash

# Douyin Analytics Platform Management Script
# Uses xvfb virtual display for server-side QR code scanning

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_msg "$RED" "Error: $1 is not installed"
        return 1
    fi
    return 0
}

# Check prerequisites
check_prerequisites() {
    print_msg "$BLUE" "Checking prerequisites..."

    local missing=0

    # Check Python
    if ! check_command python3; then
        missing=1
    fi

    # Check Node.js
    if ! check_command node; then
        missing=1
    fi

    # Check xvfb-run (for server-side QR scanning)
    if ! check_command xvfb-run; then
        print_msg "$YELLOW" "Warning: xvfb-run not found. Server-side QR scanning may not work."
        print_msg "$YELLOW" "Install with: sudo apt-get install xvfb"
    fi

    if [ $missing -eq 1 ]; then
        print_msg "$RED" "Please install missing dependencies first"
        exit 1
    fi

    print_msg "$GREEN" "Prerequisites check passed"
}

# Start backend with xvfb (for QR code scanning support)
start_backend() {
    print_msg "$BLUE" "Starting backend with xvfb virtual display..."

    cd "$BACKEND_DIR"

    # Check if xvfb-run is available
    if command -v xvfb-run &> /dev/null; then
        print_msg "$GREEN" "Using xvfb for virtual display support"
        # Start with xvfb-run for non-headless browser support
        xvfb-run -a --server-args="-screen 0 1920x1080x24" python3 run.py &
    else
        print_msg "$YELLOW" "xvfb not available, starting without virtual display"
        print_msg "$YELLOW" "Server-side QR code scanning may not work correctly"
        python3 run.py &
    fi

    BACKEND_PID=$!
    echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"
    print_msg "$GREEN" "Backend started (PID: $BACKEND_PID)"
}

# Start backend without xvfb (headless mode)
start_backend_headless() {
    print_msg "$BLUE" "Starting backend in headless mode..."

    cd "$BACKEND_DIR"
    python3 run.py &

    BACKEND_PID=$!
    echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"
    print_msg "$GREEN" "Backend started in headless mode (PID: $BACKEND_PID)"
}

# Start frontend
start_frontend() {
    print_msg "$BLUE" "Starting frontend..."

    cd "$FRONTEND_DIR"

    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_msg "$YELLOW" "Installing frontend dependencies..."
        npm install
    fi

    npm run dev &

    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"
    print_msg "$GREEN" "Frontend started (PID: $FRONTEND_PID)"
}

# Stop all services
stop_all() {
    print_msg "$BLUE" "Stopping all services..."

    # Stop backend
    if [ -f "$SCRIPT_DIR/.backend.pid" ]; then
        BACKEND_PID=$(cat "$SCRIPT_DIR/.backend.pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_msg "$GREEN" "Backend stopped"
        fi
        rm -f "$SCRIPT_DIR/.backend.pid"
    fi

    # Stop frontend
    if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
        FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_msg "$GREEN" "Frontend stopped"
        fi
        rm -f "$SCRIPT_DIR/.frontend.pid"
    fi

    # Also try to kill any remaining processes
    pkill -f "python3 run.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true

    print_msg "$GREEN" "All services stopped"
}

# Start all services
start_all() {
    check_prerequisites
    stop_all

    print_msg "$BLUE" "Starting all services..."

    start_backend
    sleep 2  # Wait for backend to initialize
    start_frontend

    print_msg "$GREEN" "All services started!"
    print_msg "$BLUE" "Backend: http://localhost:8000"
    print_msg "$BLUE" "Frontend: http://localhost:5173"
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "QR Code Scanning: The backend now uses xvfb for virtual display,"
    print_msg "$YELLOW" "which enables server-side QR code scanning with anti-detection."
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "Press Ctrl+C to stop all services"

    # Wait for interrupt
    wait
}

# Install dependencies
install_deps() {
    print_msg "$BLUE" "Installing dependencies..."

    # Backend dependencies
    print_msg "$YELLOW" "Installing backend dependencies..."
    cd "$BACKEND_DIR"
    pip3 install -r requirements.txt

    # Install Playwright browsers
    print_msg "$YELLOW" "Installing Playwright browsers..."
    playwright install chromium

    # Frontend dependencies
    print_msg "$YELLOW" "Installing frontend dependencies..."
    cd "$FRONTEND_DIR"
    npm install

    print_msg "$GREEN" "All dependencies installed!"
}

# Show status
show_status() {
    print_msg "$BLUE" "Service Status:"

    # Check backend
    if [ -f "$SCRIPT_DIR/.backend.pid" ]; then
        BACKEND_PID=$(cat "$SCRIPT_DIR/.backend.pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_msg "$GREEN" "Backend: Running (PID: $BACKEND_PID)"
        else
            print_msg "$RED" "Backend: Not running (stale PID file)"
        fi
    else
        print_msg "$RED" "Backend: Not running"
    fi

    # Check frontend
    if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
        FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_msg "$GREEN" "Frontend: Running (PID: $FRONTEND_PID)"
        else
            print_msg "$RED" "Frontend: Not running (stale PID file)"
        fi
    else
        print_msg "$RED" "Frontend: Not running"
    fi
}

# Show help
show_help() {
    echo "Douyin Analytics Platform Management Script"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start         Start all services (backend with xvfb + frontend)"
    echo "  start-backend Start backend only (with xvfb virtual display)"
    echo "  start-headless Start backend in headless mode (no xvfb)"
    echo "  start-frontend Start frontend only"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  status        Show service status"
    echo "  install       Install all dependencies"
    echo "  help          Show this help message"
    echo ""
    echo "Notes:"
    echo "  - Backend uses xvfb for virtual display to support server-side QR scanning"
    echo "  - Make sure xvfb is installed: sudo apt-get install xvfb"
    echo "  - Playwright browsers must be installed: playwright install chromium"
}

# Main command handler
case "$1" in
    start)
        start_all
        ;;
    start-backend)
        check_prerequisites
        start_backend
        ;;
    start-headless)
        check_prerequisites
        start_backend_headless
        ;;
    start-frontend)
        check_prerequisites
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 1
        start_all
        ;;
    status)
        show_status
        ;;
    install)
        install_deps
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_msg "$RED" "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
