# AGENTS.md — Spring Boot backend

Spring Boot 3.3.2 / Java 17 chat backend on port 8080. Maven layout; the
actual Java package lives at `src/main/java/com/example/chatgpt/`. Inherit
project-wide gotchas from the root `AGENTS.md` — read both before editing.

## Structure

    src/
    ├── main/
    │   ├── java/com/example/chatgpt/
    │   │   ├── ChatgptApplication.java   # @SpringBootApplication entry
    │   │   ├── config/                    # MinioConfig, MinioProperties, OllamaConfig, OllamaProperties, WebConfig (CORS)
    │   │   ├── controller/                # ChatController (/api/chat/**), SessionController (/api/sessions/**)
    │   │   ├── dto/                       # CreateSessionRequest, SendMessageResponse (request/response shapes)
    │   │   ├── model/                     # ChatSession, ChatMessage, MessageRole (Jackson @JsonValue/@JsonCreator)
    │   │   ├── ollama/                    # OllamaClient + request/response/StreamResponse DTOs
    │   │   ├── repository/                # ChatSessionRepository, ChatMessageRepository (Spring Data Mongo)
    │   │   └── service/                   # ChatService, ChatSessionService, MinioService
    │   └── resources/application.yml      # Hard-coded config; override via SPRING_DATA_MONGODB_URI / MINIO_* / OLLAMA_*
    └── pom.xml (lives at repo root; describes this Maven module)

## Where to look

| Task | Location |
|---|---|---|
| Add a REST endpoint | new method on `controller/ChatController` or `SessionController`; inject `@RequiredArgsConstructor` service |
| Add a Mongo collection | new `@Document` model in `model/` + Spring Data `MongoRepository` in `repository/` |
| Tune Ollama streaming | `ollama/OllamaClient.java` — uses OkHttp `Call` + `SseEmitter` |
| Adjust CORS / beans | `config/WebConfig.java`, `config/MinioConfig.java`, `config/OllamaConfig.java` |
| Override config | edit `application.yml` or pass `--SPRING_DATA_MONGODB_URI=...` etc. |

## Conventions (Spring Boot-specific)

- **Lombok everywhere.** `@Data` on models, `@Builder` for mutable DTOs,
  `@RequiredArgsConstructor` on controllers/services (constructor-injected
  because the project does not field-inject). Annotation processor wired via
  `pom.xml` `annotationProcessorPaths` — keep new classes consistent.
- **@ConfigurationProperties pattern.** Externalised config (MinIO, Ollama)
  uses `MinioProperties` / `OllamaProperties` annotated `@ConfigurationProperties`,
  registered via `@EnableConfigurationProperties` on the corresponding
  `*Config` class. Don't inline these values into `application.yml`-only
  constants — wire them through the properties class.
- **Mongo repositories are Spring Data.** No manual Mongo client; rely on
  `MongoRepository` for CRUD and `@Query` for custom queries.
- **SSE via `SseEmitter`.** `ChatController.streamMessage` returns a
  `SseEmitter`; `OllamaClient` reads OkHttp's streaming response line-by-line
  and calls `emitter.send(...)` per chunk. Errors close the emitter, not
  throw to the client.
- **Validation is bean-validation.** `@NotBlank` / `@Validated` on
  controllers; DTOs use Lombok `@Builder`. Don't add ad-hoc null checks when
  the annotation covers it.

## Anti-patterns (Spring Boot-specific)

- **No `/api/tasks` endpoint.** FastAPI has background tasks + SSE progress;
  Spring Boot does NOT. Don't assume parity — see
  frontend/ai/architecture/backend.md for the actual surface the UI expects.
- Do not field-inject (`@Autowired` on fields); use constructor injection via
  `@RequiredArgsConstructor`.
- Do not run `mvn test` expecting coverage. `src/test/` does not exist;
  Maven runs zero tests. See root AGENTS.md "Testing: FastAPI only" gotcha.

## Commands

    # From repo root (pom.xml is at the project root, not under src/)
    ./mvnw spring-boot:run                # Start on port 8080
    ./mvnw compile                        # Compile only
    ./mvnw -DskipTests package            # Build jar
    # Debug via VS Code launch.json "Spring Boot: ChatgptApplication"

## Notes

- `OllamaStreamResponse.java` differs from `OllamaChatResponse.java`
  because streaming returns chunked `message.content` deltas. Preserve the split.
- Spring has no MCP server — that's FastAPI-only (`fastapi_backend/mcp_server/`).
- Cross-system parity for `POST /api/chat/{sessionId}/stream` uses Spring's
  `SseEmitter` event names `delta` and `done`, matching the FastAPI
  `format_sse("delta", ...)` / `format_sse("done", ...)` contract — see
  `frontend/app/page.tsx` `flushEvent()` for the client-side parser.
