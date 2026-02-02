import uvicorn
import pathlib

if __name__ == "__main__":
    cwd = pathlib.Path(__file__).parent.resolve()
    uvicorn.run(
        app='API.main:app',
        log_config=f"{cwd}/log.ini",
        host='0.0.0.0',
        port=8450,
        'check'
    )
