"""Minimal stubs for test marker helpers used in conftest."""

def is_claimed_by_agent(item, agent_id=None):
    return False

def get_claiming_agent(item):
    return None

def get_claim_issue(item):
    return None

def agent_claimed(item, agent_id, issue):
    pass

def agent_fixed(item):
    pass

def agent_skipped(item):
    pass

def agent_in_progress(item):
    pass
