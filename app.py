from openenv_core.env_server import create_web_interface_app
from environment import OnCallEnvironment

# REPLACE THESE with the actual class names from your models.py!
from models import Action, Observation 

# Instantiate your environment
env = OnCallEnvironment()

# Wrap it in OpenEnv's built-in FastAPI web server
app = create_web_interface_app(env, Action, Observation)