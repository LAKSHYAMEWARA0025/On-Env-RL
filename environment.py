import json
from typing import Dict, Any
from openenv_core.env_server import Environment
from models import Observation, Action
from tasks import grade_easy_task, grade_medium_task, grade_hard_task

class OnCallEnvironment(Environment):
    """
    OnCall-Env: The L1 SRE Simulator
    """
    
    def __init__(self):
        super().__init__()
        self._hidden_state: Dict[str, Any] = {}
        self.time_step = 0
        
    def reset(self, task_id: str = "easy") -> Observation:
        """
        Resets the environment to an initial state based on task_id ('easy', 'medium', 'hard').
        """
        self.time_step = 0
        
        # Base infrastructure state
        self._hidden_state = {
            "task_id": task_id,
            "services": {
                "frontend": {"cpu": 10, "ram": 45, "disk": 30, "status": "healthy"},
                "backend": {"cpu": 15, "ram": 50, "disk": 40, "status": "healthy"},
                "database": {"cpu": 5, "ram": 20, "disk": 40, "status": "healthy"}
            },
            "resolved": False,
            "history": [],
            "root_cause": None,
            "logs_read": [],
            "discovered_anomalies": False
        }
        
        active_alert = ""
        
        if task_id == "easy":
            # Disk Full: Database disk 100%
            self._hidden_state["services"]["database"]["disk"] = 100
            self._hidden_state["services"]["backend"]["status"] = "failing"
            active_alert = "Web server HTTP 500s"
            
        elif task_id == "medium":
            # Memory Leak: Backend worker restarting
            self._hidden_state["services"]["backend"]["ram"] = 99
            self._hidden_state["services"]["backend"]["status"] = "crash_loop"
            active_alert = "Background worker service keeps restarting"
            
        elif task_id == "hard":
            # Cascading DB: DB connection pool full
            self._hidden_state["services"]["database"]["status"] = "pool_exhausted"
            self._hidden_state["services"]["backend"]["status"] = "timeout"
            active_alert = "Frontend is slow"

        return Observation(
            active_alert=active_alert,
            time=f"T+{self.time_step}m",
            last_output="Environment initialized.",
            reward=0.0,
            done=False
        )
        
    def step(self, action: Action) -> Observation:
        """
        Executes an action in the environment and returns observation with intermediate reward.
        """
        self.time_step += 1
        last_output = ""
        task_id = self._hidden_state.get("task_id", "easy")
        
        # Re-determine active alert based on task_id
        active_alert = ""
        if task_id == "easy":
            active_alert = "Web server HTTP 500s"
        elif task_id == "medium":
            active_alert = "Background worker service keeps restarting"
        elif task_id == "hard":
            active_alert = "Frontend is slow"

        # Log action to history
        self._hidden_state["history"].append(action.dict())
        
        step_reward = 0.0
        done = False

        # Action handling using the Pydantic action discriminator
        if action.action == "check_metrics":
            service = action.service
            if service in self._hidden_state["services"]:
                metrics = self._hidden_state["services"][service]
                last_output = json.dumps(metrics, indent=2)
                
                # Reward for discovering anomalous metrics
                is_anomalous = (metrics["cpu"] >= 80 or metrics["ram"] >= 80 or 
                                metrics["disk"] >= 80 or metrics["status"] != "healthy")
                if is_anomalous and not self._hidden_state["discovered_anomalies"]:
                    step_reward += 0.1
                    self._hidden_state["discovered_anomalies"] = True
            else:
                last_output = f"Error: Service '{service}' not found."
                step_reward -= 0.1  # Penalty for wasted tool call
                
        elif action.action == "read_logs":
            service = action.service
            if service not in self._hidden_state["services"]:
                last_output = f"Error: Service '{service}' not found."
                step_reward -= 0.1  # Penalty for wasted tool call
            else:
                if service not in self._hidden_state["logs_read"]:
                    self._hidden_state["logs_read"].append(service)
                    
                # Predefined logs based on task and service
                if task_id == "easy":
                    if service == "database":
                        if self._hidden_state["services"]["database"]["disk"] >= 100:
                            last_output = "ERROR: No space left on device\nFATAL: cannot write to WAL"
                        else:
                            last_output = "INFO: database ready to accept connections"
                    elif service == "backend":
                        last_output = "ERROR: connection to database failed - timeout"
                    else:
                        last_output = "INFO: GET / 200 OK"
                        
                elif task_id == "medium":
                    if service == "backend":
                        if self._hidden_state["services"]["backend"]["ram"] >= 90:
                            last_output = "WARN: Memory usage high\nFATAL: OOM Killed"
                        else:
                            last_output = "INFO: Worker process started"
                    else:
                        last_output = "INFO: Service healthy"
                        
                elif task_id == "hard":
                    if service == "frontend":
                        last_output = "WARN: upstream request timeout to backend API"
                    elif service == "backend":
                        last_output = "ERROR: DB Connection Timeout"
                    elif service == "database":
                        if self._hidden_state["services"]["database"]["status"] == "pool_exhausted":
                            last_output = "ERROR: Max connections reached"
                        else:
                            last_output = "INFO: Connection accepted"
                            
                # Reward for discovering anomalous logs
                error_keywords = ["oom", "no space left", "timeout", "error", "fatal"]
                if any(kw in last_output.lower() for kw in error_keywords) and not self._hidden_state["discovered_anomalies"]:
                    step_reward += 0.1
                    self._hidden_state["discovered_anomalies"] = True
                            
        elif action.action == "execute_remediation":
            remediation = action.remediation_action.lower()
            
            # Identify target service to enforce logs_read penalty
            target_service = None
            if task_id == "easy":
                target_service = "database"
            elif task_id == "medium":
                target_service = "backend"
            elif task_id == "hard":
                target_service = "database"
                
            if target_service and target_service not in self._hidden_state["logs_read"]:
                step_reward -= 0.5  # Severe penalty for remediating blindly without reading logs
                
            if task_id == "easy" and ("disk" in remediation or "clear" in remediation or "scale" in remediation):
                self._hidden_state["services"]["database"]["disk"] = 50
                self._hidden_state["services"]["backend"]["status"] = "healthy"
                last_output = "SUCCESS: Remediation applied. Disk usage reduced."
            elif task_id == "medium" and ("rollback" in remediation or "scale" in remediation or "restart" in remediation):
                self._hidden_state["services"]["backend"]["ram"] = 50
                self._hidden_state["services"]["backend"]["status"] = "healthy"
                last_output = "SUCCESS: Remediation applied. Service stabilized."
            elif task_id == "hard" and ("connection" in remediation or "pool" in remediation or "increase" in remediation):
                self._hidden_state["services"]["database"]["status"] = "healthy"
                self._hidden_state["services"]["backend"]["status"] = "healthy"
                last_output = "SUCCESS: Remediation applied. Connection pool increased."
            else:
                last_output = f"Executed '{action.remediation_action}'. No apparent effect."
                
        elif action.action == "resolve_ticket":
            self._hidden_state["resolved"] = True
            self._hidden_state["root_cause"] = action.root_cause
            last_output = f"Ticket resolved. Root cause submitted: {action.root_cause}"
            
            # Final scoring
            done = True
            if task_id == "easy":
                step_reward = grade_easy_task(self._hidden_state)
            elif task_id == "medium":
                step_reward = grade_medium_task(self._hidden_state)
            elif task_id == "hard":
                step_reward = grade_hard_task(self._hidden_state)

        return Observation(
            active_alert=active_alert,
            time=f"T+{self.time_step}m",
            last_output=last_output,
            reward=step_reward,
            done=done
        )
        
    def state(self) -> Dict[str, Any]:
        """
        Returns the persistent hidden state of the infrastructure.
        """
        return self._hidden_state
