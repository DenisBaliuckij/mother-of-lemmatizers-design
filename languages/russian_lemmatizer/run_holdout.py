import json
from pathlib import Path
from russian_lemmatizer import RussianLemmatizer

# Загружаем лемматизатор с уже исправленными путями
lem = RussianLemmatizer(
    ontology_path="OntoRussian.json",
    dev_path="russian-development.yaml",
    rules_dir="rules/ru"
)

# Запускаем оценку на holdout
print("Запуск оценки на holdout...")
results = lem.evaluate("russian-holdout.yaml")

# Выводим результаты в консоль
print(f"\n--- РЕЗУЛЬТАТЫ НА HOLDOUT ---")
print(f"Точность (токены):       {results['accuracy']:.4f}")
print(f"Точность (без регистра): {results['accuracy_case_insensitive']:.4f}")
print(f"Точность (предложения):  {results['sentence_accuracy']:.4f}")
print(f"Всего токенов:           {results['total']}")
print(f"Правильных токенов:      {results['correct']}")
print(f"CSV с ошибками сохранен: {results['csv_path']}")

# Сохраняем короткий отчет в md-файл
report_path = Path("ru-holdout-report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# Отчет по оценке на Holdout (Русский)\n\n")
    f.write(f"- **Точность (токены)**: {results['accuracy']:.4f}\n")
    f.write(f"- **Точность (без регистра)**: {results['accuracy_case_insensitive']:.4f}\n")
    f.write(f"- **Точность (предложения)**: {results['sentence_accuracy']:.4f}\n")
    f.write(f"- **Всего токенов**: {results['total']}\n")
    f.write(f"- **Правильных**: {results['correct']}\n\n")

    f.write("## Ошибки по категориям (by_confidence)\n")
    for conf, data in results['by_confidence'].items():
        f.write(f"- `{conf}`: {data['correct']}/{data['total']} (точность {data['accuracy']:.4f})\n")

print(f"\nОтчет сохранен в {report_path.resolve()}")
