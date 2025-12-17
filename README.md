# Asyncroscopy:
Enabling smart microscopy via asynchronous servers

![Structure Diagram](structure_overview.png)

## Environment setup

`uv sync` will now install only the open-source dependencies so the command works even
when the Thermo Fisher AutoScript wheels are not available in the repository. If you
need AutoScript support, download the vendor wheels into an `AS_1.14_wheels/`
directory at the project root and install the optional group:

```bash
uv sync --group autoscript
```

`uv` resolves the AutoScript packages from the local wheels configured in
`pyproject.toml`, so missing wheels previously caused `uv sync` to fail. Keeping them
in an optional dependency group avoids that failure while still allowing users with the
wheels to opt in to the extra functionality.
