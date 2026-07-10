"""Unit tests for multi-provider LLM routing (no network)."""

from src.llm.providers import infer_provider


def test_infer_ecnu():
    assert infer_provider("ecnu-plus") == "ecnu"
    assert infer_provider("ecnu-max") == "ecnu"


def test_infer_n1n():
    assert infer_provider("gpt-4o") == "n1n"
    assert infer_provider("claude-sonnet-4-6") == "n1n"
    assert infer_provider("deepseek-v3.2") == "n1n"
    assert infer_provider("qwen3-max") == "n1n"
    assert infer_provider("gemini-2.5-flash") == "n1n"
