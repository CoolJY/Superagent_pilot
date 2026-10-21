# Superagent Pilot 내부망 배포

현재 개발 기본값은 ChatGPT입니다. 먼저 [모델 설정 가이드](model-configuration.md)를 참고하세요. 아래는 향후 vLLM 전환용 설정입니다.

## 이번 구현 범위

`requirements.txt`의 첫 단계로, 기존 채팅과 스트리밍 생성 UI를 내부 vLLM에 연결합니다.
`AIR_GAP_MODE=true`에서는 Jev 라우팅과 외부 여행 이미지 도구를 등록하지 않으며,
내부 모델이 표·차트·일반 텍스트 중 표현 방식을 선택합니다. 기존 로컬 도구,
읽기 전용 스킬 백엔드와 프런트엔드의 MCP 연결 설정은 유지됩니다.

이 모드는 **배포 설정**입니다. 방화벽을 대신하지 않으며 내부 API 주소의
네트워크 접근 제어는 운영 환경에서 적용해야 합니다.

## 1. 에이전트 설정

`apps/agent/.env`에 다음을 설정합니다. 실제 주소와 모델 이름으로 교체하세요.
`LLM_BASE_URL`은 `/v1`까지 포함하며 `/chat/completions`는 붙이지 않습니다.

```dotenv
AIR_GAP_MODE=true
LLM_PROVIDER=vllm
LLM_BASE_URL=http://vllm.internal:8000/v1
LLM_MODEL=your-served-model-name
LLM_API_KEY=
LANGSMITH_TRACING=false
LANGCHAIN_TRACING_V2=false
DO_NOT_TRACK=1
COPILOTKIT_TELEMETRY_DISABLED=true
```

인증을 사용하는 내부 서버만 `LLM_API_KEY`를 설정합니다. 키는 브라우저에 전달하지
않으며, OpenAI용 환경변수의 키나 프록시를 상속하지 않습니다. 인증 없는 서버에는
SDK 형식 요건을 충족하는 `EMPTY` 값이 사용됩니다. 모델 이름의 접두사 제한은 없습니다.
주소·모델 설정이 없으면 시작 단계에서 오류를 내며 공개 클라우드로 우회하지 않습니다.

vLLM은 스트리밍 Chat Completions와 도구 호출을 지원하도록 설정해야 합니다.
자동 도구 호출의 `--enable-auto-tool-choice` 및 모델에 맞는 `--tool-call-parser`,
필요한 채팅 템플릿은 설치된 버전의 [vLLM 공식 문서](https://docs.vllm.ai/en/stable/features/tool_calling/)
를 확인하세요. 모델별 파서는 여기서 임의로 지정하지 않습니다.

## 2. 웹 앱 설정

`apps/app/.env.local`:

```dotenv
NEXT_PUBLIC_AIR_GAP_MODE=true
NEXT_PUBLIC_SERVER_MANAGED_MODEL=true
NEXT_PUBLIC_MODEL_LABEL=Internal AI
LANGGRAPH_DEPLOYMENT_URL=http://127.0.0.1:8123
NEXT_TELEMETRY_DISABLED=1
DO_NOT_TRACK=1
COPILOTKIT_TELEMETRY_DISABLED=true
```

`NEXT_PUBLIC_AIR_GAP_MODE`는 **빌드 시점**에 적용됩니다. 프로필 변경 시 재빌드하세요.
에이전트와 웹 앱은 함께 내부망 모드로 설정해야 합니다. 이 모드에서는 API 키 대화상자가
필요하지 않으며, 브라우저 키 전달·검증 API도 거부합니다. 키 입력 제거는 사용자 인증을
제공하는 기능이 아닙니다. 다중 사용자 공개 전에는 사내 인증 연동이 필요합니다.

## 3. 실행

인터넷 사용이 가능한 준비 환경에서 저장소의 잠금 파일로 의존성을 준비합니다.
Node.js 22 이상, pnpm 9.0.0, Python 3.12 이상, uv를 사용합니다.

```sh
cd OpenIntelligentUI
npx --yes pnpm@9.0.0 install --frozen-lockfile
uv sync --frozen --directory apps/agent
```

개발 중에는 터미널 두 개에서 실행합니다.

```sh
# OpenIntelligentUI 기준
uv run --frozen --directory apps/agent uvicorn main:app --host 127.0.0.1 --port 8123
npx --yes pnpm@9.0.0 --filter @repo/app dev
```

빌드 시에도 내부망 설정과 분석 수집 비활성화를 명시합니다.

```sh
NEXT_PUBLIC_AIR_GAP_MODE=true DO_NOT_TRACK=1 COPILOTKIT_TELEMETRY_DISABLED=true NEXT_TELEMETRY_DISABLED=1 npx --yes pnpm@9.0.0 build
npx --yes pnpm@9.0.0 --filter @repo/app start
```

폐쇄망에서는 `npx` 다운로드나 패키지 레지스트리를 사용할 수 없습니다. 운영 OS/아키텍처에
맞는 Node/Python 런타임과 의존성·빌드 산출물을 사전에 반입해야 합니다.
컨테이너 이미지·오프라인 패키지 반입 자동화는 후속 작업입니다.

## 동작 및 제약

- 외부 Jev API·위키미디어 도구, LangSmith 추적, 앱 분석 수집은 내부망 모드에서 끕니다.
- 웹 폰트는 저장소에 포함된 로컬 폰트를 사용합니다.
- 생성 UI의 미리보기·완성 프레임은 외부 네트워크 접근을 차단하고 CDN importmap을 제거합니다.
  HTML/CSS/일반 JavaScript와 SVG/canvas로 시각화를 구성합니다. 외부 지도 타일,
  Three.js 등 CDN 예제는 내부망에서 사용할 수 없습니다.
- 브라우저 전체의 CSP도 같은 출처의 자원·연결만 허용합니다.
- 외부 차트 라이브러리를 참조하는 기존 독립 HTML 내보내기는 아직 오프라인용으로
  변환하지 않았습니다. 일반 채팅/인라인 생성 UI와 별개인 후속 점검 항목입니다.
- 기존 대화 메모리는 프로세스 메모리에 있으며 재시작 시 사라집니다.
  사용자 인증, 영구 대화 저장, 내부 업무 데이터·도구 연결은 후속 단계입니다.
- 실제 서버의 모델 품질, 컨텍스트 한도, 한국어 스트리밍, 도구 호출과 생성 UI는
  실제 vLLM 주소·모델을 받은 뒤 검증해야 합니다. 모의 API 검증은 실제 추론 검증을 대체하지 않습니다.

## 검증

```sh
uv run --frozen --directory apps/agent pytest
npx --yes pnpm@9.0.0 test
npx --yes pnpm@9.0.0 lint
```

새 테스트는 내부 주소·임의 모델 이름·인증 키 선택, 비동기 응답,
스트리밍 도구 인자 조립, 공개 클라우드 폴백 차단, 키 없는 채팅,
외부 분석 수집 차단 및 프레임 CSP를 확인합니다.

운영 반입 전에는 인터넷 경로가 차단된 환경에서 첫 질문·후속 질문·도구 호출·
생성 UI 조작·좁은 화면을 확인하고 브라우저/서버 네트워크 기록을 점검하세요.
