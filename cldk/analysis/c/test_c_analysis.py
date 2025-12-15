from cldk.analysis.c.c_analysis import CAnalysis
from pathlib import Path

project_dir = Path("example_projects/")
c_a = CAnalysis(project_dir=project_dir)
print(f"From: test_c_analysis.py; line number: 7; INITIALIZED")

app = c_a.c_application

results_file = "resulting_app.json"
with open(results_file, "w") as f:
    f.write(app.model_dump_json(indent=2))

print(f"app : {app.model_dump_json(indent=2)}")
