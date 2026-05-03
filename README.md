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

**Step 4.** Save your environment variables (e.g., OpenAI API key) to a file called `.env` in the `inference` folder. This implies you have already [requested an API key](https://nvd.nist.gov/developers/request-an-api-key) from National Institute of Standards and Technology (NIST) to interact with the National Vulnerability Database for Common Vulnerabilities and Exposures (CVE).
```bash
echo "export OPENAI_API_KEY='AAA...'" > inference/.env
echo "export NVD_API_KEY='BBB...'" > inference/.env
```

**Step 5.** Start Dolores using the provided Makefile. 
```bash
make start
```
