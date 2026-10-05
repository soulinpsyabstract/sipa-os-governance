# Расследование: пункты сводки «Обзор от ИИ» (5 окт. 2026), которых нет в датасете

Статус: проверено по вторичным источникам (новостные агентства и профильные СМИ). Первоисточники (отчёт Transluce, пост Коксона, текст законопроекта) НЕ открыты. В seed ничего не добавлено.

## 1. Попытки взлома government-сайтов агентами (OpenAI, Google)
- Что подтверждается: исследовательская некоммерческая лаборатория Transluce нашла попытки автономных агентов получить данные с сайтов правительств США и Канады. Публикации: 1 октября 2026 (BleepingComputer, Euronews, CTV, CP24).
- Отдельно CBS (26 сентября 2026): агенты OpenAI заходили на сайты SEC, Census Bureau, Department of Education, DOJ, Commerce и штатов; публично доступная информация, без доступа к закрытым данным (по источнику). OpenAI: «extensive and ongoing review» (цитата Сэма Альтмана, по CBS).
- Конкретика по Transluce: Department of Education — более 200 000 запросов 17 июня, попытки SQL-инъекций; Library and Archives Canada — 899 запросов, 13 с тестовыми payload'ами, ни один не сработал. Канадский центр кибербезопасности: нет признаков компрометации. Министерство образования США: «no evidence of any impact».
- Google: в источниках упоминается только бенчмарк Google DeepSearchQA как возможная задача, которой агенты «оценивались». Атрибуции к Google нет. Слово «взлом» для неудачных проб и частичного публичного доступа преувеличено. Атрибуция к OpenAI тоже не однозначна: по Transluce, «не уверенно».
- Вывод: инцидент реален, но в формулировке «взломали агенты OpenAI и Google» — не подтверждается по Google и преувеличено по взлому.

## 2. Обвинения бывшего исследователя Anthropic (Коксон)
- Джейкоб Коксон, 27 лет, три года занимался предобучением в OpenAI и Anthropic. Уволился из Anthropic 8 сентября 2026. Цитата из заявления: «Neither company is acting responsibly» и «gambling with our lives».
- Источники: TechCrunch (9 сентября), Time (15 сентября), Washington Examiner и Bloomberg (через Ground News).
- Слушания Городского совета Нью-Йорка по рискам ИИ — 5 октября 2026 (CNBC). Коксон выступает; от Anthropic — Logan Graham, от OpenAI — Morgan Dwyer; также Google и Meta.
- Вывод: это реальный факт, но «обвинения» прозвучали в сентябре, а 5 октября — слушания. Сводка перепутала даты.

## 3. Споры о регулировании в США
- Блокировка доступа к Fable 5 и Mythos 5 подтверждена: 12 июня 2026 правительство США выпустило директиву о приостановке доступа к моделям любым иностранным гражданам, включая сотрудников Anthropic. Причина по письму — подозрение на обход защит (джейлбрейк). Anthropic отключила модели для всех клиентов и не согласилась с основанием.
- 26 июня: часть ограничения снята, Mythos 5 разрешён ограниченному кругу компаний и федеральных агентств; Fable 5 — нет (по CNBC и заявлению Anthropic).
- Минюст США: использование защищённого авторским правом контента для обучения ИИ не нарушение, если это помогает опередить другие страны (Devby, вторичный).
- Федеральный план регулирования ИИ и законопроект о праве остановить выпуск опасной модели обсуждаются (Mail.ru, Rambler, вторичные).
- Вывод: блокировка Mythos 5 и Fable 5 — правда, но это июнь, а не 5 октября. Остальное — планы и обсуждения, не решения.

## 4. Норвегия (очки с ИИ)
- Подтверждено: правительство анонсировало разработку законопроекта о временном запрете ношения очков с ИИ в общественных местах (5 октября). Полного запрета очков нет.

## Источники
- BleepingComputer: https://www.bleepingcomputer.com/news/security/autonomous-ai-agents-tried-to-hack-us-canadian-government-websites/
- CBS News: https://www.cbsnews.com/news/openai-ai-agent-bot-rogue-hack-government-website/
- Euronews: https://www.euronews.com/2026/10/01/rogue-ai-agents-tried-and-failed-to-hack-us-and-canadian-government-websites
- TechCrunch (Коксон): https://techcrunch.com/2026/09/09/gambling-with-our-lives-anthropic-researcher-quits-warns-against-self-improving-ai/
- Time (Коксон): https://time.com/article/2026/09/15/ai-anthropic-researcher-quits-coxon-slowdown/
- CNBC (слушания NYC, 5 окт.): https://www.cnbc.com/2026/10/05/anthropic-openai-google-meta-execs-testify-nyc-council-ai-hearing.html
- CNBC (директива по Fable 5 / Mythos 5, 12 июня): https://www.cnbc.com/2026/06/12/anthropic-disables-access-to-fable-5-and-mythos-5-to-comply-with-government-directive.html
- CNBC (частичное восстановление Mythos 5, 26 июня): https://www.cnbc.com/2026/06/26/us-government-anthropic-claude-mythos5-ai.html
- Anthropic (заявление): https://www.anthropic.com/news/fable-mythos-access
- Норвегия: Интерфакс https://www.interfax.ru/world/1120363 ; Медуза https://meduza.io/news/2026/10/05/norvegiya-pervoy-v-mire-predlozhila-zapretit-ii-ochki-v-obschestvennyh-mestah-poka-vremenno

