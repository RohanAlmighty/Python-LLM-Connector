import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import TypedDict

from openai import OpenAI, OpenAIError

from terminal_output import print_response


class ProviderConfig(TypedDict):
    """Describe the settings required to connect to an OpenAI-compatible provider."""

    api_key: str | None
    api_key_env: str | None
    base_url: str
    model: str


CONFIG_PATH = Path(__file__).with_name("providers.json")


def load_providers() -> dict[str, ProviderConfig]:
    """Load and validate provider definitions from the adjacent JSON config.

    Returns:
        Provider definitions indexed by lowercase provider name.

    Raises:
        ValueError: If the file cannot be read, parsed, or fails validation.
    """
    try:
        with CONFIG_PATH.open(encoding="utf-8") as config_file:
            raw_providers = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Unable to load provider config '{CONFIG_PATH}': {error}"
        ) from error

    if not isinstance(raw_providers, dict) or not raw_providers:
        raise ValueError("Provider config must contain a non-empty JSON object.")

    providers: dict[str, ProviderConfig] = {}
    for name, raw_config in raw_providers.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Provider names must be non-empty strings.")
        if not isinstance(raw_config, dict):
            raise TypeError(f"Configuration for provider '{name}' must be an object.")

        base_url = raw_config.get("base_url")
        model = raw_config.get("model")
        api_key = raw_config.get("api_key")
        api_key_env = raw_config.get("api_key_env")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError(f"Provider '{name}' must define a non-empty base_url.")
        if not isinstance(model, str) or not model.strip():
            raise ValueError(f"Provider '{name}' must define a non-empty model.")
        if api_key is not None and (
            not isinstance(api_key, str) or not api_key.strip()
        ):
            raise ValueError(
                f"Provider '{name}' api_key must be a non-empty string or null."
            )
        if api_key_env is not None and (
            not isinstance(api_key_env, str) or not api_key_env.strip()
        ):
            raise ValueError(
                f"Provider '{name}' api_key_env must be a non-empty string or null."
            )
        if (api_key is None) == (api_key_env is None):
            raise ValueError(
                f"Provider '{name}' must define exactly one of api_key or api_key_env."
            )

        normalized_name = name.casefold()
        if normalized_name in providers:
            raise ValueError(f"Duplicate provider name '{name}'.")
        providers[normalized_name] = {
            "api_key": api_key,
            "api_key_env": api_key_env,
            "base_url": base_url,
            "model": model,
        }

    return providers


def get_client(
    provider: str,
    providers: dict[str, ProviderConfig],
    model_override: str | None = None,
) -> tuple[OpenAI, str]:
    """Create an API client and select a model for the requested provider.

    Args:
        provider: Name of a provider in the loaded configuration.
        providers: Provider definitions returned by :func:`load_providers`.
        model_override: Optional model name to use instead of the provider default.

    Returns:
        A tuple containing the configured OpenAI client and model name.

    Raises:
        ValueError: If the provider is unsupported or its API key is missing.
        OpenAIError: If the client cannot be initialized.
    """
    provider = provider.casefold()
    config = providers.get(provider)
    if config is None:
        supported = ", ".join(providers)
        raise ValueError(
            f"Unsupported provider '{provider}'. Choose from: {supported}."
        )

    api_key = config["api_key"]
    if api_key is None:
        api_key_env = config["api_key_env"]
        if api_key_env is None:
            raise ValueError(f"No API key is configured for provider '{provider}'.")
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Set {api_key_env} to use the '{provider}' provider.")

    model = model_override if model_override is not None else config["model"]
    if not model.strip():
        raise ValueError("Model name cannot be empty.")
    client = OpenAI(api_key=api_key, base_url=config["base_url"])
    return client, model


def main() -> int:
    """Parse input, call the selected provider, and display its response.

    Returns:
        Exit status: 0 on success, 1 for provider errors, or 2 for configuration
        errors.

    Raises:
        SystemExit: If command-line arguments are invalid.
    """
    try:
        providers = load_providers()
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Send a prompt to an OpenAI-compatible cloud or local LLM."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt to send. If omitted, enter it interactively.",
    )
    parser.add_argument(
        "--provider",
        choices=providers,
        default=os.environ.get("LLM_PROVIDER", "ollama").casefold(),
        help="Provider to use (default: LLM_PROVIDER or ollama).",
    )
    parser.add_argument(
        "--model",
        help="Override the selected provider's default model.",
    )
    args = parser.parse_args()

    prompt = args.prompt if args.prompt is not None else input("Prompt: ")
    if not prompt.strip():
        parser.error("Prompt cannot be empty.")

    try:
        client, model = get_client(args.provider, providers, args.model)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    except OpenAIError as error:
        print(f"Client setup failed: {error}", file=sys.stderr)
        return 1

    start_time = perf_counter()
    try:
        response = client.responses.create(model=model, input=prompt)
    except OpenAIError as error:
        print(f"Request failed: {error}", file=sys.stderr)
        return 1
    response_time = perf_counter() - start_time

    usage = response.usage
    token_counts = None
    if usage is not None:
        token_counts = (
            usage.input_tokens,
            usage.output_tokens,
            usage.total_tokens,
        )

    print_response(
        provider=args.provider,
        model=model,
        prompt=prompt,
        output_text=response.output_text,
        response_time=response_time,
        token_counts=token_counts,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
