from cldk.analysis.c.c_analysis import CAnalysis
from cldk.analysis.c.registry import analysis_registry as registry
from pathlib import Path
from typing import NamedTuple


class Project(NamedTuple):
    name: str
    root: Path


ex_project = Project("example", Path("example_projects/"))
hb_project = Project(
    "hostboot_bootloader",
    Path("/Users/andrewjda/LLMs/PowerPC/hostboot/src/bootloader/"),
)
# project = hb_project
project = ex_project

c_a = registry.get_analysis(project.root)
print(f"From: test_c_analysis.py; line number: 7; INITIALIZED")

app = c_a.c_application

assert app == registry.get_analysis(project.root).c_application
results_file = f"{project.name}_resulting_app.json"
with open(results_file, "w") as f:
    f.write(app.model_dump_json(indent=2))

print(f"DONE writing results to {results_file}")

print(f"app : \n{app.model_dump_json(indent=2)}")
print(f"(wrote results to {results_file})")
