"""App command for the lightning-pose CLI."""

import os


def register_parser(subparsers):
    """Register the app command parser."""
    app_parser = subparsers.add_parser(
        "app",
        description="Start the lightning-pose web application.",
        usage="litpose app [OPTIONS]",
    )
    app_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the app on. Default is 8080.",
    )
    app_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the app on. Default is 127.0.0.1.",
    )


def handle(args):
    """Handle the app command."""
    # Set storage path before importing nicegui
    os.environ["NICEGUI_STORAGE_PATH"] = os.path.expanduser("~/.litpose")

    # Import lightning_pose modules only when needed
    from app.main import run_app

    # Run the app
    run_app(
        host=args.host,
        port=args.port,
    )
