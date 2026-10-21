"""Exercise the local provider wire format and the air-gap HTTP boundary."""
import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.credentials import CredentialsMiddleware
from src.model import build_model


@pytest.fixture
def internal_env(monkeypatch):
    monkeypatch.setenv('AIR_GAP_MODE', 'true')
    monkeypatch.setenv('LLM_PROVIDER', 'vllm')
    monkeypatch.setenv('LLM_MODEL', 'internal/qwen')
    monkeypatch.setenv('OPENAI_BASE_URL', 'http://vllm.internal:8000/v1')
    monkeypatch.delenv('VLLM_API_KEY', raising=False)
    monkeypatch.delenv('TYPESAFE_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'cloud-key-must-not-be-used')


def test_internal_model_streams_tool_calls_without_cloud_credentials(internal_env, monkeypatch):
    def send(client, request, **kwargs):
        assert str(request.url) == 'http://vllm.internal:8000/v1/chat/completions'
        assert request.headers['authorization'] == 'Bearer EMPTY'
        payload = json.loads(request.content)
        assert payload['model'] == 'internal/qwen'
        assert payload['stream'] is True
        assert payload['tools'][0]['function']['name'] == 'lookup'
        chunks = [
            {'role': 'assistant', 'content': '', 'tool_calls': [{'index': 0, 'id': 'call_1', 'type': 'function', 'function': {'name': 'lookup', 'arguments': '{"topic":'}}]},
            {'tool_calls': [{'index': 0, 'function': {'arguments': '"local"}'}}]},
        ]
        data = ''.join('data: ' + json.dumps({'id': 'test', 'object': 'chat.completion.chunk', 'created': 1, 'model': 'internal/qwen', 'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]}) + '\n\n' for delta in chunks)
        return httpx.Response(200, content=(data + 'data: [DONE]\n\n').encode(), headers={'content-type': 'text/event-stream'}, request=request)
    monkeypatch.setattr(httpx.Client, 'send', send)
    model = build_model().bind_tools([{'type': 'function', 'function': {'name': 'lookup', 'description': 'Lookup internal data', 'parameters': {'type': 'object', 'properties': {'topic': {'type': 'string'}}, 'required': ['topic']}}}])
    chunks = list(model.stream('Find local data'))
    combined = chunks[0]
    for chunk in chunks[1:]:
        combined += chunk
    assert combined.tool_calls[0]['args'] == {'topic': 'local'}


def test_internal_async_request_uses_configured_key(internal_env, monkeypatch):
    monkeypatch.setenv('VLLM_API_KEY', 'internal-test-key')
    async def send(client, request, **kwargs):
        assert str(request.url).startswith('http://vllm.internal:8000/v1/')
        assert request.headers['authorization'] == 'Bearer internal-test-key'
        return httpx.Response(200, json={'id': 'local', 'object': 'chat.completion', 'created': 1, 'model': 'internal/qwen', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '안녕하세요'}, 'finish_reason': 'stop'}]}, request=request)
    monkeypatch.setattr(httpx.AsyncClient, 'send', send)
    assert asyncio.run(build_model().ainvoke('Hello')).content == '안녕하세요'


@pytest.mark.parametrize('url', ['', 'https://example.test', 'ftp://local/v1', 'http://user:pass@local/v1', 'http://local/v1?key=abc'])
def test_internal_url_must_be_explicit(internal_env, monkeypatch, url):
    monkeypatch.setenv('OPENAI_BASE_URL', url)
    with pytest.raises(ValueError, match='LLM_BASE_URL'):
        build_model(allow_unconfigured=True)


def test_internal_mode_cannot_fall_back_to_cloud(internal_env, monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'auto')
    with pytest.raises(ValueError, match='LLM_PROVIDER=vllm'):
        build_model()


def test_internal_chat_needs_no_browser_keys_and_rejects_cloud_override(internal_env):
    app = FastAPI()
    app.add_middleware(CredentialsMiddleware)
    @app.post('/')
    def chat():
        return {'ok': True}
    client = TestClient(app)
    assert client.post('/').status_code == 200
    assert client.post('/', headers={'x-openai-api-key': 'browser', 'x-jev-api-key': 'browser'}).status_code == 403
    assert client.post('/credentials/validate').status_code == 403
