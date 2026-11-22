# Audit site-packages .pth startup hooks in coding-agent Python environments

**Checked on:** Socket security advisory and Python 3 `site` module documentation, 2026-11-19

## What goes wrong

Python executes lines starting with `import` inside any `.pth` file found in `site-packages` during interpreter startup via the `site` module. A compromised wheel can therefore run on every `python` invocation in an agent virtual environment even if your project never imports that package.

In the November 17 compromise of Microsoft's `agent-framework` PyPI package (versions `1.26.1` and `1.26.2`), `agent_framework_meta.pth` and `af_runtime_diag.pth` launched background credential harvesting on startup, reading `/proc/*/environ`, `~/.azure/*.json`, and environment keys matching `OPENAI`, `AWS`, `GITHUB`, and `AZURE`. Version `1.26.2` restored `agent_framework_meta/__init__.py` byte-for-byte while hiding execution in `af_runtime_diag.py`, so checking only the package `__init__.py` missed the payload.

## Fix

Scan every active `site-packages` directory for `.pth` files containing executable `import` lines, and verify installed versions against known compromised releases:

```bash
python3 -c '
import pathlib, site
roots = [pathlib.Path(p) for p in site.getsitepackages() + [site.getusersitepackages()]]
for root in roots:
    if not root.is_dir():
        continue
    for pth in sorted(root.glob("*.pth")):
        for lineno, line in enumerate(pth.read_text(errors="ignore").splitlines(), 1):
            if line.startswith(("import ", "import\t")):
                print(f"{pth}:{lineno}: {line}")
'
```

If an unexpected `.pth` import or an affected release (`agent-framework` `1.26.1` or `1.26.2`) is present, remove the package, recreate the virtual environment from pinned hashes, and rotate any credentials reachable from that environment.

## Source

- https://socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer: "The Microsoft agent-framework PyPI package was compromised on November 17th, affecting versions 1.26.1 and 1.26.2. Both versions install Python startup hooks that silently collect credentials, environment data, and cloud identity tokens"
- https://socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer: "On Python startup, the .pth file imports a module that launches collection in a background process/thread. Version 1.26.1 routes through agent_framework_meta.pth"
- https://socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer: "The legitimate package initializer is restored byte-for-byte, so inspecting only agent_framework_meta/__init__.py misses this version."
- https://socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer: "Avoid installing either version; if installed, remove them and rotate potentially exposed credentials."
- https://docs.python.org/3/library/site.html: "For backward compatibility, lines starting with import (followed by space or tab) are executed with exec()"

---

[All verified fixes & 1-command config auditor](../README.md)
