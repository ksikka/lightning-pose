"""Command modules for the lightning-pose CLI."""

from . import app, crop, predict, remap, train, nicegui_app

# List of all available commands
COMMANDS = {
    "train": train,
    "predict": predict,
    "crop": crop,
    "remap": remap,
    "app": app,
    "nicegui_app": nicegui_app,
}
