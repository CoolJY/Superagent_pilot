# 모델 연결 설정

현재 기본 설정은 Gemini API의 `gemini-3.5-flash-lite`입니다. [Google 공식 호환 API 문서](https://ai.google.dev/gemini-api/docs/openai/)에 나온 OpenAI 호환 주소를 사용해 기존 채팅 구조를 유지합니다.

## 지금: Gemini 연결

저장소의 `OpenIntelligentUI` 폴더를 기준으로, 최초 실행 시 템플릿을 복사합니다.
기존 설정 파일이 있다면 복사하지 말고 해당 파일의 값을 수정하세요.

```sh
cp apps/agent/.env.example apps/agent/.env
cp apps/app/.env.example apps/app/.env.local
```

`apps/agent/.env`:

```dotenv
AIR_GAP_MODE=false
LLM_PROVIDER=gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=
```

`GEMINI_API_KEY=` 뒤에 사용 가능한 Gemini API 키를 넣습니다. 이 파일은 Git에서 제외됩니다.
키가 비어 있으면 에이전트가 명확한 설정 오류로 시작을 중단합니다. 키를 브라우저 설정,
소스 코드, 채팅 메시지에 넣지 마세요. Gemini 웹 로그인 대신 API 키로 연결합니다.

설정 변경 후 **에이전트를 재시작**하면 적용됩니다. 프로세스 환경변수가 `.env`보다 우선합니다.
Jev 키는 필요하지 않으며, 모델은 서버가 선택하고 브라우저의 공급자 키 재정의는 거부합니다.

웹 앱은 `apps/app/.env.local`에 다음을 둡니다. 여기에는 API 키를 넣지 않습니다.

```dotenv
NEXT_PUBLIC_AIR_GAP_MODE=true
NEXT_PUBLIC_SERVER_MANAGED_MODEL=true
NEXT_PUBLIC_MODEL_LABEL=Gemini
LANGGRAPH_DEPLOYMENT_URL=http://127.0.0.1:8123
NEXT_TELEMETRY_DISABLED=1
DO_NOT_TRACK=1
COPILOTKIT_TELEMETRY_DISABLED=true
```

웹 앱의 `NEXT_PUBLIC_AIR_GAP_MODE=true`는 브라우저의 외부 자원 접근을 제한합니다.
백엔드의 `AIR_GAP_MODE=false`와 독립적이므로 브라우저는 로컬 웹 서버에만 연결하고,
에이전트가 Gemini에 질문과 도구 컨텍스트를 전송합니다. 이 단계는 실제 폐쇄망 운영이 아닙니다.
`NEXT_PUBLIC_*` 값은 웹 앱 빌드 시 반영되므로 변경 시 재빌드해야 합니다.

실행 방법과 의존성 준비는 [배포 가이드](internal-deployment.md#3-실행)를 참고하세요.

## 나중: vLLM으로 전환

같은 `apps/agent/.env`에서 다음 값만 바꾸고 에이전트를 재시작합니다.

```dotenv
AIR_GAP_MODE=true
LLM_PROVIDER=vllm
LLM_BASE_URL=http://your-vllm-server:8000/v1
LLM_MODEL=your-served-model-name
LLM_API_KEY=
```

인증 없는 vLLM 서버만 키를 비워둘 수 있습니다. 기존 OpenAI 키는 제거하거나 내부 API 키로
교체해야 합니다. 주소는 `/v1`까지 포함하며 `/chat/completions`는 코드에서 붙입니다.
화면의 모델 표시도 바꾸려면 `NEXT_PUBLIC_MODEL_LABEL`을 변경한 뒤 웹 앱을 재빌드합니다.

Gemini는 `GEMINI_API_KEY`만 사용하며 다른 공급자의 `LLM_API_KEY`를 상속하지 않습니다.

기존 설정과의 호환을 위해 `LLM_BASE_URL`이 **정의되지 않은 경우에만** `OPENAI_BASE_URL`을,
`LLM_API_KEY`가 **정의되지 않은 경우에만** OpenAI는 `OPENAI_API_KEY`, vLLM은 `VLLM_API_KEY`를
참조합니다. 새 설정을 빈 값으로 지정하면 오래된 설정으로 우회하지 않습니다.

분석 수집, Jev API, 외부 이미지 도구는 서버에서 모델을 설정하는 모드에서 비활성화합니다.
기존 `LLM_PROVIDER=auto`는 이전 BYOK 데모 호환용이며 이번 파일럿에서는 사용하지 않습니다.


## 로컬 Ollama 연결

OpenAI 호환 `/v1` 주소를 사용합니다. 로컬 Ollama는 인증 키 없이 연결할 수 있습니다.
현재 PC에서 확인한 설정은 다음과 같습니다. 다른 PC에서는 설치된 모델 이름으로 바꾸세요.

```dotenv
AIR_GAP_MODE=true
LLM_PROVIDER=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen3.8:27b
LLM_API_KEY=
```

Ollama 요청 대기 시간은 기본 600초이며 `LLM_TIMEOUT_SECONDS`로 조절할 수 있습니다.
처음에는 도구와 스킬 안내를 읽는 과정 때문에 응답 시작이 오래 걸릴 수 있습니다.

웹 앱의 `NEXT_PUBLIC_MODEL_LABEL`은 `Ollama · qwen3.8:27b`로 설정할 수 있습니다.
도구 호출을 지원하는 모델이 필요합니다. Ollama 연결도 동일한 서버 설정 파일에서 관리합니다.
API 형식은 [Ollama 공식 문서](https://docs.ollama.com/api/openai-compatibility)를 따릅니다.


## OpenAI로 다시 전환

`LLM_PROVIDER=openai`, `LLM_BASE_URL=https://api.openai.com/v1`, `LLM_MODEL=chat-latest`,
`LLM_API_KEY=<OpenAI key>`를 설정합니다. 웹 앱 표시도 `NEXT_PUBLIC_MODEL_LABEL=ChatGPT`로 바꿉니다.
Gemini API 키는 OpenAI 요청에 사용되지 않습니다.
