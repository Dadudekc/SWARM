"""
Tests for the processors module.
"""

import pytest
from dreamos.core.shared.processors import (
    MessageProcessor,
    ResponseProcessor,
    ProcessorFactory,
    ProcessorMode
)

def test_processor_mode():
    """Test that ProcessorMode enum values are correct."""
    assert ProcessorMode.MESSAGE == "message"
    assert ProcessorMode.RESPONSE == "response"

def test_processor_factory():
    """Test that ProcessorFactory creates correct processor types."""
    factory = ProcessorFactory()
    
    # Test message processor creation
    message_processor = factory.create_processor(ProcessorMode.MESSAGE)
    assert isinstance(message_processor, MessageProcessor)
    
    # Test response processor creation
    response_processor = factory.create_processor(ProcessorMode.RESPONSE)
    assert isinstance(response_processor, ResponseProcessor)
    
    # Test invalid mode
    with pytest.raises(ValueError):
        factory.create_processor("invalid_mode")

def test_message_processor():
    """Test basic message processor functionality."""
    processor = MessageProcessor()
    
    # Test process method
    test_message = "test message"
    result = processor.process(test_message)
    assert isinstance(result, str)
    assert len(result) > 0

def test_response_processor():
    """Test basic response processor functionality."""
    processor = ResponseProcessor()
    
    # Test process method
    test_response = "test response"
    result = processor.process(test_response)
    assert isinstance(result, str)
    assert len(result) > 0 