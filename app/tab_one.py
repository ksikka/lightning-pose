import asyncio
from typing import Any

from nicegui import ui


class TabOne:
    def __init__(self, link_url) -> None:
        self.container: Any = None
        self.card: Any = None
        self.i: int = 0
        self.is_running = False
        self.visibility = {"work_card": False}
        self.link_url = link_url

    def build(self):
        self.container = ui.element("div")
        with self.container:
            ui.label("Content One").classes("text-2xl")
            ui.button("do work", on_click=self.on_work_button_click)
            ui.link(self.link_url, self.link_url).classes("soft-link")
            c = ui.card()
            c.bind_visibility_from(self.visibility, "work_card")
            with c:
                ui.label().bind_text_from(self, "work_button_text")

    @property
    def work_button_text(self):
        return f"Work {self.i}"

    async def on_work_button_click(self):
        self.visibility["work_card"] = True
        if self.is_running:
            self.is_running = False
            return
        else:
            self.is_running = True

            for i in range(100):
                if not self.is_running:
                    break
                self.i += 1
                await asyncio.sleep(0.1)
