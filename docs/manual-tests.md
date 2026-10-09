# Manual tests

Copy-paste curl checks, one section per story.

## Story story-1-1-architecture-project-seed.md — Architecture and project seed

**What it adds:** a local API with `/health`, `/v1/models` and one OpenAI-compatible `/v1/chat/completions` route that sends the latest user message through a LangChain prompt to a Groq model, normal or streaming.

**Prerequisites:** start the API from the project root with `uv run python -m learning_companion`. The model checks need `GROQ_API_KEY` and `GROQ_MODEL_NAME` set in your untracked `.env`. Commands use Bash quoting (Git Bash, macOS, Linux). In `/v1/chat/completions` below, replace `YOUR_MODEL` with the `id` from `/v1/models`; the app always uses `GROQ_MODEL_NAME` and only echoes the request's `model` back.

```
curl http://127.0.0.1:8000/health
```

Expect `200` and `{"status":"ok"}`.

```
curl http://127.0.0.1:8000/v1/models
```

Expect `200` and `{"object":"list","data":[...]}` with one entry whose `id` is your `GROQ_MODEL_NAME` and `owned_by` is `groq`. If `GROQ_MODEL_NAME` is blank, `data` is an empty list.

```
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "YOUR_MODEL", "stream": false, "messages": [{"role": "user", "content": "What is a variable in Python?"}]}'
```

Expect `200` and one JSON object with `object` `chat.completion`, `choices[0].message.role` `assistant`, a short plain-language answer in `choices[0].message.content`, and `finish_reason` `stop`. If `GROQ_API_KEY` or `GROQ_MODEL_NAME` is blank you instead get `503` with `error.type` `configuration_error` naming the missing setting.

```
curl -N http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "YOUR_MODEL", "stream": true, "messages": [{"role": "user", "content": "What is a variable in Python?"}]}'
```

Expect `200` with `Content-Type: text/event-stream`: `data: {...}` lines with `object` `chat.completion.chunk` (the first delta has `role` `assistant`, later ones carry `content` text), then a chunk with `finish_reason` `stop`, and the response ends with `data: [DONE]`.

```
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "YOUR_MODEL", "stream": false, "messages": [{"role": "system", "content": "Be brief."}]}'
```

Expect `400` with `error.type` `invalid_request_error` and the message `The request has no user message.` (with the key or model name blank this returns the `503` configuration error instead, because that check runs first).
