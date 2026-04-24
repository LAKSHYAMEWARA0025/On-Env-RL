from environment import OnCallEnvironment
from models import CheckMetricsAction, ReadLogsAction, ExecuteRemediationAction, ResolveTicketAction
from tasks import grade_easy_task, grade_medium_task, grade_hard_task

def test_easy():
    env = OnCallEnvironment()
    env.reset(task_id="easy")
    env.step(CheckMetricsAction(service="database"))
    env.step(ExecuteRemediationAction(remediation_action="scale up disk"))
    env.step(ResolveTicketAction(root_cause="Database disk was full"))
    score = grade_easy_task(env.state())
    print(f"Easy Task Score: {score} (Expected 0.9)")

def test_medium_partial():
    env = OnCallEnvironment()
    env.reset(task_id="medium")
    env.step(CheckMetricsAction(service="backend"))
    env.step(ResolveTicketAction(root_cause="Out of memory OOM exception"))
    score = grade_medium_task(env.state())
    print(f"Medium Task Partial Score: {score} (Expected 0.55)")

def test_hard_sloppy():
    env = OnCallEnvironment()
    env.reset(task_id="hard")
    # No checking before remediation
    env.step(ExecuteRemediationAction(remediation_action="increase db connection pool"))
    env.step(ResolveTicketAction(root_cause="Pool full"))
    score = grade_hard_task(env.state())
    print(f"Hard Task Sloppy Score: {score} (Expected 0.65)")

def test_hard_perfect():
    env = OnCallEnvironment()
    env.reset(task_id="hard")
    # Checking before remediation
    env.step(ReadLogsAction(service="backend", lines=10))
    env.step(CheckMetricsAction(service="database"))
    env.step(ExecuteRemediationAction(remediation_action="increase db connection pool"))
    env.step(ResolveTicketAction(root_cause="Pool full"))
    score = grade_hard_task(env.state())
    print(f"Hard Task Perfect Score: {score} (Expected 0.95)")

if __name__ == "__main__":
    test_easy()
    test_medium_partial()
    test_hard_sloppy()
    test_hard_perfect()