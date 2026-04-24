from openenv_core.env_server import create_web_interface_app
from environment import OnCallEnvironment
from models import Action, Observation 

# Pass the class directly to the web app, NOT an instance!
app = create_web_interface_app(OnCallEnvironment, Action, Observation)