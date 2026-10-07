# Swarms SEO Office Runtime

A [Claw3D](https://github.com/iamlukethedev/Claw3D) **custom runtime adapter** backed by
[Swarms AI](https://github.com/kyegomez/swarms). It implements the direct HTTP runtime seam
Claw3D probes for, and turns a Swarms multi-agent team into workers in the Claw3D 3D office.

The agents are a **full SEO team**:

| Agent (office worker) | Focus |
| --- | --- |
| SEO Director | Strategy, coordination, executive summaries |
| SEO Research Analyst | Keyword research, SERP + competitor analysis |
| Content Writer | Briefs, outlines, on-page copy, meta tags |
| Technical SEO Engineer | Audits, crawlability, schema, site speed, code |
| Marketing Strategist | Distribution, campaigns, positioning |
| Link Builder | Backlinks, digital PR, outreach |

## Endpoints (Claw3D runtime seam)

- `GET /health` — liveness probe
- `GET /state` — runtime identity + the `active` agent roster (each key becomes an office agent)
- `GET /registry` — available models
- `POST /v1/chat/completions` — OpenAI-compatible chat that routes to the matching Swarms agent

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required for agents to run (Swarms uses LiteLLM under the hood) |
| `SWARMS_MODEL` | `gpt-4o-mini` | Default model for all agents |
| `SWARMS_MODELS` | `gpt-4o-mini,gpt-4o,gpt-4.1-mini,gpt-4.1` | Models exposed in `/registry` |
| `SWARMS_MAX_LOOPS` | `1` | Swarms `max_loops` per agent run |
| `SWARMS_MAX_CONCURRENT_RUNS` | `2` | Concurrent agent executions |
| `PORT` | `7770` | HTTP port (Railway injects this automatically) |

## Run locally

```bash
docker build -t swarms-seo-office-runtime .
docker run -p 7770:7770 -e OPENAI_API_KEY=sk-... swarms-seo-office-runtime
```

Then point Claw3D Studio at `http://localhost:7770` with the `Custom` backend.

## Deploy on Railway

1. Create a new service from this repo (Railway builds the Dockerfile).
2. Add `OPENAI_API_KEY` in Variables.
3. Generate a public domain — Claw3D Studio needs its hostname in
   `CUSTOM_RUNTIME_ALLOWLIST` to proxy chat requests.
