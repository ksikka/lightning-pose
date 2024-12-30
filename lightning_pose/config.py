from dataclasses import dataclass
from omegaconf import OmegaConf
from pathlib import Path

@dataclass
class ModelConfig:
    model_name: str

    @staticmethod
    def from_yaml(filepath):
        model_cfg = OmegaConf.structured(ModelConfig)
        OmegaConf.merge(model_cfg, OmegaConf.load(filepath))
        return ModelConfig(**model_cfg)


class ModelDir(Path):
    pass


class ModelDir(Path):
    pass