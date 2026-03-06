from cldk.analysis.c.c_analysis import CAnalysis
from cldk.analysis.c.registry import CCodebase, analysis_registry
from pathlib import Path

example_codebase = CCodebase(root=Path("example_projects/"))
hb_codebase = CCodebase(
    name="hostboot_bootloader",
    root=Path("../../../../PowerPC/hostboot/src/bootloader/"),
)

## NOTE: set different ones depending on what you're testing
# project = hb_project
test_codebase = example_codebase

c_a: CAnalysis = test_codebase.analysis
print(f"From: test_c_analysis.py; line number: 7; INITIALIZED")

app = c_a.c_application

assert app == analysis_registry.get(test_codebase.root).c_application

results_file = f"{test_codebase.name}_resulting_app.json"
with open(results_file, "w") as f:
    f.write(app.model_dump_json(indent=2))

print(f"DONE writing results to {results_file}")

# print(f"app : \n{app.model_dump_json(indent=2)}")
print(f"(wrote results to {results_file})")
