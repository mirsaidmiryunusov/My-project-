#!/usr/bin/env python3
"""
AI Call Center Demo Runner

This script sets up and runs the AI Call Center demo system.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlmodel
        import redis
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False


def setup_database():
    """Initialize the database with sample data."""
    print("🗄️ Setting up database...")
    
    try:
        # Remove existing database for clean start
        db_file = Path("ai_call_center.db")
        if db_file.exists():
            db_file.unlink()
            print("🗑️ Removed existing database")
        
        # Run database initialization
        subprocess.check_call([sys.executable, "init_db.py"])
        print("✅ Database setup completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
        return False


def start_redis():
    """Start Redis server if not running."""
    print("🔴 Checking Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is already running")
        return True
    except:
        print("⚠️ Redis not available - some features may not work")
        print("💡 To install Redis:")
        print("   - Ubuntu/Debian: sudo apt-get install redis-server")
        print("   - macOS: brew install redis")
        print("   - Windows: Download from https://redis.io/download")
        return False


def run_server():
    """Start the FastAPI server."""
    print("🚀 Starting AI Call Center server...")
    
    try:
        # Change to the correct port for the demo environment
        port = 12000  # Use the first available port from the runtime info
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ]
        
        print(f"🌐 Server will be available at:")
        print(f"   Local: http://localhost:{port}")
        print(f"   Network: https://work-1-fqxtxkhgfydowkzs.prod-runtime.all-hands.dev")
        print(f"   Admin Panel: https://work-1-fqxtxkhgfydowkzs.prod-runtime.all-hands.dev/static/admin.html")
        print(f"   API Docs: https://work-1-fqxtxkhgfydowkzs.prod-runtime.all-hands.dev/docs")
        print("\n📋 Demo Credentials:")
        print("   Admin Email: admin@demo.com")
        print("   Admin Password: admin123")
        print("\n🛑 Press Ctrl+C to stop the server")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")


def main():
    """Main demo runner."""
    print("🤖 AI Call Center Demo Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Check Redis (optional)
    start_redis()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed! Starting server...")
    print("=" * 50)
    
    # Start server
    run_server()


if __name__ == "__main__":
    main()