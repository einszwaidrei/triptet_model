from graph_builder.yandex_gpt_integration import get_triplets_from_yandex
from graph_actions.buffer import save_to_buffer
from datetime import datetime


def process_text_input(text: str):
    print("\n Отправка текста в Yandex GPT")
    triplets = get_triplets_from_yandex(text)

    if not triplets:
        print("Модель не вернула триплетов.")
        return

    print(f"\n Найдено {len(triplets)} триплетов:\n")
    for i, t in enumerate(triplets, 1):
        print(f"[{i}] {t['subject']} —[{t['predicate']}]-> {t['object']} | {t.get('description', '')}")

    print("\nВыберите действие:")
    print("[a] Добавить все триплеты в буфер")
    print("[n] Ничего не делать")

    choice = input("Введите команду (a/n): ").strip().lower()

    if choice == "a":
        for t in triplets:
            t["date_added"] = datetime.utcnow().isoformat()
            save_to_buffer(t)
        print(f"Добавлено {len(triplets)} триплетов в буфер.")
    elif choice == "n":
        print("Действие отменено. Текст и триплеты сброшены.")
