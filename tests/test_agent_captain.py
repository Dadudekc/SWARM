"""
Tests for the agent controller functionality.
"""

from dreamos.core import AgentController

def test_agent_controller_initialization():
    """Test that the agent controller initializes correctly."""
    controller = AgentController()
    assert controller is not None
    assert hasattr(controller, 'message_processor')
    assert hasattr(controller, 'coordinate_manager')
    assert hasattr(controller, 'cursor_controller')
    assert hasattr(controller, 'cell_phone')
    assert hasattr(controller, 'coords')
    assert hasattr(controller, 'menu')

def test_agent_controller_onboarding():
    """Test agent onboarding functionality."""
    controller = AgentController()
    # Test with UI automation disabled
    controller.onboard_agent("Agent-1", use_ui=False)
    # Test with UI automation enabled
    controller.onboard_agent("Agent-1", use_ui=True)

def test_agent_controller_message_sending():
    """Test message sending functionality."""
    controller = AgentController()
    # Test with UI automation disabled
    controller.resume_agent("Agent-1", use_ui=False)
    # Test with UI automation enabled
    controller.resume_agent("Agent-1", use_ui=True)

# Add more tests as needed... 