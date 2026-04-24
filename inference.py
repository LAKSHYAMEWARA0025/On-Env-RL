import os
import json
from openai import OpenAI
from environment import OnCallEnvironment
from models import CheckMetricsAction, ReadLogsAction, ExecuteRemediationAction, ResolveTicketAction

def main():
    # Initialize from required environment variables
    api_base_url = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME", "gpt-4-turbo")
    hf_token = os.environ.get("HF_TOKEN")

    # The prompt explicitly asks to map HF_TOKEN to the api_key parameter
    client = OpenAI(
        base_url=api_base_url,
        api_key=hf_token
    )
    
    env = OnCallEnvironment()
    
    # Define tool schemas for the LLM
    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_metrics",
                "description": "Check the metrics (cpu, ram, disk) for a specific service.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "The service name, e.g., 'frontend', 'backend', 'database'."}
                    },
                    "required": ["service"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_logs",
                "description": "Read the logs for a specific service. You must read logs before remediating.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "The service name."},
                        "lines": {"type": "integer", "description": "Number of lines to read."}
                    },
                    "required": ["service", "lines"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_remediation",
                "description": "Execute a remediation action to fix the incident.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "remediation_action": {"type": "string", "description": "Action string like 'scale up disk', 'restart service', 'increase db connection pool'."}
                    },
                    "required": ["remediation_action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "resolve_ticket",
                "description": "Resolve the ticket once the issue is fixed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root_cause": {"type": "string", "description": "The root cause of the incident."}
                    },
                    "required": ["root_cause"]
                }
            }
        }
    ]

    tasks = ['easy', 'medium', 'hard']
    max_steps = 15

    for task_id in tasks:
        # CRITICAL LOGGING: [START]
        print(f"[START] Task: {task_id}")
        
        obs = env.reset(task_id=task_id)
        
        system_prompt = (
            "You are an L1 Site Reliability Engineer fixing active incidents. "
            "You must use tools to check metrics, read logs, execute remediations, and resolve the ticket. "
            "CRITICAL: Always read logs BEFORE executing a remediation, or you will be heavily penalized. "
            "Available services: 'frontend', 'backend', 'database'. "
            "Always call exactly one tool per turn. When you believe the issue is fixed, use resolve_ticket."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Active Alert: {obs.active_alert}\nTime: {obs.time}\nLast Output: {obs.last_output}"}
        ]
        
        step_count = 0
        done = False
        final_score = 0.0
        
        while not done and step_count < max_steps:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            except Exception as e:
                # If there's an API error (e.g. invalid base url/key), we break gracefully
                print(f"API Error: {e}")
                break
            
            choice = response.choices[0]
            message = choice.message
            messages.append(message)
            
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                action_name = tool_call.function.name
                
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                
                # Execute action in environment
                if action_name == "check_metrics":
                    action = CheckMetricsAction(**args)
                elif action_name == "read_logs":
                    # provide default lines if LLM omits it
                    action = ReadLogsAction(service=args.get("service", "unknown"), lines=args.get("lines", 10))
                elif action_name == "execute_remediation":
                    action = ExecuteRemediationAction(**args)
                elif action_name == "resolve_ticket":
                    action = ResolveTicketAction(**args)
                else:
                    # Fallback for hallucinated tools
                    action = ResolveTicketAction(root_cause="Hallucinated tool call")
                
                obs = env.step(action)
                
                # CRITICAL LOGGING: [STEP]
                print(f"[STEP] Action: {action.action} | Reward: {obs.reward}")
                
                if obs.done:
                    done = True
                    final_score = obs.reward
                    
                tool_result_content = f"Time: {obs.time}\nOutput: {obs.last_output}\nReward: {obs.reward}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_content
                })
            else:
                # Agent didn't call a tool
                print(f"[STEP] Action: none | Reward: 0.0")
                messages.append({
                    "role": "user",
                    "content": "You must call a tool. If finished, call resolve_ticket."
                })
            
            step_count += 1
            
        # CRITICAL LOGGING: [END]
        print(f"[END] Final Score: {final_score}")

if __name__ == "__main__":
    main()
