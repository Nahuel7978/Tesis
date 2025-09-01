import uvicorn
from pathlib import Path

if __name__ == "__main__":
    current_dir = Path(__file__).parent
    uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            reload_excludes=[
                str(current_dir / "Storage"),
                #str(current_dir / "Services"),
                str(current_dir / "logs"),
                str(current_dir / "enviroment_api"),
                "**/__pycache__",
                "**/*.pyc",
                "**/*.log"
            ]
        )