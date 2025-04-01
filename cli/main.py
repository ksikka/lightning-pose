from __future__ import annotations

import sys

from . import friendly
from .commands import COMMANDS


def _build_parser():
    parser = friendly.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Litpose command to run.",
        parser_class=friendly.ArgumentSubParser,
    )

    # Dynamically register all available commands
    for name, module in COMMANDS.items():
        module.register_parser(subparsers)

    return parser


def main():
    parser = _build_parser()

    # If no commands provided, display the help message.
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Get the command handler dynamically
    command_handler = COMMANDS[args.command].handle

    # Execute the command
    command_handler(args)


# No if __name__ == "__main__" guard:
# https://github.com/zauberzeug/nicegui/issues/181#issuecomment-1328638810
print("hello")
import os
import sys

# Get the current process ID
pid = os.getpid()

# Get the list of command line arguments (sys.argv[0] is the script name)
command_args = sys.argv

# Join the arguments into a single string to represent the command
command_str = ' '.join(command_args)

# Print the PID
print(f"PID: {pid}")

# Print the command used to execute the script
print(f"Command: {command_str}")
main()
