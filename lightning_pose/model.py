import pandas as pd
from pathlib import Path

from lightning.pytorch import LightningModule

from config import ModelConfig

from lightning_pose.utils.io import ckpt_path_from_base_path
from lightning_pose.utils.predictions import load_model_from_checkpoint
from lightning_pose.datasets import LabeledFrameDataset, VideoDataset

__all__ = ["Model"]


class Model:
    model_dir: Path
    cfg: ModelConfig
    model: LightningModule

    @staticmethod
    def from_dir(model_dir: Path):
        cfg = ModelConfig.from_yaml(model_dir / "config.yaml")
        return Model(model_dir, cfg)

    def __init__(self, model_dir, cfg):
        self.model_dir = model_dir
        self.cfg = cfg

    def _load(self):
        ckpt_file = ckpt_path_from_base_path(
            base_path=self.model_dir, model_name=cfg.model.model_name
        )
        self.model = load_model_from_checkpoint(
            cfg=self.cfg, ckpt_file=ckpt_file, eval=True, skip_data_module=True,
        )

    #############
    # Prediction
    #############

    def predict_dataset(self, dataset: LabeledFrameDataset | VideoDataset) -> pd.DataFrame:
        self._load()
        from prediction import predict_dataset
        return predict_dataset(self, dataset)

    def predict_video(self, video_file: Path) -> pd.DataFrame:
        self._load()
        from prediction import predict_video
        return predict_video(self, video_file)
