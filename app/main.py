#!/usr/bin/env python3
from __future__ import annotations

import os
import logging
from pathlib import Path

# Override storage path before importing nicegui.
os.environ["NICEGUI_STORAGE_PATH"] = os.path.expanduser("~/.lightning-pose")

from nicegui import ui, app, background_tasks, run

from . import tab_one
from . import tabs
from .tabmanager import TabManager
from . import config
from .services.job_manager import JobManager
from .tabs.models import Models
from .tabs.model_details import ModelDetails
from .tabs.settings import Settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_header():
    # justify-between maximizes space between the children,
    # so first div goes on the left, second div on the right.
    with ui.header().classes("justify-between no-wrap"):
        with ui.row():
            # ui.image("img/LightningPose_horizontal_light.webp")
            # replace= removes the default .nicegui-link which made the link blue and underlined.
            ui.link("Home", "/p/home").classes(replace="text-lg text-white soft-link")
            ui.link("Models", "/p/models").classes(
                replace="text-lg text-white soft-link active"
            )
            ui.link("Tensorboard", "/p/tensorboard").classes(
                replace="text-lg text-white soft-link"
            )
            ui.link("Jobs", "/p/jobs").classes(
                replace="text-lg text-white soft-link"
            )


# Root and all pages will return the "single-page-app".
# All pages are prefixed by /p/ to allow for other routes to
# co-exist, such as /_nicegui/auto routes needed when using ui.image.
@ui.page("/")
@ui.page("/p/{path:path}")
def main():
    # Hack: Provides omegaconf interpolation for LP_ROOT_PATH
    import lightning_pose
    from lightning_pose.cli.commands import predict
    from lightning_pose.api.model import Model as CoreModel

    # Generated using https://quasar.dev/style/theme-builder UMD Export
    app.config.quasar_config.update(
        {
            "brand": {
                "primary": "#7c5ed6",
                "secondary": "#26A69A",
                "accent": "#9C27B0",
                "dark": "#1d1d1d",
                "dark-page": "#121212",
                "positive": "#21BA45",
                "negative": "#ed6878",
                "info": "#31CCEC",
                "warning": "#f2d038",
            }
        }
    )
    # Copied from RTD Theme.
    ui.add_css(
        """
    @font-face {
        font-family: Lato;
        src: url(/css/fonts/lato-normal.woff2) format("woff2"),url(fonts/lato-normal.woff) format("woff");
        font-weight: 400;
        font-style: normal;
        font-display: block
    }
    body {
        font-family: Lato,proxima-nova,Helvetica Neue,Arial,sans-serif;);
    }
    header a.active {
        border-bottom: 2px white solid;
    }
    """
    )
    app.add_static_files("/css/fonts", config.app_root / "css" / "fonts")

    # Create tab manager
    tab_manager = TabManager()
    tab_manager.add_tab("/p/home", tabs.home.Home())
    tab_manager.add_tab("/p/models", tabs.models.Models())
    tab_manager.add_pattern_tab(
        "/p/model/:model_name", lambda model_name: ModelDetails(model_name)
    )
    tab_manager.add_tab("/p/jobs", tabs.jobs.Jobs())
    tab_manager.add_tab("/p/tensorboard", tabs.tensorboard.TensorBoard())
    tab_manager.add_tab("/p/faketab", tab_one.TabOne("/p/models"))
    tab_manager.add_tab("/p/labeling", tabs.labeling.Labeling()

    tab_manager.add_tab("/p/settings", tabs.settings.Settings())
    _build_header()

    # this places the content which should be displayed
    tab_manager.build()


app.on_startup(lambda: print("Lightning Pose App running:", next(iter(app.urls))))


def start_tensorboard():
    """Start TensorBoard as a managed job."""
    job_manager = JobManager()
    job_manager.start_job(
        "tensorboard", "tensorboard --logdir /home/ksikka/synced/outputs --port 6007"
    )
    print("TensorBoard started as a managed job")


debug = False
def _start_tensorboard():
    # Don't start tensorboard if running dev server from 'python -m app.main'
    if not debug:
        background_tasks.create(run.io_bound(start_tensorboard))
app.on_startup(_start_tensorboard)


def run_app(
    host="0.0.0.0",
    port=8080,
    reload=False,
):
    global debug
    debug=True
    ui.run(
        host=host,
        port=port,
        reload=reload,
        # uvicorn_logging_level=logging.DEBUG,
        prod_js=False,
        title="Lightning Pose",
        favicon=config.app_root / "img/favicon.ico",
        show_welcome_message=False,
        uvicorn_reload_includes="*.py,*.vue", # include vue files
    )


if __name__ in ("__main__", "__mp_main__"):
    run_app(reload=True)
