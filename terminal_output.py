import os
import sys

COLORS = {
    "cyan": "36",
    "green": "32",
    "magenta": "35",
    "yellow": "33",
    "bold": "1",
}


def colorize(text: str, color: str, enabled: bool) -> str:
    """Apply an ANSI color to text when color output is enabled.

    Args:
        text: Text to style.
        color: Name of a color in ``COLORS``.
        enabled: Whether to add ANSI color codes.

    Returns:
        The styled text, or the original text when styling is disabled.

    Raises:
        KeyError: If ``color`` is not present in ``COLORS``.
    """
    if not enabled:
        return text
    return f"\033[{COLORS[color]}m{text}\033[0m"


def print_response(
    provider: str,
    model: str,
    prompt: str,
    output_text: str,
    response_time: float,
    token_counts: tuple[int, int, int] | None,
) -> None:
    """Print a formatted prompt, response, and request metrics.

    Args:
        provider: Name of the provider that generated the response.
        model: Model used for the request.
        prompt: Input prompt sent to the model.
        output_text: Text returned by the model.
        response_time: Request duration in seconds.
        token_counts: Input, output, and total tokens, or ``None`` if unavailable.

    Returns:
        None.

    Raises:
        KeyError: If an internal color name is missing from ``COLORS``.
    """
    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    print(colorize(f"🤖 {provider} | {model}", "bold", use_color))
    print(colorize("\n📥 INPUT", "cyan", use_color))
    print(prompt)
    print(colorize("\n📤 OUTPUT", "green", use_color))
    print(output_text)
    print(colorize("\n📊 METRICS", "magenta", use_color))
    print(
        colorize(
            f"⏱️  Response time: {response_time:.2f} seconds",
            "yellow",
            use_color,
        )
    )

    if token_counts is None:
        token_text = "🔢 Token usage: unavailable from provider"
    else:
        input_tokens, output_tokens, total_tokens = token_counts
        token_text = (
            f"🔢 Tokens: input={input_tokens}, "
            f"output={output_tokens}, total={total_tokens}"
        )
    print(colorize(token_text, "yellow", use_color))
