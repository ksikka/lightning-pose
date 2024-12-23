import torch
from omegaconf import DictConfig, ListConfig

# to ignore imports for sphix-autoapidoc
__all__ = [
    "pretty_print_str",
    "pretty_print_cfg",
]


def pretty_print_str(string: str, symbol: str = "-") -> None:
    str_length = len(string)
    print(symbol * str_length)
    print(string)
    print(symbol * str_length)


def pretty_print_cfg(cfg):
    for key, val in cfg.items():
        if key == "eval":
            continue
        if isinstance(val, DictConfig):
            print("--------------------")
            print("%s parameters" % key)
            print("--------------------")
            for k, v in val.items():
                print("{}: {}".format(k, v))
        else:
            print("{}: {}".format(key, val))
        print()
    print("\n\n")
