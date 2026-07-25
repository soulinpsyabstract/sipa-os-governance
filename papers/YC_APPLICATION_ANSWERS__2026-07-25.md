# YC Application Answers — fact-checked draft, 2026-07-25

Drafted by Gemini from live AI_EXPERIMENTS progress, revised after two rounds of fact-checking
against this repo's actual state (see `AI_EXPERIMENTS/FINDING__external-ai-confabulation-gemini-yc-pitch.md`
for the caught error and why it happened). This version has no known overclaiming — verified
against `AI_EXPERIMENTS/README.md`, `AI_EXPERIMENTS/EXP-009`, and project state as of this date.

Deadline: 2026-07-27. Not yet submitted — not yet translated to English.

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
методологии сбора данных и воспроизводимом пайплайне: за плечами 11 проведенных экспериментов,
где EXP-010 на текущий момент показал лучший результат в серии (с допущением, что на метрики
повлияла одновременная смена тренировочного движка, что мы и верифицируем в текущем EXP-012).

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

## How to mention AMD/NVIDIA honestly (if the form has an Awards/Partnerships section)

Not as deployed infrastructure — as program participation, which is the actual fact:

- **AMD MI300X**: participation in the AMD AI Hackathon (lablab.ai, July 2026), testing agentic
  loops — not production infrastructure.
- **NVIDIA**: holds an approved NVIDIA AI Enterprise evaluation license, earmarked for future
  inference-optimization testing — not currently deployed or in use.

## Open follow-ups (not yet done)

- English translation for direct paste into the YC form
- Optional: experiment-progress timeline (EXP-004 → EXP-009/010 → EXP-012) as a separate section
