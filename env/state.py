from typing import List


class EnvState:
    def __init__(self):
        self.issue: str = ""
        self.logs: str = ""
        self.root_cause: str = ""
        self.solution_patterns = []

        # keywords used for grading
        self.solution_keywords: List[str] = []
        self.diagnosis_keywords: List[str] = []

        # interaction tracking
        self.history: List[str] = []
        self.steps: int = 0

        # episode control
        self.done: bool = False