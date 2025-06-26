"""Generate the code reference pages."""
import os
from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()


root = Path(__file__).parent.parent.parent
print(root)
src = root / "sensor_portal"
print(src)

for path in sorted(src.rglob("*.py")):

    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__" and "migrations" not in parts and "management" not in parts and "sensor_portal" not in parts:
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__" or "migrations" in parts or\
        "tests" in parts or "asgi" in parts or "manage" in parts\
            or "conftest" in parts or "handlers" in parts or\
            "apps" in parts or "admin" in parts or\
        "wsgi" in parts or "exceptions" in parts or\
            "forms" in parts or "api" in parts or "urls" in parts or\
        "settings" in parts or "celery" in parts or\
            "middleware" in parts or "factories" in parts or\
            "permissions" in parts or "serializers_fake" in parts or "management" in parts or "sensor_portal" in parts\
            or "schema" in parts or "test_fixtures" in parts:
        continue

    print(doc_path)
    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, Path("../") / path)

print(nav.__dict__)
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
