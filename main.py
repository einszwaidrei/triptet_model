from graph_actions.manual_triplet import process_manual_triplet
from graph_actions.text_upload import process_text_input
from graph_actions.graph_update import update_graph_with_buffer
from graph_actions.object_query import query_object_relations
from graph_actions.relation_similarity import query_similar_triplet
from graph_actions.relation_path import query_relation_path


def main():
    while True:
        print("\n=== Меню системы ===")
        print("1. Режим онтолога")
        print("2. Найти связи у объекта")
        print("3. Найти похожие связи у двух объектов")
        print("4. Найти непрямую связь между двумя объектами")
        print("0. Выход")

        choice = input("Выберите опцию: ").strip()

        if choice == "1":
            print("\n--- Режим онтолога ---")
            print("a) Обновить граф")
            print("b) Загрузить один триплет вручную")
            print("c) Загрузить текст и извлечь триплеты")
            print("x) Назад")

            subchoice = input("Выберите подопцию: ").strip().lower()
            if subchoice == "a":
                update_graph_with_buffer()
            elif subchoice == "b":
                subj = input("Субъект: ").strip()
                pred = input("Предикат: ").strip()
                obj = input("Объект: ").strip()
                descr = input("Описание (необязательно): ").strip()
                triplet = {"subject": subj, "predicate": pred, "object": obj, "description": descr}
                process_manual_triplet(triplet)
            elif subchoice == "c":
                text = input("Введите текст: ")
                process_text_input(text)
            elif subchoice == "x":
                continue

        elif choice == "2":
            query_object_relations()

        elif choice == "3":
            query_similar_triplet()

        elif choice == "4":
            query_relation_path()

        elif choice == "0":
            print("\n Программа завершена")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
