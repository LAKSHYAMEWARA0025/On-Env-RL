# OnCall-Env: The L1 SRE Simulator

## 🚨 The Problem
Large Language Models struggle with delayed feedback and multi-step diagnostic reasoning. In the real world, Site Reliability Engineers (SREs) do not solve incidents by generating a single paragraph of text; they iteratively query metrics, read logs, form hypotheses, and execute commands. 

`OnCall-Env` is an OpenEnv-compliant simulation that trains and evaluates an LLM's ability to navigate a partially observable server environment to resolve active incidents, pushing beyond shallow next-token prediction into true world modeling.

## 🛠️ The Environment
* **Observation Space:** A structured JSON object containing the active alert, system time, and the output of the last executed tool.
* **Action Space:** `check_metrics(service)`, `read_logs(service, lines)`, `execute_remediation(action)`, and `resolve_ticket(root_cause)`.
* **The Hidden State:** A persistent engine tracks CPU, RAM, Disk, and service health. 
* **Reward Shaping:** Agents receive micro-rewards (+0.1) for finding error logs, heavy penalties (-0.5) for destructive actions taken without checking logs first, and a final scaled score based on how cleanly they resolved the ticket.

## 📊 Baseline Inference Results
We ran the baseline `inference.py` script using the `MiniMax-M2.7` model. The agent successfully navigated the environment, taking appropriate penalties for blind actions before correcting its behavior:

* **Task 1 (Easy - Disk Full):** Final Score `0.9`
* **Task 2 (Medium - Memory Leak):** Final Score `0.85`
* **Task 3 (Hard - Cascading DB Failure):** Final Score `0.95`

## 🚀 Setup & Execution
1. Clone the repository.
2. Build the Docker container: `docker build -t oncall-env .`
3. Run the inference baseline: 
   ```bash
   export API_BASE_URL="..."
   export MODEL_NAME="..."
   export HF_TOKEN="..."
   python inference.py