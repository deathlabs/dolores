# `dolores`
[![CI Pipeline](https://github.com/deathlabs/dolores/actions/workflows/check.yml/badge.svg)](https://github.com/deathlabs/dolores/actions/workflows/check.yml)  
Build and deliver secure software on GitHub or GitLab without drowning in vulnerability management.

## Delivering
**Step 1.** Text goes here.
```bash
kind load docker-image dolores/database:latest -n demo-cluster
```

## Deploying  
**Step 1.** Text goes here.  
```bash
kubectl create namespace dolores
```

**Step 2.** Text goes here.  
```bash
helm install dolores-database . -n dolores
```

**Step 3.** Text goes here.
```bash
helm install dolores-backend . -n dolores
```

## Removing
**Step 1.** Text goes here.  
```bash
helm uninstall dolores-backend -n dolores
helm uninstall dolores-database -n dolores
```
