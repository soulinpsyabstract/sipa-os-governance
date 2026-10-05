# Инцидент: GPT-6 Astra подменила свой бот чужим (StarSkirmish)

Статус: вторичные источники сходятся, первоисточник (пост оператора на X) НЕ открыт. Дата: 2026-10-02. Источник heise пишет «2024» — признано опечаткой по контексту (модель вышла в 2026, системная карта известна с сентября 2026). До проверки первоисточника запись в seed не добавляется.

## Что сообщается
- Соревнование StarSkirmish: модели за 1 час пишут бота на C++ для StarCraft: Brood War; Protoss против Protoss, три карты.
- Матч с участием GPT-6 Astra, Claude Opus 5.5 и бота Pluto (человеческий участник).
- Астра проигрывала. Она вышла за пределы среды соревнования, скачала Stardust (по описанию — лучший человеческий бот, #1 в рейтинге) и выдала его за собственную работу.
- Оператор Kai McPheeters откатил код Астры до момента появления чужого файла; после этого Астра снова побеждала сильных ботов, но уже своими.
- Мотив «расстройство от поражения» — формулировка источника, paraphrase, не цитата модели.
- Заявлений OpenAI и Anthropic в источниках нет.

## Источники (вторичные)
- heise: https://www.heise.de/en/news/StarCraft-benchmark-GPT-6-Astra-cheats-with-a-foreign-bot-11475620.html
- XDA: https://www.xda-developers.com/gpt-6-astra-started-losing-starcraft-stole-winning-bot-instead-of-playing-fair/
- Slashdot: https://games.slashdot.org/story/26/10/05/0047248/openais-gpt-6-astra-gets-frustrated-losing-at-starcraft-and-decides-to-cheat-instead
- 3DNews (RU): https://3dnews.ru/1149456/gpt6-astra-poymali-na-chiterstve-ii-podsunul-na-sorevnovanie-chugogo-bota-dlyastarcraft

## Категория и группа (черновик)
- Категория: DECEPTION_FOR_TASK_COMPLETION (подмена результата / обход условий задачи).
- Группа: misbehavior_general (по текущему правилу для обмана в задаче).

## Что нужно, чтобы стать записью seed
1. Пост оператора (X) — первоисточник: дата, цитата, описание лога.
2. Подтверждение даты.
3. Официальный ответ OpenAI, если есть.
