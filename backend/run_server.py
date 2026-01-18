#!/usr/bin/env python3
"""Run the FastAPI server."""
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    """Run the server."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
