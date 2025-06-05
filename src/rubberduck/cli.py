#!/usr/bin/env python3
"""
CLI entry point for Rubberduck LLM Caching Proxy Server
"""

import argparse
import sys
import uvicorn
from .main import app


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Rubberduck LLM Caching Proxy Server")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level", 
        choices=["debug", "info", "warning", "error"], 
        default="info",
        help="Logging level (default: info)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Rubberduck server on {args.host}:{args.port}")
    print(f"Documentation available at http://{args.host}:{args.port}/docs")
    
    try:
        uvicorn.run(
            "rubberduck.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\nShutting down Rubberduck server...")
        sys.exit(0)


if __name__ == "__main__":
    main()