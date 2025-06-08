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
    from core.messaging.cell_phone import send_message
    assert send_message is not None

@pytest.mark.asyncio
async def test_agent_imports():
    """Test agent-related imports."""
    from core.agent_control.agent_controller import AgentController
    from core.agent_control.periodic_restart import AgentManager, AgentResumeManager
    from core.agent_control.ui_automation import UIAutomation
    from core.agent_control.task_manager import TaskManager
    from core.agent_control.devlog_manager import DevLogManager
    
    assert AgentController is not None
    assert AgentManager is not None
    assert AgentResumeManager is not None
    assert UIAutomation is not None
    assert TaskManager is not None
    assert DevLogManager is not None 
