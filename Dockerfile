FROM python:3.9 AS builder

RUN pip install --user pipenv

ENV PIPENV_VENV_IN_PROJECT=1
COPY Pipfile.lock /app/Pipfile.lock

WORKDIR /app
RUN /root/.local/bin/pipenv sync

FROM python:3.9 AS runtime

WORKDIR /app

COPY --from=builder /app/.venv/ /app/.venv/
ENV PATH=".venv/bin:$PATH"

COPY . /app

CMD [ "python", "bot.py" ] 