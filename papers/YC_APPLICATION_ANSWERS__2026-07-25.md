# YC Application Answers — fact-checked draft, 2026-07-25

Drafted by Gemini from live AI_EXPERIMENTS progress, revised after two rounds of fact-checking
against this repo's actual state (see `AI_EXPERIMENTS/FINDING__external-ai-confabulation-gemini-yc-pitch.md`
for the caught error and why it happened). This version has no known overclaiming — verified
against `AI_EXPERIMENTS/README.md`, `AI_EXPERIMENTS/EXP-009`, and project state as of this date.

Deadline: 2026-07-27. Not yet submitted. English translation added below (see
"English — copy-paste ready for the YC form") — ready to paste into the actual form.

## 1. What is your tech stack and what are you building?

Мы строим распределенную когнитивную систему SIPA OS для пользователей с СДВГ и ПРЛ. Вместо
использования длинных контекстных системных промптов к коммерческим API, мы исследуем
последовательный локальный файнтунинг SLM-моделей под специфические поведенческие паттерны.

Наш текущий пайплайн экспериментов развернут на доступных облачных мощностях (включая Google
Colab T4 для тренировочных прогонов). Прямо сейчас мы обучаем EXP-012 на расширенном датасете
из 1500 кастомных примеров сценариев, последовательно увеличивая выборку с исходных 503 примеров.

Юридически стартап полностью оформлен: зарегистрировано Delaware LLC, получен EIN и
зафиксирована внутренняя IP Policy в публичном репозитории проекта.

## 2. What is unique about what you're building?

Мы создаем интерфейсы ИИ-поддержки, ориентированные на компенсацию дефицита исполнительных
функций изнутри опыта человека с нейроотличностями. Мы сравниваем базовые веса моделей с
нашими fine-tuned весами, обученными на проприетарных поведенческих трейсах.

Мы не заявляем о создании абсолютного технического рва (Moat), так как еще не проводили
прямого бенчмаркинга наших локальных моделей против сложных оптимизированных промптов на
коммерческих закрытых моделях верхнего уровня (например, GPT-4o). Наша уникальность — в
методологии сбора данных и воспроизводимом пайплайне: за плечами 16 завершённых прогонов
(12 из них с полным разбором результатов), где Mistral-7B стабильно показывает лучший
результат в серии (EXP-004, EXP-010, EXP-012, и независимо воспроизведён на отдельной
GPU-платформе после потери первого прогона по квоте) — паттерн, который мы продолжаем
проверять в контролируемых условиях, а не выдаём за окончательно доказанный.

## 3. What do you understand about your users/domain that others don't?

Мы понимаем, что вариативность сэмплирования (даже при низких значениях температуры, например,
temperature=0.3 и параметре do_sample=True) вносит сильный шум в стабильность генерации
микродействий для пользователя. В ходе EXP-009 мы зафиксировали, что случайные флуктуации
сэмплирования способны путать результаты между прогонами.

Мы не встречали публичных данных о том, что существующие на рынке ИИ-ассистенты учитывают
этот фактор удержания состояния (state) применительно к когнитивным сбоям при СДВГ или ПРЛ.
Мы ищем баланс между гибкостью модели и жестким удержанием контекста через обучение весов на
кастомных поведенческих трейсах.

## 4. How do you and your system work together?

Архитектура работает на 5 нодах (SERVER — домашний хаб, T15, X7, LAPTOP, X5 — все на
ZeroTier mesh), полностью спроектированных и построенных Aelin AquaSoul. Я — единственный
архитектор и decision-maker: задаю направление, одобряю каждое действие, финальное решение
всегда за мной. Это не риторика — это зафиксированное правило системы (Protocol 0, CORE LAW),
и оно проверяется каждый день на практике: AI-слой не действует без явной команды оператора,
у него нет собственной инициативы и права интерпретировать неоднозначные запросы самостоятельно.

При этом непосредственное исполнение — код, файлы, коммиты, генерация датасетов, деплой,
коммуникация — в основном делегировано AI-агентам, работающим поверх этой инфраструктуры.
На практике это означает: я формулирую задачу и утверждаю каждый шаг, AI берёт на себя объём
рутинного и технического исполнения, который иначе потребовал бы отдельной инженерной команды.
Это позволяет одному человеку вести полноценную многослойную систему — но человек, а не AI,
остаётся единственным субъектом решений (это же закреплено юридически: `OWNERSHIP.md` и
`GOVERNANCE.md` в публичном репозитории проекта называют Aelin AquaSoul Founder/CEO/Chief
Architect и primary decision-maker — не AI).

