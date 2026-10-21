# Superagent Pilot

폐쇄망에서 내부 vLLM 모델을 사용하는 채팅·반응형 UI 파일럿입니다.
화면과 에이전트는 `OpenIntelligentUI/`를 기반으로 합니다.

- 요구사항: [requirements.txt](requirements.txt)
- 내부망 설정·실행: [내부 배포 가이드](OpenIntelligentUI/docs/internal-deployment.md)
- 원본 프로젝트: [OpenIntelligentUI](OpenIntelligentUI/README.md)

현재 기본 모델은 Gemini `gemini-3.5-flash-lite`이며 주소·모델·키는 [모델 설정 가이드](OpenIntelligentUI/docs/model-configuration.md)에 따라 변경합니다.

현재 구현: 내부 OpenAI 호환 Chat Completions 연결, 서버 측 인증 설정,
외부 키 입력 없는 채팅, 내부망 모드의 외부 시각화 API·분석 수집 비활성화,
로컬 폰트와 네트워크 접근이 제한된 생성 UI.

실제 vLLM 연결 및 운영용 폐쇄망 패키징은 배포 환경에서 검증해야 합니다.
