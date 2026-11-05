import sys

def main():
    if "--api" in sys.argv:
        from api.http_server import main as start_api

        start_api()
    else:
        from cli.main import main as start_cli

        start_cli()

if __name__ == "__main__":
    main()
