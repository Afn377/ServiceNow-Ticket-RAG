import pytest

import deepseek_client


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content):
        self._content = content
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content):
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content):
        self.chat = _FakeChat(content)


def test_call_deepseek_returns_message_content(monkeypatch):
    fake_client = _FakeClient("hello from deepseek")
    monkeypatch.setattr(deepseek_client, "_client", lambda api_key=None: fake_client)

    result = deepseek_client.call_deepseek("say hello")

    assert result == "hello from deepseek"
    assert fake_client.chat.completions.last_kwargs["model"] == deepseek_client.DEEPSEEK_MODEL
    assert fake_client.chat.completions.last_kwargs["messages"] == [
        {"role": "user", "content": "say hello"}
    ]


def test_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        deepseek_client._client(api_key=None)
