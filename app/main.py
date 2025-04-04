#!/usr/bin/env python3
import os

# Override storage path before importing nicegui.
os.environ["NICEGUI_STORAGE_PATH"] = os.path.expanduser("~/.lightning-pose")

import logging

from nicegui import ui, app, run, background_tasks

from . import tab_one
from . import tabs
from .tabmanager import TabManager
from . import config
from .services.job_manager import JobManager




# Root and all pages will return the "single-page-app".
# All pages are prefixed by /p/ to allow for other routes to
# co-exist, such as /_nicegui/auto routes needed when using ui.image.
@ui.page("/")
@ui.page("/p/{path}")
def main():
    # Generated using https://quasar.dev/style/theme-builder UMD Export
    app.config.quasar_config.update({
        "brand": {
            "primary": '#7c5ed6',
            "secondary": '#26A69A',
            "accent": '#9C27B0',

            "dark": '#1d1d1d',
            'dark-page': '#121212',

            "positive": '#21BA45',
            "negative": '#ed6878',
            "info": '#31CCEC',
            "warning": '#f2d038',
        }
    })
    # Copied from RTD Theme.
    ui.add_css("""
    @font-face {
        font-family: Lato;
        src: url(/css/fonts/lato-normal.woff2) format("woff2"),url(fonts/lato-normal.woff) format("woff");
        font-weight: 400;
        font-style: normal;
        font-display: block
    }
    body {
        font-family: Lato,proxima-nova,Helvetica Neue,Arial,sans-serif;);
    }""")
    app.add_static_files('/css/fonts', config.app_root / 'css'/ 'fonts')

    tab_manager = TabManager()
    tab_manager.add_tab("/p/home", tabs.home.Home())
    tab_manager.add_tab("/p/models", tabs.models.Models())
    tab_manager.add_tab("/p/jobs", tabs.jobs.Jobs())
    tab_manager.add_tab("/p/tensorboard", tabs.tensorboard.TensorBoard())
    tab_manager.add_tab("/p/faketab", tab_one.TabOne("/p/models"))

    # adding some navigation buttons to switch between the different pages
    with ui.header():
        # ui.image("img/LightningPose_horizontal_light.webp")
        # replace= removes the default .nicegui-link which made the link blue and underlined.
        ui.link("Home", "/p/home").classes(replace="text-lg text-white soft-link")
        ui.link("Models", "/p/models").classes(replace="text-lg text-white soft-link")
        ui.link("Jobs", "/p/jobs").classes(replace="text-lg text-white soft-link")
        ui.link("TensorBoard", "/p/tensorboard").classes(replace="text-lg text-white soft-link")
        ui.link("TestTab", "/p/faketab").classes(replace="text-lg text-white soft-link")

    # this places the content which should be displayed
    tab_manager.build()


app.on_startup(lambda: print('Lightning Pose App running:', next(iter(app.urls))))


def start_tensorboard():
    """Start TensorBoard as a managed job."""
    job_manager = JobManager()
    job_manager.start_job("tensorboard", "tensorboard --logdir /home/ksikka/synced/outputs --port 6007")
    print("TensorBoard started as a managed job")


app.on_startup(lambda: background_tasks.create(run.io_bound(start_tensorboard)))



def run_app(
        host="0.0.0.0",
        port=8080,
        reload=False,
):
    ui.run(
        host=host,
        port=port,
        reload=reload,
        #uvicorn_logging_level=logging.DEBUG,
        prod_js=False,
        title="Lightning Pose",
        favicon=config.app_root / "img/favicon.ico",
        show_welcome_message=False,
    )


if __name__ in ("__main__", "__mp_main__"):
    run_app(reload=True)