## English — copy-paste ready for the YC form

Translated and updated to current state (2349-example dataset, EXP-012 closed, EXP-013/014
still running as of this writing — not claimed as finished).

### 1. What is your tech stack and what are you building?

We're building SIPA OS, a cognitive-support system for users with ADHD and BPD. Instead of
relying on long context-stuffed system prompts against commercial APIs, we're researching
iterative local fine-tuning of small language models toward specific behavioral compliance
patterns — a resource, not a decision-maker, that never fabricates and stops to ask under
ambiguity.

Our experiment pipeline runs on available cloud compute (Google Colab T4 for training runs,
Azure OpenAI for a parallel gpt-4o track). The training dataset has grown from an initial
503 examples to 2,349, through successive expansion rounds each tied to a specific canon
source (our internal governance rules, then our earliest historical protocol documents from
December 2025). 16 fine-tuning runs completed to date (12 with full written analysis,
4 more trained and awaiting write-up) across 6 base model families (DeepSeek, Qwen,
Mistral, Llama, gpt-4o, Phi — with GLM, Gemma, and Hermes attempts in progress as of this
writing) and 5 platforms (Lightning AI, Nebius, Azure OpenAI, Google Colab, Together AI)
— including broken and inconclusive ones, which we document as such rather than omit.

Legally, the company is fully formed: a Delaware LLC, EIN issued, and an internal IP Policy
recorded in the project's public governance repository.

### 2. What is unique about what you're building?

We're building AI-support interfaces aimed at compensating for executive-function deficits
from inside the lived experience of neurodivergence. We compare base model weights against
our fine-tuned weights, trained on proprietary behavioral traces.

We do not claim an absolute technical moat — we have not yet run a direct benchmark of our
local models against heavily-optimized prompts on top-tier closed commercial models (e.g.
GPT-4o). Our differentiation is in the methodology and the reproducible pipeline itself: 14
experiments run so far, with mixed but real findings — automatic benchmark scores are
frequently wrong in both directions (false positives on the base model, false negatives on
the fine-tuned model), and every experiment write-up includes a manual, response-by-response
correction of the raw score, not just the raw number. We treat this as a finding about the
methodology, not something to smooth over.

### 3. What do you understand about your users/domain that others don't?

We've found that sampling variance (even at low temperature — e.g. temperature=0.3 with
do_sample=True) introduces real noise into the stability of microaction generation for the
user. During one experiment (EXP-009) we documented random sampling fluctuations muddying
results between runs of the identical prompt.

We haven't found public data suggesting existing AI assistants on the market account for
this state-retention factor as it applies specifically to cognitive breakdowns under ADHD
or BPD. We're working to balance model flexibility against firm context retention by
training weights on custom behavioral traces rather than relying on prompt engineering
alone.

### 4. How do you and your system work together?

The architecture runs on 5 physical nodes (a home server hub plus four devices, mesh-networked
via ZeroTier), entirely designed and built by me, Aelin AquaSoul. I am the sole architect and
decision-maker: I set direction and approve every action; the final call is always mine. This
isn't rhetoric — it's an enforced system rule (internally: Protocol 0, CORE LAW), and it's
verified in practice daily: the AI layer never acts without an explicit operator command, has
no independent initiative, and no authority to interpret ambiguous requests on its own.

Direct execution — code, files, commits, dataset generation, deployment, communication — is
largely delegated to AI agents operating on top of this infrastructure. In practice: I define
the task and approve each step; the AI absorbs the volume of routine and technical execution
that would otherwise require a dedicated engineering team. This lets one person run a
full multi-layer system — but the human, not the AI, remains the sole subject of decisions
(this is also legally recorded: our public governance repository's OWNERSHIP.md and
GOVERNANCE.md name Aelin AquaSoul as Founder/CEO/Chief Architect and primary decision-maker
— not the AI).

## How to mention AMD/NVIDIA honestly (if the form has an Awards/Partnerships section)

Not as deployed infrastructure — as program participation, which is the actual fact:

- **AMD MI300X**: participation in the AMD AI Hackathon (lablab.ai, July 2026), testing agentic
  loops — not production infrastructure.
- **NVIDIA**: holds an approved NVIDIA AI Enterprise evaluation license, earmarked for future
  inference-optimization testing — not currently deployed or in use.

## Open follow-ups (not yet done)

- English translation for direct paste into the YC form
- Optional: experiment-progress timeline (EXP-004 → EXP-009/010 → EXP-012) as a separate section
