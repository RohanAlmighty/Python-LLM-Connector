# Python LLM Connector

A small CLI for sending prompts to OpenAI-compatible cloud or local LLM providers.

## Setup

Install the OpenAI SDK:

```powershell
python -m pip install -r requirements.txt
```

Copy the example environment file and add your Groq API key if needed:

```powershell
Copy-Item .env.example .env
```

In VS Code, `"python.terminal.useEnvFile": true` in `.vscode/settings.json` passes
`.env` variables to Python terminals. Set `LLM_PROVIDER=groq` and `GROQ_API_KEY`
in `.env` to use Groq; reload the terminal after changing `.env`.

Ollama is the default provider. Start Ollama and make sure the configured model is
available before using it.

Provider URLs, default models, and API-key environment variable names are defined
in `providers.json`. Keep real API keys in environment variables, not in this file.

## Usage

Run without arguments to enter a prompt interactively:

```powershell
python llm_connector.py
```

Or pass a prompt and choose a provider or model:

```powershell
python llm_connector.py "Explain how rainbows form."
python llm_connector.py --provider groq "Explain how rainbows form."
python llm_connector.py --provider ollama --model phi4-mini "Explain how rainbows form."
```

The CLI displays the prompt, response, response time, and token counts when the
provider returns usage data. Run `python llm_connector.py --help` for options.
