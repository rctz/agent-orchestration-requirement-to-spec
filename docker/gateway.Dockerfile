# req3 gateway image (design §13; plan M4/M9).
# Build from the repo root:
#   docker build -f docker/gateway.Dockerfile -t req3-gateway .
# Runtime env: REQ3_API_KEY, REQ3_WEBHOOK_SECRET, LITELLM_BASE_URL,
# LITELLM_API_KEY, OPENCODE_SERVER_PASSWORD (via compose env_file).
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY req3/ ./req3/
RUN pip install --no-cache-dir .
COPY roles.yaml ./
COPY prompts/ ./prompts/
COPY schemas/ ./schemas/
COPY checklists/ ./checklists/
COPY profiles/ ./profiles/
COPY docker/gateway.config.yaml /app/config.yaml
ENV REQ3_CONFIG=/app/config.yaml
EXPOSE 7790
CMD ["python", "-m", "req3.main"]
