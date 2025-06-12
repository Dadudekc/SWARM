"""
Tests for the coordinate manager module.
"""

import pytest
from dreamos.core.shared.coordinate_manager import (
    CoordinateManager,
    load_coordinates,
    save_coordinates,
    get_coordinates,
    set_coordinates
)

def test_coordinate_manager_initialization():
    """Test that CoordinateManager initializes correctly."""
    manager = CoordinateManager()
    assert manager is not None
    assert isinstance(manager, CoordinateManager)

def test_coordinate_operations():
    """Test basic coordinate operations."""
    # Test setting coordinates
    test_coords = {"x": 100, "y": 200}
    set_coordinates(test_coords)
    
    # Test getting coordinates
    retrieved_coords = get_coordinates()
    assert retrieved_coords == test_coords
    
    # Test saving coordinates
    save_coordinates()
    
    # Test loading coordinates
    loaded_coords = load_coordinates()
    assert loaded_coords == test_coords

def test_invalid_coordinates():
    """Test handling of invalid coordinates."""
    with pytest.raises(ValueError):
        set_coordinates({"invalid": "coordinates"})
    
    with pytest.raises(ValueError):
        set_coordinates({"x": "not_a_number", "y": 200}) 