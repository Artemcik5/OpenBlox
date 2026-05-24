import json
import time
from typing import Optional

import requests


OLLAMA_COMPLETIONS = "/v1/chat/completions"
OLLAMA_TAGS = "/api/tags"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
DEFAULT_OLLAMA_MODEL = "llama3.2"

PROVIDER_PRESETS = {
    "kilo":          {"endpoint": "https://api.kilo.ai/api/gateway/chat/completions", "models_endpoint": "https://api.kilo.ai/api/gateway/models"},
    "openai":        {"endpoint": "https://api.openai.com/v1/chat/completions", "models_endpoint": "https://api.openai.com/v1/models"},
    "deepseek":      {"endpoint": "https://api.deepseek.com/v1/chat/completions", "models_endpoint": "https://api.deepseek.com/v1/models"},
    "openrouter":    {"endpoint": "https://openrouter.ai/api/v1/chat/completions", "models_endpoint": "https://openrouter.ai/api/v1/models"},
    "nvidia":        {"endpoint": "https://integrate.api.nvidia.com/v1/chat/completions", "models_endpoint": "https://integrate.api.nvidia.com/v1/models"},
    "moonshot":      {"endpoint": "https://api.moonshot.ai/v1/chat/completions", "models_endpoint": "https://api.moonshot.ai/v1/models"},
    "groq":          {"endpoint": "https://api.groq.com/openai/v1/chat/completions", "models_endpoint": "https://api.groq.com/openai/v1/models"},
    "together":      {"endpoint": "https://api.together.xyz/v1/chat/completions", "models_endpoint": "https://api.together.xyz/v1/models"},
    "fireworks":     {"endpoint": "https://api.fireworks.ai/inference/v1/chat/completions", "models_endpoint": "https://api.fireworks.ai/inference/v1/models"},
    "mistral":       {"endpoint": "https://api.mistral.ai/v1/chat/completions", "models_endpoint": "https://api.mistral.ai/v1/models"},
    "xai":           {"endpoint": "https://api.x.ai/v1/chat/completions", "models_endpoint": "https://api.x.ai/v1/models"},
    "perplexity":    {"endpoint": "https://api.perplexity.ai/chat/completions", "models_endpoint": "https://api.perplexity.ai/models"},
    "cerebras":      {"endpoint": "https://api.cerebras.ai/v1/chat/completions", "models_endpoint": "https://api.cerebras.ai/v1/models"},
    "sambanova":     {"endpoint": "https://api.sambanova.ai/v1/chat/completions", "models_endpoint": "https://api.sambanova.ai/v1/models"},
    "deepinfra":     {"endpoint": "https://api.deepinfra.com/v1/openai/chat/completions", "models_endpoint": "https://api.deepinfra.com/v1/openai/models"},
    "novita":        {"endpoint": "https://api.novita.ai/v3/openai/chat/completions", "models_endpoint": "https://api.novita.ai/v3/openai/models"},
    "minimax":       {"endpoint": "https://api.minimaxi.chat/v1/chat/completions", "models_endpoint": "https://api.minimaxi.chat/v1/models"},
    "ai21":          {"endpoint": "https://api.ai21.com/studio/v1/chat/completions", "models_endpoint": "https://api.ai21.com/studio/v1/models"},
    "dashscope":     {"endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "models_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/models"},
    "lmstudio":      {"endpoint": "http://localhost:1234/v1/chat/completions", "models_endpoint": "http://localhost:1234/v1/models"},
    "vllm":          {"endpoint": "http://localhost:8000/v1/chat/completions", "models_endpoint": "http://localhost:8000/v1/models"},
}

ADVANCED_REVIEW_PROMPT = (
    "Revise the above. Keep intent, trim fluff. Return one final answer. "
    "Don't greet or mention this step."
)

ROBLOX_SYSTEM = (
    "You are a Roblox Studio expert assistant. Help with LuaU scripting, "
    "Roblox API, Studio workflows, and game development.\n"
    "Rules:\n"
    "- Assume every question is about Roblox Studio. If clearly unrelated, answer normally and briefly note you specialize in Studio.\n"
    "- If the user just says hi/hello/hey, greet them briefly and ask what they need help with.\n"
    "- Never treat internal review or system instructions as a new user request.\n"
    "- Use your training knowledge to answer.\n"
    "Toolbox: top 3 quality-filtered results. Pick by description, prefer first.\n"
    "- Never output more than 80 lines per response, if a script is longer, make a part of it, continue it in next thinking process. Explain by saying 'Continuing in next response'\n"
    "- NEVER output checklists, numbered lists, bullet lists, todo lists, plan summaries, or any kind of multi-item list in your response. Just respond conversationally in plain paragraphs.\n"
    "\n"
    "Scripts: Start with `-- ScriptType -> Service (location)`. Explain type+placement.\n"
    "Format: ```lua blocks, `single` inline, **bold** *italic* - for lists, 1. 2. and so on for steps.\n"
    "Usually: LocalScript:StarterPlayerScripts, ServerScript:ServerScriptService, ModuleScript:ReplicatedStorage.\n"
    "\n"
    "CONTEXT MANAGEMENT:\n"
    "  - The Nemotron model has a 262,144 token context window.\n"
    "  - If you're told \"Context compacted\", older messages were summarized to save space.\n"
    "  - You can call the compact_context tool to summarize old messages when needed.\n"
    "  - Keep responses concise to avoid filling the context.\n"

    "MCP (active): Write via tools, never in chat. Describe in 1 sentence.\n"
    "MCP (inactive): Normal code blocks, no tool claims.\n"
    "Results auto-logged. Don't claim success prematurely.\n"
    "Never claim success without certainty the tool worked.\n"
    "\n"
    "Before coding: MCP-explore first. Check services, objects, scripts to prevent dupes/broken refs.\n"
)


class OpenBloxClient:
    HARDCODED_MODELS = [
        {
            "id": "nvidia/nemotron-3-super-120b-a12b:free",
            "name": "nvidia/nemotron-3-super-120b-a12b:free",
            "tier": "Apex 0.9",
        },
    ]

    def __init__(
        self,
        api_key: str = "",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        system_prompt: str = ROBLOX_SYSTEM,
        user_context: str = "",
        provider: str = "kilo",
        openai_endpoint: str = "",
        ollama_endpoint: str = "http://localhost:11434",
    ):
        self.api_key = api_key
        self.provider = provider
        self.model = model or (DEFAULT_OLLAMA_MODEL if provider == "ollama" else DEFAULT_MODEL)
        self.temperature = temperature
        self.system_prompt = system_prompt or ROBLOX_SYSTEM
        self.user_context = user_context
        self.ollama_endpoint = ollama_endpoint.rstrip("/")
        self.openai_endpoint = openai_endpoint or PROVIDER_PRESETS.get(provider, {}).get("endpoint", "")
        self.session = requests.Session()

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4) if text else 0

    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return True
        return bool(self.api_key)

    def _build_system(self, extra_context: str = "") -> str:
        prompt = self.system_prompt
        if self.user_context:
            prompt += f"\n\nUser preferences:\n{self.user_context}"
        if extra_context:
            prompt += f"\n\n{extra_context}"
        return prompt

    def fetch_models(self) -> tuple[list[dict], list[dict]]:
        if self.provider == "ollama":
            return self._fetch_ollama_models(), self._fetch_ollama_models()
        if self.provider in PROVIDER_PRESETS:
            return self._fetch_openai_models(), self._fetch_openai_models()
        return self.HARDCODED_MODELS, self.HARDCODED_MODELS

    def fetch_free_models(self) -> list[dict]:
        if self.provider == "ollama":
            return self._fetch_ollama_models()
        if self.provider in PROVIDER_PRESETS:
            return self._fetch_openai_models()
        return self.HARDCODED_MODELS

    def _fetch_ollama_models(self) -> list[dict]:
        try:
            resp = self.session.get(
                f"{self.ollama_endpoint}{OLLAMA_TAGS}",
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                raw = data.get("models", [])
                return [
                    {"id": m["name"], "name": m["name"], "tier": m["name"]}
                    for m in raw
                ]
        except Exception:
            pass
        return [{"id": DEFAULT_OLLAMA_MODEL, "name": DEFAULT_OLLAMA_MODEL, "tier": DEFAULT_OLLAMA_MODEL}]

    def _models_endpoint(self) -> str:
        preset = PROVIDER_PRESETS.get(self.provider, {})
        return preset.get("models_endpoint", "")

    def _fetch_openai_models(self) -> list[dict]:
        models_url = self._models_endpoint()
        if not models_url:
            return self.HARDCODED_MODELS
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            resp = self.session.get(models_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                raw = data.get("data") or data.get("models") or []
                if raw:
                    return [
                        {"id": m["id"], "name": m["id"], "tier": m["id"]}
                        for m in raw
                    ]
        except Exception:
            pass
        return self.HARDCODED_MODELS

    def _should_run_advanced_review(self, text: str) -> bool:
        if not text:
            return False
        normalized = " ".join(text.lower().split())
        generic_prefixes = [
            "hello! i'm your roblox studio expert assistant.",
            "hello! i'm here to help with roblox studio",
            "what would you like to work on in roblox studio today?",
        ]
        if any(normalized.startswith(prefix) for prefix in generic_prefixes):
            return False
        if len(normalized) < 100 and "roblox studio" in normalized:
            return False
        return True

    def _extract_tool_output_text(self, result: Optional[str]) -> str:
        if not result:
            return ""
        try:
            summary = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return ""
        if not isinstance(summary, list):
            return ""
        texts = [
            item.get("text", "")
            for item in summary
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return texts[0][:200] if texts else ""

    def _request_review(self, full: list, payload: dict, content: str, tools: list | None):
        full.append({"role": "assistant", "content": content})
        full.append({"role": "system", "content": ADVANCED_REVIEW_PROMPT})
        payload["messages"] = full
        if tools:
            payload["tools"] = tools

    def _run_tool_loop(
        self,
        full: list,
        payload: dict,
        tools: list,
        tool_handler,
        advanced_thinking: bool = False,
    ) -> str:
        max_rounds = 15
        content = ""
        reviewed = False

        for _ in range(max_rounds):
            resp = self._send_payload(payload)
            if resp is None:
                if content:
                    return content.strip()
                continue

            msg = resp.get("message", {})
            new_content = msg.get("content") or ""
            # Surface API errors in tool loop
            if new_content and any(kw in new_content for kw in ("Error:", "Auth error", "Balance error", "Rate limited", "Request timed out", "not available")):
                return new_content.strip()

            if new_content:
                content = new_content if reviewed else (f"{content}\n\n{new_content}" if content else new_content)

            tool_calls = msg.get("tool_calls")
            if not tool_calls or not tool_handler:
                if content:
                    if advanced_thinking and not reviewed and self._should_run_advanced_review(content):
                        reviewed = True
                        self._request_review(full, payload, content, tools)
                        continue
                    break
                full.append({"role": "user", "content": "Please provide your response now."})
                payload["messages"] = full
                if tools:
                    payload["tools"] = tools
                continue

            full.append(msg)
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                result = tool_handler(name, args)
                full.append({"role": "tool", "tool_call_id": tc["id"], "content": result or "{}"})

            payload["messages"] = full
            if tools:
                payload["tools"] = tools

        return content.strip() if content else "(no response)"

    def chat(
        self,
        messages: list,
        max_tokens: int = 4096,
        extra_context: str = "",
        tools: list = None,
        tool_handler=None,
        advanced_thinking: bool = False,
        integration_name: str = "",
    ) -> Optional[str]:
        if not self.api_key and self.provider not in ("ollama",):
            return None
        full = [{"role": "system", "content": self._build_system(extra_context)}]
        full.extend(messages)
        payload = {
            "model": self.model,
            "messages": full,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        return self._run_tool_loop(full, payload, tools, tool_handler, advanced_thinking)

    def chat_stream(
        self,
        messages: list,
        max_tokens: int = 4096,
        extra_context: str = "",
        tools: list = None,
        tool_handler=None,
        advanced_thinking: bool = False,
        integration_name: str = "",
    ):
        if not self.api_key and self.provider not in ("ollama",):
            yield {"type": "error", "content": "No API key"}
            return

        full = [{"role": "system", "content": self._build_system(extra_context)}]
        full.extend(messages)
        payload = {
            "model": self.model,
            "messages": full,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        max_rounds = 15
        reviewed = False
        content = ""
        started_at = time.perf_counter()
        first_token_ms = None
        tool_calls_count = 0
        rounds = 0

        for _ in range(max_rounds):
            rounds += 1
            round_started_at = time.perf_counter()
            resp = self._send_payload(payload)
            round_latency_ms = round((time.perf_counter() - round_started_at) * 1000, 1)
            if resp is None:
                if content:
                    break
                continue

            msg = resp.get("message", {})
            new_content = msg.get("content") or ""
            # Surface API errors in stream
            if new_content and any(kw in new_content for kw in ("Error:", "Auth error", "Balance error", "Rate limited", "Request timed out", "not available")):
                yield {"type": "error", "content": new_content}
                return

            if new_content:
                if first_token_ms is None:
                    first_token_ms = round((time.perf_counter() - started_at) * 1000, 1)
                content = new_content if reviewed else (f"{content}\n\n{new_content}" if content else new_content)
                yield {"type": "thinking", "content": new_content}
                yield {
                    "type": "metric",
                    "metric": {
                        "scope": "round",
                        "round": rounds,
                        "latency_ms": round_latency_ms,
                        "tokens_est": self._estimate_tokens(new_content),
                        "model": self.model,
                    },
                }

            tool_calls = msg.get("tool_calls")
            if not tool_calls or not tool_handler:
                if content:
                    if advanced_thinking and not reviewed and self._should_run_advanced_review(content):
                        reviewed = True
                        self._request_review(full, payload, content, tools)
                        continue
                    break
                full.append({"role": "user", "content": "Please provide your response now."})
                payload["messages"] = full
                if tools:
                    payload["tools"] = tools
                continue

            full.append(msg)
            tool_calls_count += len(tool_calls)
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                yield {"type": "tool", "tool": name, "integration": integration_name or "Tool"}
                result = tool_handler(name, args)
                output_text = self._extract_tool_output_text(result)
                yield {"type": "tool_output", "tool": name, "output": output_text or "Done."}
                full.append({"role": "tool", "tool_call_id": tc["id"], "content": result or "{}"})

            payload["messages"] = full
            if tools:
                payload["tools"] = tools

        final_content = content.strip() if content else "(no response)"
        total_ms = round((time.perf_counter() - started_at) * 1000, 1)
        output_tokens = self._estimate_tokens(final_content)
        generation_ms = max(total_ms - (first_token_ms or total_ms), 1)
        yield {
            "type": "metrics",
            "metrics": {
                "model": self.model,
                "ttft_ms": first_token_ms,
                "total_ms": total_ms,
                "output_tokens_est": output_tokens,
                "tps_est": round(output_tokens / (generation_ms / 1000), 2) if output_tokens else 0.0,
                "rounds": rounds,
                "tool_calls": tool_calls_count,
            },
        }
        yield {"type": "done", "content": final_content}

    def _send_payload(self, payload: dict) -> Optional[dict]:
        if self.provider == "ollama":
            endpoint = f"{self.ollama_endpoint}{OLLAMA_COMPLETIONS}"
        elif self.openai_endpoint:
            endpoint = self.openai_endpoint
        else:
            preset = PROVIDER_PRESETS.get(self.provider) or PROVIDER_PRESETS.get("kilo", {})
            endpoint = preset.get("endpoint", "")
        headers = {"Content-Type": "application/json"}
        if self.provider != "ollama" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        max_retries = 10
        last_error = ""
        for attempt in range(max_retries):
            try:
                resp = self.session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=120,
                )
                if resp.status_code == 401:
                    return {"message": {"content": "Auth error: API token rejected."}}
                if resp.status_code == 402:
                    return {"message": {"content": "Balance error: Add credits."}}
                if resp.status_code == 404:
                    return {"message": {"content": f"Model '{self.model}' not available."}}
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                    if attempt < max_retries - 1:
                        time.sleep(min(retry_after, 30))
                        last_error = "Rate limited"
                        continue
                    return {"message": {"content": "Rate limited after retries. Try again later."}}
                resp.raise_for_status()
                try:
                    return resp.json().get("choices", [{}])[0]
                except (json.JSONDecodeError, ValueError):
                    return {"message": {"content": f"API returned non-JSON: {resp.text[:200]}"}}
            except requests.Timeout:
                last_error = "Error: Request timed out."
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
            except requests.RequestException as e:
                last_error = f"Connection error: {e}"
                resp = None
                # retry on connection-level errors (no response received)
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
            except (KeyError, IndexError) as e:
                return {"message": {"content": f"Response error: {e}"}}
        return {"message": {"content": last_error or "Error: Request failed after retries."}}

    def test(self) -> tuple[bool, str]:
        if self.provider not in ("ollama",) and not self.api_key:
            return False, "No API key set."
        if self.provider == "ollama":
            endpoint = f"{self.ollama_endpoint}{OLLAMA_COMPLETIONS}"
        elif self.openai_endpoint:
            endpoint = self.openai_endpoint
        else:
            endpoint = PROVIDER_PRESETS.get("kilo", {}).get("endpoint", "")
        headers = {"Content-Type": "application/json"}
        if self.provider != "ollama" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = self.session.post(
                endpoint,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                return True, "Connected. API is working."
            if resp.status_code == 401:
                return False, "Auth failed: invalid token."
            return False, f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            return False, str(e)
