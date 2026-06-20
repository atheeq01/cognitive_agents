import os
import sys

api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "apps/api"))
if api_path not in sys.path:
    sys.path.append(api_path)

try:
    from app.agents.contradiction_pipeline.project_synthesis_agent import project_synthesis_agent
    print("SUCCESS: Synthesis Agent Imported")
except Exception as e:
    import traceback
    traceback.print_exc()
