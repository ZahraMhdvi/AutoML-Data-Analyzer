

import platform
import sys
from functools import lru_cache


PACKAGES = ("numpy", "pandas", "scikit-learn", "scipy", "xgboost", "fastapi", "openai")


@lru_cache(maxsize=1)
def environment_versions():
    from importlib import metadata

    versions = {"python": sys.version.split()[0], "platform": platform.platform(terse=True)}
    for package in PACKAGES:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    return versions
