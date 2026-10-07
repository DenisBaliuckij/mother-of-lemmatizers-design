# Требования по языкам

*Language-specific requirements. English below.*

Разделы `ru/` и `en/` описывают лемматизатор независимо от языка. Здесь собраны требования к конкретным языкам: какие свойства языка лемматизатор обязан учитывать, что из этого уже есть в онтологии языковых ресурсов и на каких контрольных примерах это проверять.

| Язык | Glottocode | Уровень | Требования | Статус |
|---|---|---|---|---|
| Венгерский | `hung1274` | A | [ru](hung1274-hungarian/ru.md) · [en](hung1274-hungarian/en.md) · [профиль](hung1274-hungarian/profile.yaml) · [примеры](hung1274-hungarian/test-cases.tsv) | на рецензии |

## Устройство папки языка

Папка называется `<glottocode>-<язык по-английски>`: glottocode — ключ языка во всей системе (см. контракт в [разделе 9](../ru/09-input-and-output.md)), название — для удобства чтения.

| Файл | Что в нём |
|---|---|
| `ru.md`, `en.md` | Требования в таблицах по темам. У каждого требования постоянный номер `<КОД>-NN` (для венгерского `HU-01`…) и компонент уровня A, на который оно ложится. Затем — выводы для архитектуры, пробелы в онтологии, готовые анализаторы, замечания при переносе из исходного документа и источники |
| `profile.yaml` | Предлагаемые вычислительные подразделы языкового профиля онтологии (таблицы исключений, особые морфемы, правила чередований) в машиночитаемом виде |
| `test-cases.tsv` | Контрольные примеры, по одному на строку, столбцы через табуляцию: `id`, `form` (словоформа), `context` (фраза, если без неё лемму не определить), `lemma`, `features` (признаки в стиле Universal Dependencies, только однозначные), `requirements` (номера требований), `note` |

Номера требований не меняются и не используются повторно: удалённое требование помечается как снятое, новое получает следующий номер. Так ссылки из обсуждений и pull request'ов остаются верными.

## Как добавить язык

1. Скопируйте папку `hung1274-hungarian/` под новым именем и очистите содержимое, сохранив заголовки.
2. Найдите glottocode языка на [glottolog.org](https://glottolog.org/) и выберите двух-трёхбуквенный код для номеров требований.
3. Добавьте строку в таблицу выше.
4. Откройте pull request; в еженедельной сводке изменения языка собираются в группу `languages/<папка>`.

---

# Language-specific requirements

The sections in `ru/` and `en/` describe the lemmatizer independently of any language. This folder collects requirements for particular languages: which properties of the language the lemmatizer must handle, which of them the language-resource ontology already covers, and which test cases check them.

Each language has a folder `<glottocode>-<English name>` with `ru.md` and `en.md` (the requirements, each with a permanent ID such as `HU-01` and the Tier A component it falls on), `profile.yaml` (proposed computational subsections of the ontology's language profile) and `test-cases.tsv` (tab-separated test cases: `id`, `form`, `context`, `lemma`, `features`, `requirements`, `note`). Requirement IDs are never changed or reused. To add a language, copy the Hungarian folder, clear it, add a row to the table above and open a pull request; the weekly digest groups its changes under `languages/<folder>`.
