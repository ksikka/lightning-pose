# Automatically import all modules in the package, so we can do:
# >>> import tabs
# >>> tabs.home.Home()
# Instead of
# >>> import tabs.home
# >>> import home.Home()
import os
import importlib
import glob

__all__ = []

for module_path in glob.glob(os.path.join(os.path.dirname(__file__), "*.py")):
    module_name = os.path.basename(module_path)[:-3]  # Remove .py extension
    if module_name != "__init__":
        module = importlib.import_module("." + module_name, __name__)
        __all__.append(module_name)
