import sys
import os

api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../api"))
if api_path not in sys.path:
    sys.path.append(api_path)

import app
api_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../api/app"))
if api_app_path not in app.__path__:
    app.__path__.append(api_app_path)

import pkgutil
import importlib

def merge_paths(base_pkg, source_path):
    for importer, name, ispkg in pkgutil.iter_modules([source_path]):
        if ispkg:
            full_name = f"{base_pkg.__name__}.{name}"
            try:
                mod = importlib.import_module(full_name)
                sub_source = os.path.join(source_path, name)
                if hasattr(mod, '__path__') and sub_source not in mod.__path__:
                    mod.__path__.append(sub_source)
                merge_paths(mod, sub_source)
            except ImportError as e:
                pass

merge_paths(app, api_app_path)

try:
    from app.agents.pipeline import orchestrator
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
