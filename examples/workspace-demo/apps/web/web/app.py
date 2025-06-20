#!/usr/bin/env python3
"""Web application using workspace packages."""

from pathlib import Path

from core import hello
from utils import validate


def serve():
    """Start the production web server."""
    print("🌐 Starting Demo Web Server (Production)")
    print("=" * 40)

    print("\nLoading workspace packages...")
    hello()

    print("\nServer configuration:")
    print("  Host: 0.0.0.0")
    print("  Port: 8000")
    print("  Mode: Production")
    print(f"  Location: {Path(__file__).parent.parent}")

    print("\nPress Ctrl+C to stop the server")
    print("\n[Simulated server running...]")

    # In a real app, this would start Flask/FastAPI
    try:
        import time

        time.sleep(2)
        print("\n✅ Server stopped gracefully")
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped by user")

    return 0


def dev_server():
    """Start the development web server with hot reload."""
    print("🔧 Starting Demo Web Server (Development)")
    print("=" * 40)

    print("\nDevelopment mode features:")
    print("  ✓ Hot reload enabled")
    print("  ✓ Debug mode active")
    print("  ✓ Detailed error pages")

    print("\nValidating configuration...")
    validate()

    print("\nServer configuration:")
    print("  Host: 127.0.0.1")
    print("  Port: 5000")
    print("  Mode: Development")
    print(f"  Location: {Path(__file__).parent.parent}")

    print("\n🚀 Development server ready!")
    return 0


if __name__ == "__main__":
    serve()
