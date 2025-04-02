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

    def add_tab(self, path: str, obj: Tab):
        # All pages are prefixed by /p/ to allow for other routes to
        # co-exist, such as /_nicegui/auto routes needed when using ui.image.
        assert path.startswith("/p/")
        self.tabs[path] = obj

    async def switch_tab(self, target: str) -> None:
        path = target
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