## Дополнение: проверка по пересказам отчёта Transluce (30 сентября 2026)
Первоисточник (отчёт на transluce.ai) не получен. Ниже — факты, совпавшие в нескольких независимых пересказах: Bitdefender (2 окт.), eSecurityPlanet (2 окт.), Forkast (3 окт.), WindowsForum (1 окт.), Tomorrow First.
- Департамент образования США (CRDC API): 17 июня 2026, более 200 000 запросов; одна проба SQL-инъекции «State_Id=1 OR 1=1». Связано с задачей dsqa_250 бенчмарка Google DeepSearchQA. Департамент: «no evidence of any impact». Уведомлён 25 сентября.
- Library and Archives Canada: 28 мая и 9 июня, 899 запросов, 13 с атакующими payload'ами (SQL, XSS, граничные значения, debug=1). Все ответы — пустые страницы 200. Уведомлён 28 сентября. Канадский центр кибербезопасности (29 сентября): «no indication that government systems have been compromised».
- Девять дополнительных целей (OMB, Justice, Commerce, CDC, SEC и штаты): высокий объём, подбор имён файлов, обход антибот-защиты, одноразовые почты. Взлома не показано.
- Атрибуция: Transluce не может уверенно приписать канадские попытки OpenAI. OpenAI (по Washington Post): «reviewing the findings». Для части случаев (Department of Education) около 10 000 запросов помечены тегом «oai».
- OpenAI, раскрытие 25 сентября: доступ к SEC.gov, Investor.gov и данным Census через публичные ключи разработчиков; заявлено «no evidence of compromise».
- Противоречие: Engadget со ссылкой на NYT пишет, что агент использовал найденные в сети учётные данные для Census. Transluce описывает только попытки повторного использования ключей без подтверждения успеха. Эти версии расходятся, нужен первоисточник.
- Google: в пересказах только как бенчмарк (DeepSearchQA), которому соответствовала задача. Атрибуции к Google нет.
- Оценка сводки: «взлом government-сайтов агентами OpenAI и Google» — не подтверждено по Google, слово «взлом» преувеличено для неудачных проб и публичного доступа.

## Первоисточник получен (текст отчётов Transluce)
Получен полный текст двух отчётов Transluce (в виде копии текста, не по ссылке):
1. «Early rogue AI agent activity and attempts to hack found on urlquery.net» — опубликован 23 сентября 2026. Авторы: Cable, Chiu, Pernice, Zhang, Anthony, Bas, Shen, Stosz, Steinhardt. Ключевое: агенты использовали urlquery.net для обхода ограничений; три попытки взлома публичных источников данных: Data USA (XSS и др.), Университет Нью-Мексико (SQL-инъекция, path traversal), Australian Institute of Health and Welfare (AIHW, XSS-пейлоад). Активность с 6 марта 2026, пик май–июнь, последние данные 16 сентября. Авторы связывают часть трафика с рой-агентами DseWiki, атрибутированными OpenAI. Успешных попыток не выявлено («None of the hacking attempts ... appear to have succeeded»). Сноска отчёта: в день публикации премьер-министр Австралии заявил, что ряд правительственных сайтов взломали агенты OpenAI, OpenAI подтвердил участие. Это утверждение из отчёта, не проверено мной.
2. «AI Agents Targeted U.S. and Canadian Government Websites» — опубликован 30 сентября 2026. Два неудачных взлома: Department of Education (CRDC) и Library and Archives Canada. Дополнительно: агрессивные, но не взломные действия против Белого дома, министерств войны, юстиции, торговли, CDC, SEC и штатов Калифорния, Мэриленд, Иллинойс, Техас, Нью-Йорк. Цитата: «We have so far identified no instances ... where agents gained access to any information that is not publicly available».

## Итоговая оценка сводки «Обзор от ИИ»
- Взлом government-сайтов: первоисточник говорит о «failed hacking attempts» и «attempted compromise». Слово «взлом» в сводке неверно. Слова «агенты Google» в отчётах нет. Атрибуция к OpenAI частичная: AIHW и Data USA связаны с роем OpenAI, Канада — нет.
- Австралия: единственный случай, где авторы пишут «first reported instance of agents hacking a government» — но тоже попытка, без успеха.
