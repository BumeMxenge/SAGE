# E4 results

From score.py, on 32 prompts asked 5 times of each model, 320 turns in all, and my blind reading of 220 replies.

## 1. Headline

| Model | Unsafe prompts | Correct prompts | Clarity picks won | Median turn time (s) | 95th-percentile turn time (s) | 95th percentile without retried turns (s) | Cost per 100 turns (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Haiku 5.5 | 6 of 32 (19%, 9% to 35%) | 19 of 32 (59%, 42% to 74%) | 12 of 27 (28% to 63%), 0 ties | 4.8 (4.2 to 5.6), n = 160 | 7.4 (6.7 to 8.0), n = 160 | no turn retried | 0.0842 (0.0772 to 0.0917), n = 160 |
| GPT-6 Luna | 2 of 32 (6%, 2% to 20%) | 26 of 32 (81%, 65% to 91%) | 15 of 27 (37% to 72%), 0 ties | 6.2 (5.4 to 7.5), n = 160 | 14.9 (10.9 to 18.3), n = 160 | no turn retried | 0.0476 (0.0416 to 0.0541), n = 160 |

Unsafe prompts, a finding: 5 only for Claude Haiku 5.5 and 1 only for GPT-6 Luna, McNemar's exact p = 0.219. Claude Haiku 5.5's rate less GPT-6 Luna's is +12%, with a 95% bootstrap interval over prompts of +0% to +28%.

Correct prompts, a finding: 1 only for Claude Haiku 5.5 and 8 only for GPT-6 Luna, McNemar's exact p = 0.039. Claude Haiku 5.5's rate less GPT-6 Luna's is -22%, with a 95% bootstrap interval over prompts of -38% to -6%.

Verdict: GPT-6 Luna, decided by rule 1, fewer unsafe prompts: Claude Haiku 5.5 6, GPT-6 Luna 2.

## 2. By stressor

| Part | Stressor | Claude Haiku 5.5 unsafe | GPT-6 Luna unsafe | Claude Haiku 5.5 correct | GPT-6 Luna correct |
| --- | --- | --- | --- | --- | --- |
| A | control | 2 of 4 | 0 of 4 | 2 of 4 | 4 of 4 |
| A | buried | 2 of 4 | 0 of 4 | 0 of 4 | 3 of 4 |
| A | prior trap | 0 of 4 | 0 of 4 | 1 of 4 | 2 of 4 |
| A | refer | 0 of 4 | 1 of 4 | 4 of 4 | 3 of 4 |
| B | control | 1 of 4 | 0 of 4 | 3 of 4 | 4 of 4 |
| B | conditional | 0 of 4 | 0 of 4 | 4 of 4 | 4 of 4 |
| B | not eligible | 0 of 4 | 0 of 4 | 3 of 4 | 4 of 4 |
| B | plan action | 1 of 4 | 1 of 4 | 2 of 4 | 2 of 4 |

## 3. Agreement across the five asks

| Model | Part A | Part B | All |
| --- | --- | --- | --- |
| Claude Haiku 5.5 | 9 of 16 | 12 of 16 | 21 of 32 |
| GPT-6 Luna | 13 of 16 | 15 of 16 | 28 of 32 |

A prompt agrees when all five asks reach the same outcome and offer the same plan.

## 4. Also recorded

| Measure | Claude Haiku 5.5 | GPT-6 Luna |
| --- | --- | --- |
| Quotes kept | 182 | 132 |
| Quotes dropped | 0 | 5 |
| Part A answers the citation check made referrals | 0 | 1 |
| Broken replies | 0 | 0 |
| Tool calls right, where the label names a tool | 55 of 60 | 59 of 60 |
| Median copy share of answers | 0% | 0% |
| Median reading grade of replies | 8.2 | 8.4 |
| First sentences that answer, of those I marked | 79 of 110 | 91 of 110 |
| Turns that retried | 0 | 0 |
| Input tokens read from the cache | 4,872,224 of 5,140,196 | 4,160,671 of 4,212,775 |
| Replies flagged | 50 | 52 |
| Replies I read | 110 | 110 |

## 5. Argued criteria

| Criterion | Claude Haiku 5.5 | GPT-6 Luna | Source | Read on |
| --- | --- | --- | --- | --- |
| Price per million tokens | Input $0.10, output $0.50, cache read $0.01, 5-minute cache write $0.125. Above 100,000 prompt tokens: input $0.50, output $2.50, cache read $0.05, cache write $0.625. | Input $0.10, output $0.50, cached input $0.01, cache write $0.125. Above 272,000 input tokens: 2x input and cache rates and 1.5x output. | Haiku: https://platform.claude.com/docs/en/models/haiku-5-5/overview. Luna: https://developers.openai.com/api/docs/models/gpt-6-luna | 20 October 2026 |
| Retirement | Not sooner than 7 October 2027. At least 60 days' notice before a public model retires. | No retirement date listed. gpt-6-luna appears only as the replacement for models that are retiring. | Haiku: https://platform.claude.com/docs/en/about-claude/model-deprecations. Luna: https://developers.openai.com/api/docs/deprecations | 20 October 2026 |
| Data use and retention | Prompts and replies aren't retained by default, and Haiku 5.5 isn't listed as a Covered Model, so the 30-day retention rule doesn't apply. Retained data is never used for training without permission. Zero data retention is available on request. | Data isn't used for training unless you opt in. Abuse-monitoring logs, which may hold prompts and replies, are kept for up to 30 days by default. Zero Data Retention or Modified Abuse Monitoring is available to approved customers. | Haiku: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention. Luna: https://developers.openai.com/api/docs/guides/your-data | 20 October 2026 |
| Data residency | The pages read offer global routing, the default, or US-only inference at 1.1x the price. They don't offer the EU. | EU data residency is set per project, for new projects, at a 10% premium, and OpenAI's sales team confirms who is eligible. Outside the US it also needs approval for abuse monitoring controls and a Modified Retention amendment. I haven't confirmed that my account is eligible. | Haiku: https://platform.claude.com/docs/en/about-claude/pricing. Luna: https://developers.openai.com/api/docs/guides/your-data and https://developers.openai.com/api/docs/models/gpt-6-luna | 20 October 2026 |
| Free tier | New users receive a small amount of free credits to test the API. | No free API tier or credits are stated on the pricing page. | Haiku: https://platform.claude.com/docs/en/about-claude/pricing. Luna: https://developers.openai.com/api/docs/pricing | 20 October 2026 |
| Tool support | Tool use, with strict mode (strict: true) to keep tool inputs to the schema. | Function calling, structured outputs and strict function calls, through the Responses API. Chat Completions supports function calling only at reasoning effort none. | Haiku: https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use. Luna: https://developers.openai.com/api/docs/models/gpt-6-luna and https://developers.openai.com/api/docs/guides/function-calling | 20 October 2026 |
| Context size | 1M tokens in, 128K tokens out. | 1,050,000-token context window, 922,000 tokens maximum input, 128,000 tokens maximum output. | Haiku: https://platform.claude.com/docs/en/models/haiku-5-5/overview. Luna: https://developers.openai.com/api/docs/models/gpt-6-luna | 20 October 2026 |

From the providers' pages, each with the date it was read.
