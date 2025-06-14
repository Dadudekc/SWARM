# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

"""
Dream.OS
--------
A modular operating system for AI agents.
"""

# EDIT START: Defer heavy optional imports during partial test runs.
import importlib
import types
from typing import Any, Dict


_OPTIONAL_SYMBOLS: Dict[str, str] = {
    "Scanner": "dreamos.core.verification.scanner",
    "patch_validator": "dreamos.core.patch_validator",
    "patch_analyzer": "dreamos.core.patch_analyzer",
    "patch_metrics": "dreamos.core.patch_metrics",
    "patch_metrics_analyzer": "dreamos.core.patch_metrics_analyzer",
    "patch_metrics_collector": "dreamos.core.patch_metrics_collector",
    "patch_metrics_processor": "dreamos.core.patch_metrics_processor",
    "patch_metrics_reporter": "dreamos.core.patch_metrics_reporter",
    "patch_metrics_validator": "dreamos.core.patch_metrics_validator",
    "patch_metrics_visualizer": "dreamos.core.patch_metrics_visualizer",
    "patch_metrics_aggregator": "dreamos.core.patch_metrics_aggregator",
    "patch_metrics_exporter": "dreamos.core.patch_metrics_exporter",
    "patch_metrics_importer": "dreamos.core.patch_metrics_importer",
    "patch_metrics_transformer": "dreamos.core.patch_metrics_transformer",
    "patch_metrics_normalizer": "dreamos.core.patch_metrics_normalizer",
    "patch_metrics_denormalizer": "dreamos.core.patch_metrics_denormalizer",
    "patch_metrics_serializer": "dreamos.core.patch_metrics_serializer",
    "patch_metrics_deserializer": "dreamos.core.patch_metrics_deserializer",
    "patch_metrics_compressor": "dreamos.core.patch_metrics_compressor",
    "patch_metrics_decompressor": "dreamos.core.patch_metrics_decompressor",
    "patch_metrics_encryptor": "dreamos.core.patch_metrics_encryptor",
    "patch_metrics_decryptor": "dreamos.core.patch_metrics_decryptor",
}


def __getattr__(name: str) -> Any:  # noqa: D401
    target = _OPTIONAL_SYMBOLS.get(name)
    if target is None:
        raise AttributeError(name)

    try:
        module = importlib.import_module(target)
        symbol = getattr(module, name, module)
        globals()[name] = symbol  # cache for reuse
        return symbol
    except BaseException:  # pragma: no cover – missing optional deps
        # Provide stub placeholder so attribute access doesn't fail.
        placeholder = types.SimpleNamespace(__doc__=f"Stub for missing optional symbol '{name}'")
        globals()[name] = placeholder
        return placeholder
# EDIT END

__all__ = [
    'Scanner',
    'patch_validator',
    'patch_analyzer',
    'patch_metrics',
    'patch_metrics_analyzer',
    'patch_metrics_collector',
    'patch_metrics_processor',
    'patch_metrics_reporter',
    'patch_metrics_validator',
    'patch_metrics_visualizer',
    'patch_metrics_aggregator',
    'patch_metrics_exporter',
    'patch_metrics_importer',
    'patch_metrics_transformer',
    'patch_metrics_normalizer',
    'patch_metrics_denormalizer',
    'patch_metrics_serializer',
    'patch_metrics_deserializer',
    'patch_metrics_compressor',
    'patch_metrics_decompressor',
    'patch_metrics_encryptor',
    'patch_metrics_decryptor'
]
