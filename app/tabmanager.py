import re
from typing import Callable, Dict, Union, Coroutine
from typing import Protocol

from nicegui import background_tasks, helpers, ui


class _TabManagerComponent(ui.element, component="js/tab_manager.js"):
    pass


class Tab(Protocol):
    def build(self) -> Coroutine | None:
        pass


class TabManager:
    content: ui.element = None
    tabs: Dict[str, Tab] = None

    def __init__(self) -> None:
        self.tabs: Dict[str, Tab] = {}
        self.patterns: Dict[str, Callable[[str], Tab]] = {}

    def add_tab(self, path: str, obj: Tab):
        # All pages are prefixed by /p/ to allow for other routes to
        # co-exist, such as /_nicegui/auto routes needed when using ui.image.
        assert path.startswith("/p/")
        self.tabs[path] = obj

    def add_pattern_tab(self, pattern: str, factory: Callable[[str], Tab]):
        """Add a tab that matches a URL pattern.

        Args:
            pattern: URL pattern with :param_name placeholders
            factory: Function that creates a tab instance with the extracted parameters
        """
        assert pattern.startswith("/p/")
        self.patterns[pattern] = factory

    def _match_pattern(self, path: str) -> tuple[Callable[[str], Tab], Dict[str, str]]:
        """Match a path against registered patterns.

        Returns:
            Tuple of (factory, params) if matched, (None, None) otherwise
        """
        for pattern, factory in self.patterns.items():
            # Convert pattern to regex, replacing :param with (?P<param>[^/?&#]+)
            # This matches any character except /, ?, &, and # which have special meaning in URLs
            regex_pattern = re.sub(r":(\w+)", r"(?P<\1>[^/?&#]+)", pattern)
            match = re.match(regex_pattern, path)
            if match:
                return factory, match.groupdict()
        return None, None

    async def switch_tab(self, target: str) -> None:
        path = target

        # Check for pattern match first
        factory, params = self._match_pattern(path)
        if factory:
            tab = factory(**params)
        else:
            # Fall back to exact match
            tab = self.tabs[target]

        # Add new tab to history if we're indeed changing the path.
        # noinspection PyAsyncCall
        ui.run_javascript(
            f"""
            if (window.location.pathname !== "{path}") {{
                history.pushState({{page: "{path}"}}, "", "{path}");
            }}
        """
        )

        self.content.clear()
        with self.content:
            maybe_coroutine = tab.build()
            if maybe_coroutine is not None:
                await maybe_coroutine

    def build(self):
        self.content = _TabManagerComponent().classes("w-full p-4 bg-gray-100")
        # Listen for navigation events from the UI, like forward, back button.
        self.content.on("switch_tab", lambda e: self.switch_tab(e.args))
