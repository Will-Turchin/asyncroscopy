# Asyncroscopy:
Enabling smart microscopy via asynchronous servers

![Structure Diagram](structure_overview.png)

## Environment setup

`uv sync` installs only the open-source dependencies, so the command works even when
the Thermo Fisher AutoScript wheels are not present. If you need AutoScript support,
download the vendor wheels into an `AS_1.14_wheels/` directory at the project root and
install the optional group (the exact wheel names below must exist in that folder):

```bash
uv sync --group autoscript
```

The AutoScript dependency group points directly to the wheel files under
`AS_1.14_wheels/`. Running `uv sync` without `--group autoscript` no longer probes the
missing files, which avoids the previous "Distribution not found" errors on machines
that do not have access to the vendor wheels.
