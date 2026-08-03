"""
Utility modules for the Memorize RAG project.
"""


def fetch_and_bifurcate_models(*args, **kwargs):
    from utils.model_fetcher import fetch_and_bifurcate_models as _fetch

    return _fetch(*args, **kwargs)


def get_available_models(*args, **kwargs):
    from utils.model_fetcher import get_available_models as _get

    return _get(*args, **kwargs)


__all__ = ["fetch_and_bifurcate_models", "get_available_models"]
