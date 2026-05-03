# `dolores`
An AI agent that proactively finds and fixes bugs based on open source intelligence. 

## Quickstart
**Step 1.** Clone the Dolores GitHub repository. 
```bash
git clone https://github.com/deathlabs/dolores.git
```

**Step 2.** Change directories to the folder downloaded.
```bash
cd dolores
```

**Step 3.** Then, build Dolores locally using the provided Makefile. 
```bash
make
```

**Step 4.** Save your environment variables (e.g., OpenAI API key) to a file called `.env` in the `inference` folder. 
```bash
echo "export OPENAI_API_KEY='abc...'" > inference/.env
```

**Step 5.** Start Dolores using the provided Makefile. 
```bash
make start
```
