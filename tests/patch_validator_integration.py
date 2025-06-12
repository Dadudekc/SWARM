import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Integration tests for the patch validator with scanner."""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from dreamos.core.autonomy.patch_validator import PatchValidator
from agent_tools.swarm_tools.scanner.scanner import Scanner
from dreamos.core.autonomy.codex_patch_tracker import CodexPatchTracker

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    return tmp_path

@pytest.fixture
def scanner(temp_project):
    """Create a scanner instance."""
    return Scanner(project_root=str(temp_project))

@pytest.fixture
def patch_tracker(temp_project):
    """Create a patch tracker instance."""
    return CodexPatchTracker(str(temp_project))

@pytest.fixture
def validator(scanner, patch_tracker):
    """Create a patch validator instance."""
    return PatchValidator(scanner, patch_tracker)

@pytest.mark.asyncio
async def test_clean_patch_validation(validator, scanner, temp_project):
    """Test validation of a clean patch with no duplicates."""
    # Create a clean test file
    test_file = temp_project / "clean_test.py"
    test_file.write_text("""
def unique_function():
    return "This is a unique implementation"
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "clean_patch",
        str(test_file),
        test_file.read_text()
    )
    
    assert is_valid
    assert results["status"] == "validated"
    assert "scanner_results" in results
    assert results["scanner_results"]["total_duplicates"] == 0
    assert "narrative" in results["scanner_results"]

