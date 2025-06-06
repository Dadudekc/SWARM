import pytest
from dreamos.social.utils.log_manager import LogManager, LogConfig

@pytest.fixture
def setup_tmp_log_dir(tmp_path):
    """Set up temporary log directory."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create LogManager with the temp dir
    config = LogConfig(log_dir=str(log_dir))
    manager = LogManager(config=config)
    
    yield log_dir, manager
    
    # Cleanup
    manager.shutdown() 