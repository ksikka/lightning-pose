import os
from dataclasses import dataclass
import time
from pathlib import Path
from typing import Optional
import asyncio
import logging
from omegaconf import OmegaConf, DictConfig, ListConfig
from .. import config
from nicegui import run

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_TYPE_MAP = {
    "heatmap": "Heatmap",
    "heatmap_mhcrnn": "Context",
}


@dataclass
class Model:
    name: str  # Model's path relative to config.model_dir
    creation_timestamp: float
    creation_timestamp_fmt: str
    _config: Optional[DictConfig] = None
    model_type: Optional[str] = None
    display_model_arch: str = ""
    losses_to_use: list | None = None
    display_losses_to_use: str = ""
    display_model_type: str = ""

    def __setattr__(self, name: str, value: any) -> None:
        """Override to update derived attributes when base attributes change."""
        super().__setattr__(name, value)
        if name == "_config" and value is not None:
            # Update properties when config is loaded
            self.model_type = self._config.model.model_type
            self.losses_to_use = list(self._config.model.losses_to_use)

        if name == "model_type":
            # Update display_model_type whenever _model_type changes
            self.display_model_arch = MODEL_TYPE_MAP.get(value, value or "")

        if name == "losses_to_use":
            # Update display_model_type whenever _model_type changes
            self.display_losses_to_use = ", ".join(value) if value is not None else ""

        if name in ("model_type", "losses_to_use"):
            self.display_model_type = (
                "Supervised" if not self.display_losses_to_use else "Unsupervised"
            )
            self.display_model_type += (
                " " + self.display_model_arch
                if self.model_type == "heatmap_mhcrnn"
                else ""
            )

    @property
    async def async_config(self) -> Optional[DictConfig]:
        """Load the model's config file asynchronously if not already loaded."""
        if self._config is None:
            config_path = Path(config.model_dir) / self.name / "config.yaml"
            try:
                self._config = await run.io_bound(OmegaConf.load, config_path)
            except Exception as e:
                logger.warning(f"Failed to load config for model {self.name}: {e}")

        return self._config

    @classmethod
    def list(cls):
        """Recursively find all Lightning Pose model directories by looking for config.yaml files."""
        file_info = []
        model_dir = Path(config.model_dir)

        # Use os.walk to get all files in one pass
        for root, _, files in os.walk(model_dir):
            # Only process directories that contain config.yaml
            if "config.yaml" in files:
                root_path = Path(root)
                config_path = root_path / "config.yaml"

                # Get creation time in a single stat call
                stat = config_path.stat()
                try:
                    creation_timestamp = stat.st_birthtime
                except AttributeError:
                    creation_timestamp = stat.st_ctime

                creation_timestamp_fmt = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(creation_timestamp)
                )

                # Get relative path from model_dir to use as name
                relative_path = root_path.relative_to(model_dir)
                file_info.append(
                    cls(str(relative_path), creation_timestamp, creation_timestamp_fmt)
                )

        return list(sorted(file_info, key=lambda x: x.name))

    @classmethod
    async def async_list(cls):
        """List all models and load their configs asynchronously."""
        # Get list of models
        models = await run.io_bound(cls.list)

        # Load all configs in parallel using asyncio.gather
        try:
            await asyncio.gather(*[model.async_config for model in models])
        except Exception as e:
            logger.warning(f"Failed to load some configs: {e}")

        return models
