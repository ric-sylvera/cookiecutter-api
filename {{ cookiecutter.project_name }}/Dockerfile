FROM python:3.11-slim AS base

# Required to run get SSL certs and perform health checks when locally run in docker-compose
RUN apt-get update -q && apt-get install -yq curl gosu

ARG AWS_REGION=eu-west-1
RUN curl -sS "https://truststore.pki.rds.amazonaws.com/${AWS_REGION}/${AWS_REGION}-bundle.pem" > /rds-cert-bundle.pem

WORKDIR /app

#
# ---- Install libraries ----
FROM base AS build

COPY pyproject.toml poetry.lock ./entrypoint.py ./logconfig.yml /app/
COPY ./app /app/app
COPY ./static static

RUN poetry install


#
# ---- Lacework Agent ----
FROM lacework/datacollector:latest-sidecar AS lacework-agent-build-image

#
# ---- Release ----
FROM base AS release

RUN useradd -ms /bin/bash sylvera

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

ENV TZ="UTC"

# expose port and define CMD
ENV PORT=8080
EXPOSE $PORT

#
# ---- Local dev image ----
FROM release as local

ENTRYPOINT [ "sh", "-c", "gosu sylvera /app/entrypoint.py \"$@\"", "sh"]

#
# ---- AWS release image ----
FROM release as aws

COPY --from=lacework-agent-build-image /var/lib/lacework-backup /var/lib/lacework-backup

ENTRYPOINT [ "sh", "-c", "/var/lib/lacework-backup/lacework-sidecar.sh && gosu sylvera /app/entrypoint.py \"$@\"", "sh"]