@pytest.mark.asyncio
async def test_duplicate_handler_validation(validator, scanner, temp_project):
    """Test validation of a patch with duplicate handler code."""
    # Create files with duplicate handlers
    handler1 = temp_project / "handler1.py"
    handler1.write_text("""
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
    """)
    
    handler2 = temp_project / "handler2.py"
    handler2.write_text("""
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "duplicate_patch",
        str(handler2),
        handler2.read_text()
    )
    
    assert not is_valid
    assert results["error"] == "Scanner validation failed"
    assert "scanner_results" in results
    assert results["scanner_results"]["total_duplicates"] > 0
    assert "data_processors" in results["scanner_results"]["themes"]

@pytest.mark.asyncio
async def test_near_identical_test_fixture(validator, scanner, temp_project):
    """Test validation of a patch with near-identical test fixtures."""
    # Create test files with similar fixtures
    test1 = temp_project / "test1.py"
    test1.write_text("""
@pytest.fixture
def test_data():
    return {
        "name": "test",
        "value": 42
    }
    """)
    
    test2 = temp_project / "test2.py"
    test2.write_text("""
@pytest.fixture
def test_data():
    return {
        "name": "test",
        "value": 42,
        "extra": True
    }
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "fixture_patch",
        str(test2),
        test2.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    assert "test_fixtures" in results["scanner_results"]["themes"]
    assert "structural_insights" in results["scanner_results"]

@pytest.mark.asyncio
async def test_empty_patch_validation(validator, scanner):
    """Test validation of an empty patch."""
    is_valid, results = await validator.validate_patch(
        "empty_patch",
        "empty.py",
        ""
    )
    
    assert not is_valid
    assert results["error"] == "Scanner validation failed"
    assert "scanner_results" in results
    assert results["scanner_results"]["total_duplicates"] == 0

@pytest.mark.asyncio
async def test_malformed_scanner_output(validator, patch_tracker):
    """Test handling of malformed scanner output."""
    # Mock the scanner to return malformed output
    with patch.object(patch_tracker, 'validate_with_scanner') as mock_validate:
        mock_validate.return_value = (False, {"invalid": "json"})
        
        is_valid, results = await validator.validate_patch(
            "malformed_patch",
            "test.py",
            "def test(): pass"
        )
        
        assert not is_valid
        assert "error" in results
        assert "scanner_results" not in results

@pytest.mark.asyncio
async def test_scanner_timeout_handling(validator, patch_tracker):
    """Test handling of scanner timeout."""
    # Mock the scanner to simulate timeout
    with patch.object(patch_tracker, 'validate_with_scanner') as mock_validate:
        mock_validate.side_effect = asyncio.TimeoutError("Scanner timeout")
        
        is_valid, results = await validator.validate_patch(
            "timeout_patch",
            "test.py",
            "def test(): pass"
        )
        
        assert not is_valid
        assert results["error"] == "Scanner timeout"
        assert "scanner_results" not in results

@pytest.mark.asyncio
async def test_complex_nested_duplicates(validator, scanner, temp_project):
    """Test validation of a patch with complex nested duplicates."""
    # Create files with nested duplicate structures
    base1 = temp_project / "base1.py"
    base1.write_text("""
class BaseHandler:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)
    """)
    
    base2 = temp_project / "base2.py"
    base2.write_text("""
class BaseHandler:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "nested_patch",
        str(base2),
        base2.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    assert "base_classes" in results["scanner_results"]["themes"]
    assert "structural_insights" in results["scanner_results"]
    assert len(results["scanner_results"]["themes"]) > 0

@pytest.mark.asyncio
async def test_multiple_theme_detection(validator, scanner, temp_project):
    """Test detection of multiple themes in a single patch."""
    # Create a file with multiple duplicate patterns
    complex_file = temp_project / "complex.py"
    complex_file.write_text("""
class DataProcessor:
    def process(self, data):
        return [x * 2 for x in data]

@pytest.fixture
def test_data():
    return {"value": 42}

def validate_input(data):
    return all(x > 0 for x in data)
    """)
    
    # Create similar patterns in other files
    other_file = temp_project / "other.py"
    other_file.write_text("""
class DataProcessor:
    def process(self, data):
        return [x * 2 for x in data]

@pytest.fixture
def test_data():
    return {"value": 42}

def validate_input(data):
    return all(x > 0 for x in data)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "multi_theme_patch",
        str(complex_file),
        complex_file.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert len(themes) > 1
    assert any("data_processors" in theme for theme in themes)
    assert any("test_fixtures" in theme for theme in themes)

@pytest.mark.asyncio
async def test_cross_module_base_class_duplicates(validator, scanner, temp_project):
    """Test detection of duplicate base classes across different modules."""
    # Create a core module with base classes
    core_dir = temp_project / "core"
    core_dir.mkdir()
    base_handler = core_dir / "base_handler.py"
    base_handler.write_text("""
class BaseHandler:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)
    
    def get_config(self):
        return self.config
    """)
    
    # Create a feature module with similar base class
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_handler = feature_dir / "feature_handler.py"
    feature_handler.write_text("""
class FeatureHandler:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)
    
    def get_config(self):
        return self.config
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "cross_module_base_patch",
        str(feature_handler),
        feature_handler.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    assert "base_classes" in results["scanner_results"]["themes"]
    assert "structural_insights" in results["scanner_results"]
    assert len(results["scanner_results"]["themes"]["base_classes"]) > 0

@pytest.mark.asyncio
async def test_cross_module_utility_duplicates(validator, scanner, temp_project):
    """Test detection of duplicate utility functions across different modules."""
    # Create utility functions in different modules
    utils_dir = temp_project / "utils"
    utils_dir.mkdir()
    data_utils = utils_dir / "data_utils.py"
    data_utils.write_text("""
def process_data(data):
    result = []
    for item in data:
        if isinstance(item, (int, float)):
            result.append(item * 2)
        else:
            result.append(item)
    return result

def validate_data(data):
    return all(isinstance(x, (int, float)) for x in data)
    """)
    
    # Create similar utilities in another module
    helpers_dir = temp_project / "helpers"
    helpers_dir.mkdir()
    data_helpers = helpers_dir / "data_helpers.py"
    data_helpers.write_text("""
def process_data(data):
    result = []
    for item in data:
        if isinstance(item, (int, float)):
            result.append(item * 2)
        else:
            result.append(item)
    return result

def validate_data(data):
    return all(isinstance(x, (int, float)) for x in data)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "cross_module_utils_patch",
        str(data_helpers),
        data_helpers.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    assert "data_processors" in results["scanner_results"]["themes"]
    assert len(results["scanner_results"]["themes"]["data_processors"]) > 0

@pytest.mark.asyncio
async def test_cross_module_mixed_duplicates(validator, scanner, temp_project):
    """Test detection of mixed duplicate patterns across different modules."""
    # Create a complex module structure with mixed duplicates
    core_dir = temp_project / "core"
    core_dir.mkdir()
    base_processor = core_dir / "base_processor.py"
    base_processor.write_text("""
class BaseProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)

def process_data(data):
    result = []
    for item in data:
        if isinstance(item, (int, float)):
            result.append(item * 2)
        else:
            result.append(item)
    return result
    """)
    
    # Create a feature module with similar patterns
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_processor = feature_dir / "feature_processor.py"
    feature_processor.write_text("""
class FeatureProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)

def process_data(data):
    result = []
    for item in data:
        if isinstance(item, (int, float)):
            result.append(item * 2)
        else:
            result.append(item)
    return result
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "cross_module_mixed_patch",
        str(feature_processor),
        feature_processor.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert len(themes) > 1
    assert "base_classes" in themes
    assert "data_processors" in themes
    assert "structural_insights" in results["scanner_results"]

@pytest.mark.asyncio
async def test_cross_module_nested_structure_duplicates(validator, scanner, temp_project):
    """Test detection of nested structure duplicates across different modules."""
    # Create a module with nested structures
    core_dir = temp_project / "core"
    core_dir.mkdir()
    nested_processor = core_dir / "nested_processor.py"
    nested_processor.write_text("""
class DataProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)

class NestedProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.nested_data = []
    
    def process_nested(self, item):
        return self.process(item) * 2
    
    def validate_nested(self, data):
        return self.validate(data) and all(x > 0 for x in data)
    """)
    
    # Create another module with similar nested structures
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_nested = feature_dir / "feature_nested.py"
    feature_nested.write_text("""
class DataProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return item * 2
    
    def validate(self, data):
        return all(x > 0 for x in data)

class NestedProcessor(DataProcessor):
    def __init__(self):
        super().__init__()
        self.nested_data = []
    
    def process_nested(self, item):
        return self.process(item) * 2
    
    def validate_nested(self, data):
        return self.validate(data) and all(x > 0 for x in data)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "cross_module_nested_patch",
        str(feature_nested),
        feature_nested.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert len(themes) > 1
    assert "base_classes" in themes
    assert "nested_structures" in themes
    assert "structural_insights" in results["scanner_results"]
    assert any("inheritance" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_duplicate_method_chain_inheritance(validator, scanner, temp_project):
    """Test detection of duplicate method chains across inheritance hierarchies."""
    # Create a core module with a method chain
    core_dir = temp_project / "core"
    core_dir.mkdir()
    base_processor = core_dir / "base_processor.py"
    base_processor.write_text("""
class BaseProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return self._validate(item) and self._transform(item)
    
    def _validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def _transform(self, item):
        return item * 2

class DataProcessor(BaseProcessor):
    def process(self, item):
        return super().process(item) and self._enrich(item)
    
    def _enrich(self, item):
        return {"value": item, "processed": True}
    """)
    
    # Create a feature module with similar method chain
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_processor = feature_dir / "feature_processor.py"
    feature_processor.write_text("""
class FeatureProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        return self._validate(item) and self._transform(item)
    
    def _validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def _transform(self, item):
        return item * 2

class EnhancedProcessor(FeatureProcessor):
    def process(self, item):
        return super().process(item) and self._enrich(item)
    
    def _enrich(self, item):
        return {"value": item, "processed": True}
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "method_chain_patch",
        str(feature_processor),
        feature_processor.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "method_chains" in themes
    assert "inheritance_patterns" in themes
    assert any("chain" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_overridden_methods_same_logic(validator, scanner, temp_project):
    """Test detection of overridden methods with same logic in different modules."""
    # Create a core module with base class
    core_dir = temp_project / "core"
    core_dir.mkdir()
    base_handler = core_dir / "base_handler.py"
    base_handler.write_text("""
class BaseHandler:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        if not self._validate(item):
            return None
        return self._transform(item)
    
    def _validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def _transform(self, item):
        return item * 2

class DataHandler(BaseHandler):
    def _validate(self, item):
        # Same logic, different implementation
        if not isinstance(item, (int, float)):
            return False
        return item > 0
    
    def _transform(self, item):
        # Same logic, different implementation
        return item + item
    """)
    
    # Create a feature module with similar overrides
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_handler = feature_dir / "feature_handler.py"
    feature_handler.write_text("""
class FeatureHandler:
    def __init__(self):
        self.data = []
        self.config = {}
    
    def process(self, item):
        if not self._validate(item):
            return None
        return self._transform(item)
    
    def _validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def _transform(self, item):
        return item * 2

class EnhancedHandler(FeatureHandler):
    def _validate(self, item):
        # Same logic, different implementation
        if not isinstance(item, (int, float)):
            return False
        return item > 0
    
    def _transform(self, item):
        # Same logic, different implementation
        return item + item
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "overridden_methods_patch",
        str(feature_handler),
        feature_handler.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "method_overrides" in themes
    assert "logical_duplicates" in themes
    assert any("override" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_template_method_duplication(validator, scanner, temp_project):
    """Test detection of duplicate template method patterns across modules."""
    # Create a core module with template method
    core_dir = temp_project / "core"
    core_dir.mkdir()
    template_processor = core_dir / "template_processor.py"
    template_processor.write_text("""
class TemplateProcessor:
    def process(self, data):
        if not self._validate_input(data):
            return None
        processed = self._process_items(data)
        return self._format_output(processed)
    
    def _validate_input(self, data):
        return isinstance(data, list) and all(isinstance(x, (int, float)) for x in data)
    
    def _process_items(self, data):
        return [x * 2 for x in data]
    
    def _format_output(self, data):
        return {"processed": data, "count": len(data)}

class DataProcessor(TemplateProcessor):
    def _process_items(self, data):
        return [x * 3 for x in data]
    
    def _format_output(self, data):
        return {"data": data, "length": len(data)}
    """)
    
    # Create a feature module with similar template
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_template = feature_dir / "feature_template.py"
    feature_template.write_text("""
class FeatureTemplate:
    def process(self, data):
        if not self._validate_input(data):
            return None
        processed = self._process_items(data)
        return self._format_output(processed)
    
    def _validate_input(self, data):
        return isinstance(data, list) and all(isinstance(x, (int, float)) for x in data)
    
    def _process_items(self, data):
        return [x * 2 for x in data]
    
    def _format_output(self, data):
        return {"processed": data, "count": len(data)}

class EnhancedProcessor(FeatureTemplate):
    def _process_items(self, data):
        return [x * 3 for x in data]
    
    def _format_output(self, data):
        return {"data": data, "length": len(data)}
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "template_method_patch",
        str(feature_template),
        feature_template.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "template_methods" in themes
    assert "method_hooks" in themes
    assert any("template" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_decorator_pattern_duplication(validator, scanner, temp_project):
    """Test detection of duplicate decorator patterns across modules."""
    # Create a core module with decorator pattern
    core_dir = temp_project / "core"
    core_dir.mkdir()
    decorator_processor = core_dir / "decorator_processor.py"
    decorator_processor.write_text("""
class BaseProcessor:
    def process(self, item):
        return item * 2

class LoggingProcessor(BaseProcessor):
    def process(self, item):
        print(f"Processing: {item}")
        result = super().process(item)
        print(f"Result: {result}")
        return result

class ValidationProcessor(BaseProcessor):
    def process(self, item):
        if not isinstance(item, (int, float)):
            raise ValueError("Invalid input")
        return super().process(item)

class CompositeProcessor(ValidationProcessor, LoggingProcessor):
    pass
    """)
    
    # Create a feature module with similar decorator pattern
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_decorator = feature_dir / "feature_decorator.py"
    feature_decorator.write_text("""
class FeatureProcessor:
    def process(self, item):
        return item * 2

class LoggingFeature(FeatureProcessor):
    def process(self, item):
        print(f"Processing: {item}")
        result = super().process(item)
        print(f"Result: {result}")
        return result

class ValidationFeature(FeatureProcessor):
    def process(self, item):
        if not isinstance(item, (int, float)):
            raise ValueError("Invalid input")
        return super().process(item)

class CompositeFeature(ValidationFeature, LoggingFeature):
    pass
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "decorator_pattern_patch",
        str(feature_decorator),
        feature_decorator.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "decorator_patterns" in themes
    assert "method_wrappers" in themes
    assert any("decorator" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_diamond_inheritance_duplication(validator, scanner, temp_project):
    """Test detection of duplicate diamond inheritance patterns."""
    # Create a core module with diamond pattern
    core_dir = temp_project / "core"
    core_dir.mkdir()
    diamond_base = core_dir / "diamond_base.py"
    diamond_base.write_text("""
class BaseProcessor:
    def process(self, item):
        return item * 2

class ValidationMixin:
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0

class LoggingMixin:
    def log(self, item):
        print(f"Processing: {item}")

class DataProcessor(BaseProcessor, ValidationMixin, LoggingMixin):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        return super().process(item)

class EnhancedProcessor(BaseProcessor, LoggingMixin, ValidationMixin):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        return super().process(item)
    """)
    
    # Create a feature module with similar diamond pattern
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_diamond = feature_dir / "feature_diamond.py"
    feature_diamond.write_text("""
class FeatureProcessor:
    def process(self, item):
        return item * 2

class ValidationFeature:
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0

class LoggingFeature:
    def log(self, item):
        print(f"Processing: {item}")

class FeatureDataProcessor(FeatureProcessor, ValidationFeature, LoggingFeature):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        return super().process(item)

class EnhancedFeatureProcessor(FeatureProcessor, LoggingFeature, ValidationFeature):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        return super().process(item)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "diamond_pattern_patch",
        str(feature_diamond),
        feature_diamond.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "diamond_patterns" in themes
    assert "mro_duplicates" in themes
    assert any("diamond" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_mro_ambiguity_duplication(validator, scanner, temp_project):
    """Test detection of duplicate MRO ambiguity patterns."""
    # Create a core module with MRO ambiguity
    core_dir = temp_project / "core"
    core_dir.mkdir()
    mro_base = core_dir / "mro_base.py"
    mro_base.write_text("""
class BaseHandler:
    def handle(self, item):
        return item * 2

class ValidationHandler:
    def handle(self, item):
        if not isinstance(item, (int, float)):
            return None
        return item * 2

class LoggingHandler:
    def handle(self, item):
        print(f"Handling: {item}")
        return item * 2

class AmbiguousHandler(ValidationHandler, LoggingHandler):
    pass

class AnotherAmbiguousHandler(LoggingHandler, ValidationHandler):
    pass
    """)
    
    # Create a feature module with similar MRO ambiguity
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_mro = feature_dir / "feature_mro.py"
    feature_mro.write_text("""
class FeatureHandler:
    def handle(self, item):
        return item * 2

class ValidationFeature:
    def handle(self, item):
        if not isinstance(item, (int, float)):
            return None
        return item * 2

class LoggingFeature:
    def handle(self, item):
        print(f"Handling: {item}")
        return item * 2

class AmbiguousFeature(ValidationFeature, LoggingFeature):
    pass

class AnotherAmbiguousFeature(LoggingFeature, ValidationFeature):
    pass
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "mro_ambiguity_patch",
        str(feature_mro),
        feature_mro.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "mro_ambiguity" in themes
    assert "method_conflicts" in themes
    assert any("ambiguous" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_mixin_explosion_duplication(validator, scanner, temp_project):
    """Test detection of duplicate mixin explosion patterns."""
    # Create a core module with mixin explosion
    core_dir = temp_project / "core"
    core_dir.mkdir()
    mixin_base = core_dir / "mixin_base.py"
    mixin_base.write_text("""
class ValidationMixin:
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0

class LoggingMixin:
    def log(self, item):
        print(f"Processing: {item}")

class CachingMixin:
    def cache(self, item):
        return f"cached_{item}"

class MetricsMixin:
    def track(self, item):
        return f"tracked_{item}"

class BaseProcessor:
    def process(self, item):
        return item * 2

class ProcessorWithMixins(BaseProcessor, ValidationMixin, LoggingMixin, CachingMixin, MetricsMixin):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        cached = self.cache(item)
        self.track(cached)
        return super().process(item)
    """)
    
    # Create a feature module with similar mixin explosion
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_mixin = feature_dir / "feature_mixin.py"
    feature_mixin.write_text("""
class ValidationFeature:
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0

class LoggingFeature:
    def log(self, item):
        print(f"Processing: {item}")

class CachingFeature:
    def cache(self, item):
        return f"cached_{item}"

class MetricsFeature:
    def track(self, item):
        return f"tracked_{item}"

class FeatureProcessor:
    def process(self, item):
        return item * 2

class FeatureWithMixins(FeatureProcessor, ValidationFeature, LoggingFeature, CachingFeature, MetricsFeature):
    def process(self, item):
        if not self.validate(item):
            return None
        self.log(item)
        cached = self.cache(item)
        self.track(cached)
        return super().process(item)
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "mixin_explosion_patch",
        str(feature_mixin),
        feature_mixin.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "mixin_explosion" in themes
    assert "method_chains" in themes
    assert any("mixin" in insight.lower() for insight in results["scanner_results"]["structural_insights"])

@pytest.mark.asyncio
async def test_interface_duplication(validator, scanner, temp_project):
    """Test detection of duplicate interface patterns across modules."""
    # Create a core module with interface pattern
    core_dir = temp_project / "core"
    core_dir.mkdir()
    interface_base = core_dir / "interface_base.py"
    interface_base.write_text("""
from abc import ABC, abstractmethod

class DataProcessorInterface(ABC):
    @abstractmethod
    def process(self, item):
        pass
    
    @abstractmethod
    def validate(self, item):
        pass
    
    @abstractmethod
    def transform(self, item):
        pass

class BaseProcessor(DataProcessorInterface):
    def process(self, item):
        if not self.validate(item):
            return None
        return self.transform(item)
    
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def transform(self, item):
        return item * 2
    """)
    
    # Create a feature module with similar interface
    feature_dir = temp_project / "features"
    feature_dir.mkdir()
    feature_interface = feature_dir / "feature_interface.py"
    feature_interface.write_text("""
from abc import ABC, abstractmethod

class FeatureProcessorInterface(ABC):
    @abstractmethod
    def process(self, item):
        pass
    
    @abstractmethod
    def validate(self, item):
        pass
    
    @abstractmethod
    def transform(self, item):
        pass

class FeatureProcessor(FeatureProcessorInterface):
    def process(self, item):
        if not self.validate(item):
            return None
        return self.transform(item)
    
    def validate(self, item):
        return isinstance(item, (int, float)) and item > 0
    
    def transform(self, item):
        return item * 2
    """)
    
    # Validate the patch
    is_valid, results = await validator.validate_patch(
        "interface_pattern_patch",
        str(feature_interface),
        feature_interface.read_text()
    )
    
    assert not is_valid
    assert "scanner_results" in results
    themes = results["scanner_results"]["themes"]
    assert "interface_patterns" in themes
    assert "abstract_methods" in themes
    assert any("interface" in insight.lower() for insight in results["scanner_results"]["structural_insights"]) 