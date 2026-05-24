# OpenBlox

OpenBlox is a local Roblox Studio assistant built around a FastAPI backend and a static web client. It is designed to help with Roblox-focused chat, Luau scripting, documentation lookup, context management, and optional MCP-based Roblox Studio integration.

## What it does

- Runs a local web app at `http://localhost:8520`
- Stores chat sessions per conversation
- Saves API settings, model selection, search settings, and user context
- Supports a Roblox Studio MCP integration for tool calls
- Supports optional advanced self-review and automatic context compaction
- Streams responses to the browser UI
- Image upload for vision models (drag & drop or upload button)
- 22+ AI providers: Kilo, OpenAI, DeepSeek, OpenRouter, NVIDIA NIM, Groq, Together, Fireworks, Mistral, xAI, Perplexity, Cerebras, SambaNova, DeepInfra, Novita, MiniMax, AI21, Moonshot, DashScope, LM Studio, vLLM, and Ollama (local)
- All OpenAI-compatible providers auto-fill their endpoint from presets

## Architecture

- `server.py`: FastAPI app and API routes
- `frontend/`: static HTML/CSS/JS web client
- `openblox_client.py`: chat completion client with provider presets, tool/review loop, and retry with exponential backoff
- `tools_manager.py`: built-in tool state and MCP client lifecycle
- `chat_store.py`: session persistence
- `website_manager.py`: config and website source persistence
- `installer.py`: GUI and terminal installer/updater
- `openblox_update_and_run.bat`: Windows update + install + launch helper

## Requirements

- Windows
- Python 3.11+ recommended
- Internet access for the AI API and optional documentation lookups
- Roblox Studio MCP installed locally if you want tool integration

## Install

```bash
git clone https://github.com/Artemcik5/OpenBlox.git
cd OpenBlox
python -m pip install -r requirements.txt
python run.py
```

Then open [http://localhost:8520](http://localhost:8520).

## Windows helper

If you want a one-click update/install flow on Windows, run:

```bat
openblox_update_and_run.bat
```

This batch file:

- upgrades `pip`
- installs `requirements.txt`
- runs `installer.py` in terminal mode
- launches `run.py` in a visible terminal window

## Updating

You can update in two ways:

1. Run `openblox_update_and_run.bat`
2. Run `installer.py` directly

Examples:

```bash
python installer.py
```

```bash
python installer.py --terminal --path "C:\path\to\OpenBlox" --launch
```

The updater preserves only repo assets that belong in the install folder. User data is stored in AppData, so updating does not depend on keeping local `config.json` or `chats/` inside the repository.

## Data storage

OpenBlox stores user data in AppData:

- Config and API settings: `%APPDATA%\OpenBlox\config.json`
- Chat sessions: `%APPDATA%\OpenBlox\chats\`

On startup, OpenBlox will migrate older repo-local `config.json` and `chats/` data into AppData if present.

## Provider configuration

OpenBlox supports 22 AI providers. Most are OpenAI-compatible:

| Provider | Default Endpoint | API Key Required |
|---|---|---|
| Kilo AI | `https://api.kilo.ai/api/gateway/chat/completions` | Yes |
| OpenAI | `https://api.openai.com/v1/chat/completions` | Yes |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | Yes |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | Yes |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1/chat/completions` | Yes |
| Groq | `https://api.groq.com/openai/v1/chat/completions` | Yes |
| Together AI | `https://api.together.xyz/v1/chat/completions` | Yes |
| Fireworks AI | `https://api.fireworks.ai/inference/v1/chat/completions` | Yes |
| Mistral AI | `https://api.mistral.ai/v1/chat/completions` | Yes |
| xAI Grok | `https://api.x.ai/v1/chat/completions` | Yes |
| Perplexity | `https://api.perplexity.ai/chat/completions` | Yes |
| Cerebras | `https://api.cerebras.ai/v1/chat/completions` | Yes |
| SambaNova | `https://api.sambanova.ai/v1/chat/completions` | Yes |
| DeepInfra | `https://api.deepinfra.com/v1/openai/chat/completions` | Yes |
| Novita AI | `https://api.novita.ai/v3/openai/chat/completions` | Yes |
| MiniMax | `https://api.minimaxi.chat/v1/chat/completions` | Yes |
| AI21 Labs | `https://api.ai21.com/studio/v1/chat/completions` | Yes |
| Moonshot / Kimi | `https://api.moonshot.ai/v1/chat/completions` | Yes |
| Qwen / DashScope | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | Yes |
| LM Studio (local) | `http://localhost:1234/v1/chat/completions` | No |
| vLLM (local) | `http://localhost:8000/v1/chat/completions` | No |
| Ollama (local) | Custom endpoint | No |

When you select a provider, the endpoint auto-fills from presets. You can also enter a custom endpoint for any OpenAI-compatible API.

## Current behavior

- The backend binds to `127.0.0.1:8520`
- CORS is restricted to `http://localhost:8520` and `http://127.0.0.1:8520`
- The frontend is served directly by FastAPI using `StaticFiles`
- Sessions are saved as JSON files
- Advanced thinking performs at most one internal review pass for substantive answers
- MCP tools are exposed only when enabled in a session
- API calls retry up to 10 times with exponential backoff on rate limits (429), timeouts, and 5xx errors
- Image uploads limited to 21MB per file (PNG, JPEG, GIF, WebP, BMP)
- First launch shows a setup wizard if no config is found or config has `"unconfigured": true`
- API key field uses CSS-masked text to avoid triggering browser password managers

## Development notes

- `run.py` starts the local server
- `requirements.txt` contains the Python dependencies
- The frontend is plain HTML/CSS/JavaScript, not a bundled SPA framework
- The default model is `nvidia/nemotron-3-super-120b-a12b:free`

## Known limitations

- This project is Roblox-specific by design and will redirect non-Roblox questions
- There is no login/auth system because the app is intended for local use
- Session storage is file-based rather than database-backed
- MCP availability depends on the local Roblox MCP setup
- There is no packaged executable in the repository yet
- Not all providers support model listing; for those that don't, a fallback model list is shown

## Contributing

Contributions are welcome.

Typical workflow:

1. Fork the repository
2. Create a branch
3. Make your changes
4. Test locally
5. Open a pull request

## License

This project is licensed under the terms of the included [LICENSE](./LICENSE).
