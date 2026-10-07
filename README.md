# Мать лемматизаторов — черновик архитектуры

*Mother of Lemmatizers: a draft system design for one lemmatizer covering every language in Glottolog, kept in Markdown so that linguists can correct and discuss it section by section. English version: [`en/`](en/).*

Один лемматизатор для всех языков из списка Glottolog: он распознаёт язык каждого фрагмента текста, лемматизирует по выверенным грамматическим правилам, если они есть, а для незнакомого языка находит его родственников и выводит из их грамматик предварительную грамматику, опираясь на закономерности языковых изменений.

**Статус:** черновик 1 от 27 сентября 2026 года. Текст открыт для правок и обсуждения.

## Разделы

| | Русский | English |
|---|---|---|
| 0 | [Мать лемматизаторов](ru/00-title.md) | [Mother of Lemmatizers](en/00-title.md) |
| 1 | [Обзор](ru/01-overview.md) | [Overview](en/01-overview.md) |
| 2 | [Схема архитектуры](ru/02-architecture-schema.md) | [Architecture schema](en/02-architecture-schema.md) |
| 3 | [Распознавание языка](ru/03-language-recognition.md) | [Language recognition](en/03-language-recognition.md) |
| 4 | [Поиск родственников неизвестного языка](ru/04-finding-relatives-of-an-unknown-language.md) | [Finding relatives of an unknown language](en/04-finding-relatives-of-an-unknown-language.md) |
| 5 | [Лемматизация по готовым правилам (уровень A)](ru/05-lemmatizing-with-existing-rules-tier-a.md) | [Lemmatizing with existing rules (Tier A)](en/05-lemmatizing-with-existing-rules-tier-a.md) |
| 6 | [Язык известен, правил нет (уровень B)](ru/06-known-language-without-rules-tier-b.md) | [Known language without rules (Tier B)](en/06-known-language-without-rules-tier-b.md) |
| 7 | [Порождение грамматики неизвестного языка (уровень C)](ru/07-grammar-generation-for-an-unknown-language-tier-c.md) | [Grammar generation for an unknown language (Tier C)](en/07-grammar-generation-for-an-unknown-language-tier-c.md) |
| 8 | [Законы языковой эволюции, на которые опирается система](ru/08-laws-of-language-evolution-the-system-relies-on.md) | [Laws of language evolution the system relies on](en/08-laws-of-language-evolution-the-system-relies-on.md) |
| 9 | [Вход и выход](ru/09-input-and-output.md) | [Input and output](en/09-input-and-output.md) |
| 10 | [Соответствие нашей инфраструктуре](ru/10-mapping-to-our-stack.md) | [Mapping to our stack](en/10-mapping-to-our-stack.md) |
| 11 | [Оценка качества](ru/11-evaluation.md) | [Evaluation](en/11-evaluation.md) |
| 12 | [Ограничения и риски](ru/12-limits-and-risks.md) | [Limits and risks](en/12-limits-and-risks.md) |
| 13 | [Литература](ru/13-references.md) | [References](en/13-references.md) |

## Требования по языкам

Требования к конкретным языкам — свойства языка, которые лемматизатор обязан учитывать, пробелы в онтологии и контрольные примеры — лежат в папке [`languages/`](languages/), по папке на язык. Сейчас там венгерский: [`languages/hung1274-hungarian/`](languages/hung1274-hungarian/).

Каждый раздел — отдельный файл, поэтому правки и обсуждения разных разделов не мешают друг другу. Номера файлов в `ru/` и `en/` совпадают.

Схемы написаны на [Mermaid](https://mermaid.js.org/) прямо в тексте раздела: GitHub рисует их при просмотре, а правятся они как обычный текст.

В папке [`original/`](original/) лежат PDF первого черновика (русский и английский) — это неизменяемый снимок, с которого начато обсуждение. Актуальный текст — в Markdown-файлах.

## Как обсуждать и вносить правки

- **Замечание к конкретному месту** — откройте pull request с правкой и объясните её в описании, или оставьте комментарий к строке в чужом pull request'е.
- **Вопрос или спорный момент без готовой правки** — заведите Issue по шаблону «Замечание к разделу».
- **Свободное обсуждение идей** — вкладка Discussions.

Прямые коммиты в `main` запрещены. Любое изменение вносится через pull request и должно получить одно одобрение от другого участника. Подробности — в [CONTRIBUTING.md](CONTRIBUTING.md).

## Еженедельная сводка

Каждое воскресенье в 18:00 UTC GitHub Actions собирает все pull request'ы, слитые за прошедшую неделю, и публикует сводку на русском языке — кто и что изменил, по разделам — в виде Issue с меткой `digest` и заголовком «Сводка mother-of-lemmatizers-design: …». Если изменений не было, в Issue будет короткое сообщение «За неделю изменений нет». Все сводки собраны на вкладке Issues (фильтр по метке `digest`). Скрипт: [`scripts/weekly_digest.py`](scripts/weekly_digest.py).

Изменения группируются по разделам: правка `ru/03-language-recognition.md` попадёт в группу `ru/03-language-recognition`, изменения требований к языку — в группу языка (например, `languages/hung1274-hungarian`), а остальные изменения — в группу «Прочее».

### Как получать сводку на электронную почту

Письмо с новой сводкой рассылает сам GitHub. Есть два способа его получать:

- **Попасть в список получателей.** Мейнтейнер добавляет ваш логин GitHub в переменную репозитория `DIGEST_NOTIFY` (Settings → Secrets and variables → Actions → Variables; логины через пробел, запятую или точку с запятой). Тогда сводка начинается со строки «Для: @ваш-логин», и GitHub уведомляет вас. Переменная необязательна: если она пуста, строки «Для:» в сводке нет и письмо получают только те, кто подписан на репозиторий.
- **Подписаться на репозиторий самостоятельно.** Нажмите Watch → «All Activity» либо Custom → Issues на странице репозитория.

В обоих случаях в [настройках уведомлений GitHub](https://github.com/settings/notifications) должна быть включена доставка на электронную почту.

Важно: репозиторий публичный, поэтому Issue со сводкой — включая логины из строки «Для:» — видно всем.

Очень большие недели сокращаются: сначала из сводки убираются списки файлов, а если и этого мало — показывается только начало списка pull request'ов, и в конце указано, что показаны не все изменения. Так сводка укладывается в ограничение GitHub на размер Issue.

> **Ограничение GitHub.** Если в публичном репозитории 60 дней нет активности, запланированные workflow отключаются автоматически, и сводки перестают появляться. Если это случилось, включите workflow заново на вкладке Actions. Пропущенную сводку мейнтейнер может опубликовать вручную — запустите workflow на вкладке Actions с выключенным `dry_run`; это сработает только до следующего воскресенья 18:00 UTC, потому что окно сводки привязано к календарю. Ручной запуск в том же окне, за которое сводка уже опубликована по расписанию, создаст второй Issue.

## Лицензия

[CC-BY-4.0](LICENSE): материалы можно использовать и изменять, указывая авторство.
