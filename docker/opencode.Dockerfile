# req3 opencode server image (design §13; plan M2/M9).
# Build from the repo root:
#   docker build -f docker/opencode.Dockerfile -t req3-opencode .
# opencode.json is generated at build time from roles.yaml + prompts/, so
# the image never contains a hand-edited config.
# Runtime env: LITELLM_BASE_URL, LITELLM_API_KEY, OPENCODE_SERVER_PASSWORD
# (HTTP Basic; username defaults to "opencode" — see executor/opencode.py).
FROM python:3.13-slim AS config
RUN pip install --no-cache-dir pyyaml==6.0.3
WORKDIR /src
COPY roles.yaml scripts/gen_opencode_config.py ./
COPY prompts/ ./prompts/
RUN python3 gen_opencode_config.py --roles roles.yaml --prompts prompts \
    --design-model glm-5.3-flash --review-model glm-5.3 \
    --out /out/opencode.json

FROM node:22-slim
# Pinned 1.19.0 (plan §1). npm's postinstall hook can fail silently — run it
# explicitly afterwards (gotcha list).
RUN npm install -g opencode-ai@1.19.0 \
 && cd "$(npm root -g)/opencode-ai" && node postinstall.mjs \
 && opencode --version
WORKDIR /app
COPY --from=config /out/opencode.json /app/opencode.json
# Project skills (verified location M4; agents currently use none).
COPY opencode/skills/ /app/.opencode/skill/
EXPOSE 4096
# Internal network only — never published (design §11).
CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
