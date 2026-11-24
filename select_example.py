# Selects the sketch to build: PlatformIO builds one source folder per project,
# so this script points it to lectures/**/<name>/ or projects/**/<name>/.
# The name comes from MIMIC_EXAMPLE (VS Code task) or custom_example (env).
Import("env")
import os

example = os.environ.get("MIMIC_EXAMPLE") or env.GetProjectOption("custom_example", "")
if not example:
    raise SystemExit("No sketch selected. Set custom_example or MIMIC_EXAMPLE.")
project = env.subst("$PROJECT_DIR")
found = []
for top in ("lectures", "projects"):
    for d, dirs, files in os.walk(os.path.join(project, top)):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        if os.path.basename(d) == example and example + ".ino" in files:
            found.append(d)
if len(found) != 1:
    raise SystemExit(f"Sketch not found (or not unique): {example} {found}")
env.Replace(PROJECT_SRC_DIR=found[0])
print(f"*** Building sketch: {os.path.relpath(found[0], project)}")
