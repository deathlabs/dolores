# `dolores`

**How Do I Add a VEX Document?**  
If you need to create a VEX document for the `tools` container regarding the applicability of `GHSA-vj7q-gjh5-988w` in `pypi/mcp@1.28.0`, you would run the command below.
```bash
vexctl create \
    --author "Victor Fernandez III" \
    --product="pkg:pypi/mcp@1.28.0" \
    --vuln="GHSA-vj7q-gjh5-988w" \
    --status="not_affected" \
    --justification="vulnerable_code_not_in_execute_path" > .github/vex/tools-vex.json 
```
