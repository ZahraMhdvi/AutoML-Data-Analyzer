

import argparse

import uvicorn


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="AutoML Data Analyzer server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="restart automatically when code changes")
    args = parser.parse_args()

    shown_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    print(f"\n  AutoML Data Analyzer -> http://{shown_host}:{args.port}\n")

    uvicorn.run("api.main:app", host=args.host, port=args.port, reload=args.reload)
