import tempfile
from dreamos.core.analytics.failure_pipeline import FailureAnalyticsPipeline

def test_log_and_resolve():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    pipe = FailureAnalyticsPipeline(db_path=tmp.name)
    err_id = pipe.log_error("agent1", "TypeError", "bad value")
    stats = pipe.stats()
    assert stats["total"] == 1
    assert stats["counts"]["TypeError"] == 1
    pipe.mark_resolved(err_id, "fixed")
    stats2 = pipe.stats()
    assert stats2["resolved"] == 1
    assert stats2["resolution_rate"] == 100.0
