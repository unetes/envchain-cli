# envchain-cli

> Manage per-project environment variable chains with inheritance and override support.

---

## Installation

```bash
pip install envchain-cli
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envchain-cli
```

---

## Usage

Define environment chains in a `.envchain.yml` file at your project root:

```yaml
base:
  DATABASE_URL: postgres://localhost/mydb
  DEBUG: "false"

development:
  inherits: base
  DEBUG: "true"
  LOG_LEVEL: verbose

production:
  inherits: base
  DATABASE_URL: postgres://prod-host/mydb
```

Then load a chain into your shell or a subprocess:

```bash
# Export variables for the 'development' chain
envchain load development

# Run a command with the 'production' chain applied
envchain run production -- python manage.py migrate
```

Override any variable on the fly:

```bash
envchain run development --set LOG_LEVEL=debug -- python app.py
```

List all defined chains and their resolved variables:

```bash
envchain list
envchain inspect production
```

---

## License

This project is licensed under the [MIT License](LICENSE).