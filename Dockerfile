# Base stage: always builds the main app
FROM python:3.12-slim AS base

WORKDIR /app

COPY ./src /app
COPY ./requirements.txt /app/requirements.txt
COPY ./configuration.template.json /app/configuration.template.json

RUN pip install --upgrade pip && \
    pip install -r ./requirements.txt

RUN apt-get update && apt-get install -y gettext-base


# Set arguments for environment variables (one per line)
ARG CODEBASE_DESCRIPTION="Default description"
ARG CODE_COMMAND_STRATEGY="update_file"
ARG PROMPTING_PROVIDER="OpenAI"
ARG PROMPTING_API_KEY="your-api-key"
ARG PROMPTING_MODEL="gpt-4.1"
ARG PROMPTING_TEMPERATURE="0.2"
ARG PROMPTING_MAX_TOKENS="3000"
ARG PROMPTING_TOP_P="1.0"
ARG PROMPTING_TIMEOUT="60"
ARG CODE_DIRECTORY="./codebase"
ARG CODE_STAGING_DIRECTORY="./codebase_staging"
ARG FASTAPI_PORT="3000"
ARG REPROMPT_ON_CHANGE="true"
ARG KEYPOINT_NOTIFICATION_ENABLED="false"
ARG KEYPOINT_NOTIFICATION_ENDPOINT="http://game-web-wrapper:8001/notify-of-event"
ARG CODE_IGNORE_PATTERNS="\"**/node_modules/\", \"**/dist/\", \".vscode/\", \".git/\""
ARG CODE_INCLUDE_ONLY_PATTERNS="\"*.ts\", \"*.png\""


# Set default environment variables
ENV CODEBASE_DESCRIPTION=${CODEBASE_DESCRIPTION} \
    CODE_COMMAND_STRATEGY=${CODE_COMMAND_STRATEGY} \
    PROMPTING_PROVIDER=${PROMPTING_PROVIDER} \
    PROMPTING_API_KEY=${PROMPTING_API_KEY} \
    PROMPTING_MODEL=${PROMPTING_MODEL} \
    PROMPTING_TEMPERATURE=${PROMPTING_TEMPERATURE} \
    PROMPTING_MAX_TOKENS=${PROMPTING_MAX_TOKENS} \
    PROMPTING_TOP_P=${PROMPTING_TOP_P} \
    PROMPTING_TIMEOUT=${PROMPTING_TIMEOUT} \
    CODE_DIRECTORY=${CODE_DIRECTORY} \
    CODE_STAGING_DIRECTORY=${CODE_STAGING_DIRECTORY} \
    FASTAPI_PORT=${FASTAPI_PORT} \
    REPROMPT_ON_CHANGE=${REPROMPT_ON_CHANGE} \
    KEYPOINT_NOTIFICATION_ENABLED=${KEYPOINT_NOTIFICATION_ENABLED} \
    KEYPOINT_NOTIFICATION_ENDPOINT=${KEYPOINT_NOTIFICATION_ENDPOINT} \
    CODE_IGNORE_PATTERNS=${CODE_IGNORE_PATTERNS} \
    CODE_INCLUDE_ONLY_PATTERNS=${CODE_INCLUDE_ONLY_PATTERNS}

RUN envsubst < /app/configuration.template.json > /app/configuration.json
RUN rm /app/configuration.template.json

EXPOSE ${FASTAPI_PORT}

CMD ["python", "/app/main.py", "--config", "/app/configuration.json"]

# with_codebase stage: includes codebase directory
FROM base AS with_codebase

COPY ./codebase /app/codebase