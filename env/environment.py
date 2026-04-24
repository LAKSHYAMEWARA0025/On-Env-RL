from models.observation import Observation
from models.action import Action
from models.reward import Reward

from env.state import EnvState
from env.reward import compute_reward

from tasks.easy import PortInUseTask


class DevSupportEnv:
    def __init__(self):
        self._state = None
        self.current_task = None

    # -------------------------
    # RESET
    # -------------------------
    def reset(self) -> Observation:
        self._state = EnvState()

        # For now: always load easy task
        self.current_task = PortInUseTask()

        # Populate state from task
        self._state.issue = self.current_task.get_issue()
        self._state.logs = self.current_task.get_logs()
        self._state.root_cause = self.current_task.get_root_cause()
        self._state.solution_keywords = self.current_task.get_solution_keywords()
        self._state.diagnosis_keywords = self.current_task.get_diagnosis_keywords()
        self._state.solution_patterns = self.current_task.get_solution_patterns()
        return Observation(
            issue=self._state.issue,
            logs=self._state.logs,
            history=[]
        )

    # -------------------------
    # STEP
    # -------------------------
    def step(self, action: Action):
        if self._state is None:
            raise ValueError("Environment not initialized. Call reset() first.")

        if self._state.done:
            raise ValueError("Episode already finished. Call reset().")

        # Update state
        self._state.steps += 1
        self._state.history.append(action.content)

        # Compute reward
        reward: Reward = compute_reward(action.content, self._state)

        # Done condition
        done = False

        # Success condition
        if reward.score >= 0.8:
            done = True

        # Max steps condition
        if self._state.steps >= 3:
            done = True

        self._state.done = done

        # Return new observation
        observation = Observation(
            issue=self._state.issue,
            logs=self._state.logs,
            history=self._state.history
        )

        return observation, reward, done, {}

    # -------------------------
    # STATE
    # -------------------------
    def state(self) -> EnvState:
        return self._state