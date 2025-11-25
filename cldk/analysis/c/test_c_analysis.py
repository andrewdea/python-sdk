from cldk.analysis.c.c_analysis import CAnalysis
from pathlib import Path

project_dir = Path("example_projects/")
c_a = CAnalysis(project_dir=project_dir)
print(f"From: test_c_analysis.py; line number: 7; INITIALIZED")

app = c_a.c_application

print(f"app.call_graph : {app.call_graph}")
