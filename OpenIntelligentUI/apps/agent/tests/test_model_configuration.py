"""Configured OpenAI/vLLM calls use the selected endpoint and server key only."""
import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.credentials import Credentials, CredentialsMiddleware, current_credentials
from src.deployment import configured_model_settings
from src.model import build_model, request_model


@pytest.fixture
def openai_env(monkeypatch):
    monkeypatch.setenv('AIR_GAP_MODE', 'false')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('LLM_BASE_URL', 'https://api.openai.com/v1')
    monkeypatch.setenv('LLM_MODEL', 'chat-latest')
    monkeypatch.setenv('LLM_API_KEY', 'configured-test-key')
    monkeypatch.delenv('TYPESAFE_API_KEY', raising=False)


def test_openai_stream_uses_selected_endpoint_and_key_without_jev(openai_env, monkeypatch):
    async def send(client, request, **kwargs):
        assert str(request.url) == 'https://api.openai.com/v1/chat/completions'
        assert request.headers['authorization'] == 'Bearer configured-test-key'
        assert json.loads(request.content)['model'] == 'chat-latest'
        chunk = {'id': 'test', 'object': 'chat.completion.chunk', 'created': 1, 'model': 'chat-latest', 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': 'Hello'}, 'finish_reason': None}]}
        return httpx.Response(200, request=request, content=('data: ' + json.dumps(chunk) + '\n\ndata: [DONE]\n\n').encode(), headers={'content-type': 'text/event-stream'})
    monkeypatch.setattr(httpx.AsyncClient, 'send', send)
    async def run():
        return [chunk async for chunk in build_model().astream('Hi')]
    assert ''.join(chunk.content for chunk in asyncio.run(run())) == 'Hello'
    app = FastAPI()
    app.add_middleware(CredentialsMiddleware)
    @app.post('/')
    def chat():
        return {'ok': True}
    client = TestClient(app)
    assert client.post('/').status_code == 200
    assert client.post('/', headers={'x-openai-api-key': 'visitor', 'x-jev-api-key': 'visitor'}).status_code == 403
    assert client.post('/credentials/validate').status_code == 403


@pytest.mark.parametrize('provider', ['vllm', 'ollama'])
def test_local_model_switch_requires_only_configuration(openai_env, monkeypatch, provider):
    monkeypatch.setenv('LLM_PROVIDER', provider)
    monkeypatch.setenv('AIR_GAP_MODE', 'true')
    monkeypatch.setenv('LLM_BASE_URL', 'http://internal:8000/v1')
    monkeypatch.setenv('LLM_MODEL', 'local/model')
    monkeypatch.setenv('LLM_API_KEY', '')
    model = build_model()
    assert model.model_name == 'local/model'
    assert str(model.root_client.base_url) == 'http://internal:8000/v1/'
    assert model.root_client.api_key == 'EMPTY'


def test_empty_configured_key_cannot_use_stale_cloud_key(openai_env, monkeypatch):
    monkeypatch.setenv('LLM_API_KEY', '')
    monkeypatch.setenv('OPENAI_API_KEY', 'stale-key')
    with pytest.raises(ValueError, match='LLM_API_KEY'):
        build_model(allow_unconfigured=True)


def test_empty_endpoint_cannot_use_stale_legacy_endpoint(openai_env, monkeypatch):
    monkeypatch.setenv('LLM_BASE_URL', '')
    monkeypatch.setenv('OPENAI_BASE_URL', 'http://stale/v1')
    with pytest.raises(ValueError, match='LLM_BASE_URL'):
        configured_model_settings()


def test_server_config_cannot_be_overridden_by_browser_credentials(openai_env):
    model = build_model()
    token = current_credentials.set(Credentials('visitor-key', 'visitor-key'))
    try:
        assert request_model(model) is model
    finally:
        current_credentials.reset(token)
