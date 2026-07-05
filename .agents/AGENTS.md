# Agent Behavioral Rules

## Workspace Context Validation
* **목적**: Active Document(활성 커서) 위치로 인해 작업 폴더를 오인하는 오류 방지
* **규칙**: 현재 폴더를 식별하거나 대상 프로젝트를 분석할 때, `Active Document`의 경로에 무조건 의존하지 않는다.
* **행동 지침**: 반드시 `<user_information>`의 활성 워크스페이스 URI(예: `/Users/l/project/DownTube`)와 대조 확인한다.
* **예외 처리**: 활성 문서가 워크스페이스를 벗어난 경우(예: `/Users/l/project/SSKI/`), 임의로 폴더를 넘나들지 말고 반드시 사용자에게 대상 폴더가 어디인지 재확인하거나 기본 워크스페이스 경로를 기준으로 작업한다.
