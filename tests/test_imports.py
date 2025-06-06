"""
Test critical imports for the project.
"""

import pytest
import pytest_asyncio

pytestmark = pytest.mark.pyqt5

@pytest.mark.asyncio
async def test_pyqt5_import():
    """Test PyQt5 imports."""
    from PyQt5.QtCore import Qt
    assert Qt is not None

@pytest.mark.asyncio
async def test_discord_import():
    """Test Discord imports."""
    from discord.ext.commands import Context
    assert Context is not None

@pytest.mark.asyncio
async def test_cell_phone_import():
    """Test cell phone messaging imports."""
    from dreamos.core.messaging.cell_phone import send_message
    assert send_message is not None 