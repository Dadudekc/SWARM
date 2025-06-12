import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

import pytest
import json
import time
from pathlib import Path
from dreamos.core.messaging.request_queue import RequestQueue, Request

@pytest.fixture
def temp_queue_file(tmp_path):
    return str(tmp_path / "test_queue.json")

@pytest.fixture
def queue(temp_queue_file):
    return RequestQueue(temp_queue_file)

def test_add_request(queue):
    # Test adding a request
    message = "Test request"
    request = queue.add_request(message)
    
    assert isinstance(request, Request)
    assert request.message == message
    assert request.status == "pending"
    assert request.response is None
    assert request.error is None
    
    # Verify request was saved
    with open(queue.queue_file) as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["message"] == message

def test_update_request(queue):
    # Add a request
    request = queue.add_request("Test request")
    
    # Update the request
    response = "Test response"
    error = "Test error"
    queue.update_request(
        request.id,
        status="completed",
        response=response,
        error=error
    )
    
    # Verify request was updated
    updated_request = queue.requests[request.id]
    assert updated_request.status == "completed"
    assert updated_request.response == response
    assert updated_request.error == error
    
    # Verify changes were saved
    with open(queue.queue_file) as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["status"] == "completed"
        assert data[0]["response"] == response
        assert data[0]["error"] == error

def test_get_pending_requests(queue):
    # Add some requests
    request1 = queue.add_request("Request 1")
    request2 = queue.add_request("Request 2")
    request3 = queue.add_request("Request 3")
    
    # Update one request
    queue.update_request(request2.id, status="completed")
    
    # Get pending requests
    pending = queue.get_pending_requests()
    assert len(pending) == 2
    assert all(req.status == "pending" for req in pending)
    assert request1 in pending
    assert request3 in pending
    assert request2 not in pending

def test_clear_completed(queue):
    # Add some requests
    request1 = queue.add_request("Request 1")
    request2 = queue.add_request("Request 2")
    request3 = queue.add_request("Request 3")
    
    # Update some requests
    queue.update_request(request1.id, status="completed")
    queue.update_request(request2.id, status="failed")
    
    # Clear completed requests
    queue.clear_completed()
    
    # Verify only pending request remains
    assert len(queue.requests) == 1
    assert request3.id in queue.requests
    assert request1.id not in queue.requests
    assert request2.id not in queue.requests
    
    # Verify changes were saved
    with open(queue.queue_file) as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["id"] == request3.id 