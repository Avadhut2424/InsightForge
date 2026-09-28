# Ollama Local LLM Setup

To ensure fully grounded results on large context tasks, we use `llama3.1-8k`, a configuration of `llama3.1:8b` with an 8192 context window and temperature set to 0 for determinism.

## How to create `llama3.1-8k`

1. Install [Ollama](https://ollama.com/) on your host machine.
2. Ensure you have the base model downloaded:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Create the custom model using the provided Modelfile:
   ```bash
   cd ollama
   ollama create llama3.1-8k -f Modelfile
   ```
4. Verify the model exists and has the correct context window:
   ```bash
   ollama show llama3.1-8k --parameters
   ```

## Configuration

In your `.env` file, ensure you have the following settings:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_MODEL=llama3.1-8k
```

## Model Keep-Alive Recommendation

By default, Ollama unloads models from memory after 5 minutes of inactivity, which causes subsequent requests to incur significant "cold-start" loading latency (tens of seconds).

To keep the model resident in memory across pipeline passes, set the `OLLAMA_KEEP_ALIVE` environment variable on the host running the Ollama service:

- **Windows (PowerShell)**:
  ```powershell
  [System.Environment]::SetEnvironmentVariable('OLLAMA_KEEP_ALIVE', '30m', 'User')
  ```
  Or launch the Ollama service with:
  ```powershell
  $env:OLLAMA_KEEP_ALIVE="30m"; ollama serve
  ```
- **Linux / macOS**:
  ```bash
  export OLLAMA_KEEP_ALIVE="30m"
  # Or configure systemd override:
  # Environment="OLLAMA_KEEP_ALIVE=30m"
  ```

Additionally, a warm-up call (`warm_up_llm()`) should be executed during application startup to preemptively load weights before user queries arrive.

