from typing import Dict, Any

def grade_easy_task(state: Dict[str, Any]) -> float:
    """
    Task 1 (Easy): 'Disk Full' on the database.
    Returns 0.90 if the agent executed the disk scale-up remediation.
    Returns 0.10 if it failed.
    """
    # In easy scenario, success is indicated by the database disk dropping below 100
    if state["services"]["database"]["disk"] < 100:
        return 0.90
    return 0.10


def grade_medium_task(state: Dict[str, Any]) -> float:
    """
    Task 2 (Medium): 'Memory Leak' on the backend.
    Returns 0.85 for a full fix (restarting/rolling back the service).
    Returns 0.55 for partial credit (identifying OOM in the resolve_ticket call without fixing it).
    Returns 0.15 for failure.
    """
    # Success is indicated by the backend ram usage dropping (or status returning to healthy)
    if state["services"]["backend"]["ram"] < 90:
        return 0.85
    
    # Check for partial credit: identify OOM
    root_cause = state.get("root_cause", "")
    if root_cause and ("oom" in root_cause.lower() or "out of memory" in root_cause.lower() or "memory" in root_cause.lower()):
        return 0.55
        
    return 0.15


def grade_hard_task(state: Dict[str, Any]) -> float:
    """
    Task 3 (Hard): 'DB Connection Exhaustion'.
    Returns 0.95 for perfect execution (checked backend logs AND database metrics before applying the fix).
    Returns 0.65 for sloppy execution (applying the fix without checking the data first).
    Returns 0.05 for failure.
    """
    # Check if the DB connection pool was fixed
    if state["services"]["database"]["status"] != "healthy":
        return 0.05
        
    # Fixed! Now verify execution order from history
    checked_backend_logs = False
    checked_db_metrics = False
    
    for action in state.get("history", []):
        # Did they check backend logs?
        if action.get("action") == "read_logs" and action.get("service") == "backend":
            checked_backend_logs = True
            
        # Did they check DB metrics?
        if action.get("action") == "check_metrics" and action.get("service") == "database":
            checked_db_metrics = True
            
        # Did they remediate? We evaluate the checks *before* or *at* the time of remediation.
        # Once we see remediation, we break to ensure they didn't just check it afterwards.
        if action.get("action") == "execute_remediation":
            break
            
    if checked_backend_logs and checked_db_metrics:
        return 0.95
    else:
        return 0.65
