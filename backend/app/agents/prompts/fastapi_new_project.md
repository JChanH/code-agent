### FastAPI 신규 프로젝트 핵심 규칙 요약

**디렉토리 구조:**
main.py / core/{config,lifespan,user_dependencies}.py / models/db/ / repository/ / service/ / router/ / utils/ / cache/ / exceptions.py

**레이어 의존성 (역방향 절대 금지):**
router → service → repository → models/db

**필수 파일 체크리스트:**
- core/config.py: Settings 싱글톤 (os.getenv 직접 호출 금지)
- models/result.py: ApiResponse[T] 공통 응답 래퍼
- exceptions.py: BusinessException 기본 예외 계층
- utils/db_handler_sqlalchemy.py: DBManager + db_conn 싱글톤

**네이밍 컨벤션:**
- 파일: {domain}_router.py / {domain}_service.py / {domain}_repo.py
- 클래스: {Domain}Service / {Domain}Repository / {Action}{Domain}Request / {Domain}{Content}Response
- 서비스 메서드: process_{동작} (예: process_login, process_create_product)
- 레포지토리 메서드: find_by_{field} / find_all_by_{field} / create / update_by_{field}

**핵심 규칙:**
- 모든 API 응답은 ApiResponse.success(data) 래퍼 사용
- 트랜잭션은 async with db_conn.transaction() as session: 블록에서만
- commit은 repository에서 하지 않음 (service 역할)
- ORM 모델을 API 응답에 직접 반환 금지 → Pydantic 응답 모델로 변환
- 모든 커스텀 예외는 BusinessException 상속
- 모든 테이블에 created_at, updated_at 포함
