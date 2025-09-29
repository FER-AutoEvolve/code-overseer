# Base stage: always builds the main app
FROM python:3.12-slim AS base

WORKDIR /app

COPY ./src /app
COPY ./requirements.txt /app/requirements.txt
COPY ./configuration.template.json /app/configuration.template.json

RUN pip install --upgrade pip && \
    pip install -r ./requirements.txt

RUN apt-get update && apt-get install -y gettext-base

ENV CODEBASE_DESCRIPTION="Default description" \
    CODE_COMMAND_STRATEGY="update_file" \
    PROMPTING_PROVIDER="OpenAI" \
    PROMPTING_API_KEY="your-api-key" \
    PROMPTING_MODEL="gpt-4.1" \
    PROMPTING_TEMPERATURE="0.2" \
    PROMPTING_MAX_TOKENS="3000" \
    PROMPTING_TOP_P="1.0" \
    PROMPTING_TIMEOUT="60" \
    CODE_DIRECTORY="./codebase" \
    FASTAPI_PORT="3000"

RUN envsubst < /app/configuration.template.json > /app/configuration.json
RUN rm /app/configuration.template.json

EXPOSE ${FASTAPI_PORT}

CMD ["python", "/app/main.py", "--config", "/app/configuration.json"]

# with_codebase stage: includes codebase directory
FROM base AS with_codebase

COPY ./codebase /app/codebase