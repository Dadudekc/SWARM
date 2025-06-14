# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

# EDIT START: Relax eager imports to avoid module-level `pytest.skip` propagating
try:
    from . import base_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import bridge_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import conftest  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import daemon_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import file_ops_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import interface_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import manager_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import perpetual_test_fixer_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import retry_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import session_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass

try:
    from . import token_test  # noqa: F401
except BaseException:  # pragma: no cover
    pass
# EDIT END

__all__ = [
    'base_test',
    'bridge_test',
    'conftest',
    'daemon_test',
    'file_ops_test',
    'interface_test',
    'manager_test',
    'perpetual_test_fixer_test',
    'retry_test',
    'session_test',
    'token_test',
]
