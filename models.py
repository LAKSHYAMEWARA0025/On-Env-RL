from typing import Optional, Union, Literal
from pydantic import Field
from typing_extensions import Annotated
from openenv_core import Action as BaseAction, Observation as BaseObservation

# --- Observation Space ---

class Observation(BaseObservation):
    active_alert: Optional[str] = Field(
        default=None, 
        description="The active PagerDuty-style alert."
    )
    time: str = Field(
        ..., 
        description="System time."
    )
    last_output: str = Field(
        ..., 
        description="The stdout/stderr of the last executed tool."
    )

# --- Action Space (Tools) ---

class CheckMetricsAction(BaseAction):
    action: Literal["check_metrics"] = "check_metrics"
    service: str = Field(..., description="The service to check metrics for.")

class ReadLogsAction(BaseAction):
    action: Literal["read_logs"] = "read_logs"
    service: str = Field(..., description="The service to read logs from.")
    lines: int = Field(..., description="Number of lines to read.")

class ExecuteRemediationAction(BaseAction):
    action: Literal["execute_remediation"] = "execute_remediation"
    remediation_action: str = Field(..., description="The remediation action to execute.")

class ResolveTicketAction(BaseAction):
    action: Literal["resolve_ticket"] = "resolve_ticket"
    root_cause: str = Field(..., description="The identified root cause of the incident.")

# Define the overall Action type as a discriminated union
Action = Annotated[
    Union[CheckMetricsAction, ReadLogsAction, ExecuteRemediationAction, ResolveTicketAction],
    Field(discriminator="action")
]
