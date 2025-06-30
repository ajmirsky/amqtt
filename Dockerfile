
# -- build stage, install dependencies only using `uv`
FROM python:3.13-alpine AS build

RUN pip install uv

WORKDIR /app

COPY . /app
RUN apk add gcc python3-dev musl-dev linux-headers
RUN uv pip install --target=/deps .
RUN uv pip install --target=/deps newrelic


# -- final image, copy dependencies and amqtt source
FROM python:3.13-alpine

WORKDIR /app

COPY --from=build /deps /usr/local/lib/python3.13/site-packages/

COPY ./amqtt/scripts/default_broker.yaml /app/conf/broker.yaml
COPY ./amqtt/scripts/broker_monitor.py /app/broker_monitor.py

EXPOSE 1883

ENV PATH="/usr/local/lib/python3.13/site-packages/bin:$PATH"


CMD ["python", "/app/broker_monitor.py"]
