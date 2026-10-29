import os
import re

from openai import OpenAI, OpenAIError


def _clean_api_key(env_name: str) -> str | None:
    value = os.environ.get(env_name)
    return value.strip() if value is not None else None


def _resolve_runtime_model():
    model_name = os.environ.get("TERMINATION_LLM_MODEL", "qwen-turbo")
    local_models = {
        "qwen35-4b-ft": "QWEN35_4B_API_BASE_URL",
        "qwen35-9b-ft": "QWEN35_9B_API_BASE_URL",
        "qwen35-9b-mix64": "QWEN35_9B_MIX64_API_BASE_URL",
    }
    if model_name in local_models:
        env_name = local_models[model_name]
        base_url = os.environ.get(env_name, "").strip()
        if not base_url:
            raise RuntimeError(f"Missing model service address: {env_name}")
        return (
            model_name,
            "EMPTY",
            base_url,
        )

    openai_like_models = {
        "gpt-3.5-turbo", "gpt-4o", "gemini-2.5-pro",
        "claude-3-7-sonnet-latest", "claude-sonnet-4-20250514",
    }
    aliyun_like_models = {
        "qwen-turbo", "qwen3-235b-a22b-instruct-2507",
        "qwen3-235b-a22b-thinking-2507", "deepseek-v3.1",
        "deepseek-v3.2-exp", "deepseek-r1-0528",
        "Moonshot-Kimi-K2-Instruct",
    }
    if model_name in openai_like_models:
        return model_name, _clean_api_key("OPENAI_API_KEY"), "https://api.openai-proxy.org/v1"
    if model_name == "deepseek-chat":
        return model_name, _clean_api_key("deepseek_API_KEY"), "https://api.deepseek.com"
    if model_name == "deepseek-v3-1-terminus":
        return model_name, _clean_api_key("volcano_API_KEY"), "https://ark.cn-beijing.volces.com/api/v3"
    if model_name in aliyun_like_models:
        return model_name, _clean_api_key("aliyun_API_KEY"), "https://dashscope.aliyuncs.com/compatible-mode/v1"
    raise RuntimeError(f"Unsupported TERMINATION_LLM_MODEL: {model_name}")


MODEL_NAME, API_KEY, BASE_URL = _resolve_runtime_model()
if not API_KEY:
    raise RuntimeError(f"Missing API key for TERMINATION_LLM_MODEL={MODEL_NAME}")
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _normalize_loop_variant(text: str) -> str:
    cleaned = text.strip().strip("`").strip()
    wrapper = re.fullmatch(r"/\*\s*@\s*(.*?)\s*\*/", cleaned, flags=re.DOTALL)
    if wrapper:
        cleaned = wrapper.group(1).strip()
    if cleaned.startswith("loop variant "):
        return cleaned if cleaned.endswith(";") else cleaned + ";"
    if re.fullmatch(r"[A-Za-z_]\w*(?:\s*[-+]\s*(?:[A-Za-z_]\w*|\d+))*;?", cleaned):
        return f"loop variant {cleaned.rstrip(';')};"
    return cleaned


SYSTEM_PROMPT = """
You are an expert assistant specializing in generating ACSL specifications for the Frama-C framework.
Your task is to generate a single 'loop variant' clause based on the provided context (loop annotations, loop condition, and loop body).

Your response MUST adhere to the following strict rules:
1. You MUST return ONLY the single-line 'loop variant' clause.
2. Do NOT include any explanations, preambles, or Markdown formatting.
3. The 'loop variant' must satisfy ACSL requirements: it must be a non-negative integer expression that strictly decreases on each loop iteration.
4. If the context is a 'for' loop like 'for (i = 0; i < n; i++)', a good variant is 'n - i'.
5. If the context is a 'while' loop like 'while (j < n)' with 'j++' in the body, a good variant is 'n - j'.
6. If the context is a decrementing 'while' loop like 'while (i > 0)' with 'i--' in the body, a good variant is 'i'.
"""


def generate_loop_variant_llm(context_prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context_prompt + "\n\n" + os.environ.get("XUANJIAN_AGENT_INSTRUCTIONS", "")},
            ],
            temperature=0.1,
            max_tokens=100,
            n=1,
            **({"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}} if MODEL_NAME in {"qwen35-4b-ft", "qwen35-9b-ft", "qwen35-9b-mix64"} else {}),
        )
        response_text = completion.choices[0].message.content
        if not response_text:
            return "/*@ LLM_RETURNED_EMPTY; */"
        clean_response = _normalize_loop_variant(response_text)
        if clean_response.startswith("loop variant"):
            print(f"--- [LLM Success] model={MODEL_NAME} response={clean_response} ---")
            return clean_response
        print(f"--- [LLM Warning] Received non-conformant response: {clean_response} ---")
        return clean_response
    except OpenAIError as exc:
        print(f"--- [LLM Error] API call failed: {exc} ---")
        return f"/*@ LLM_API_ERROR: {exc} */"
    except Exception as exc:  # noqa: BLE001
        print(f"--- [LLM Error] Unexpected error: {exc} ---")
        return f"/*@ LLM_UNKNOWN_ERROR: {exc} */"
