#Список дел
import json
import os

FILENAME = "tasks.json"

# функция загрузки данных
def load_tasks():
    if not os.path.exists(FILENAME):
        return []
    with open(FILENAME, "r", encoding="utf-8") as f:
        return json.load(f)

# функция сохранения данных
def save_tasks(tasks):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# функция добавления задачи
def add_task(tasks):
    task = input("Введите задачу (или Enter для выхода): ").strip()
    if task == "":
            print("Отмена.")
            return
    tasks.append({"task": task, "Выполнено": False})
    save_tasks(tasks)
    print(f"Задача '{task}' добавлена.")

# функция показа всех задач
def show_tasks(tasks):
    if not tasks:
        print("Активных задач не найдено")
    else:
        print("Ваши задачи: ")
        for i, task in enumerate(tasks, start=1):
            status = "[x]" if task["Выполнено"] else "[ ]"
            print(f"{i}. {status} {task['task']}")

# функция редактирования задачи
def edit_task(tasks):
    show_tasks(tasks)
    if not tasks:
        return
    user_input = input("Введите номер задачи для редактирования (или Enter для выхода): ").strip()
    if user_input == "":
        print("Отмена.")
        return
    try:
        number = int(user_input)
    except ValueError:
        print("Нужно ввести число")
        return
    if 1 <= number <= len(tasks):
        new_text = input("Введите новый текст задачи: ")
        if new_text == "":
            print("Отмена редактирования.")
            return
        tasks[number - 1]["task"] = new_text
        save_tasks(tasks)
        print(f"Задача {number} обновлена")
    else:
        print("Неверный номер задачи")

# функция удаления задачи
def delete_task(tasks):
    show_tasks(tasks)
    if not tasks:
        return
    user_input = input("Введите номер задачи для удаления (или Enter для выхода): ").strip()
    if user_input == "":
        print("Отмена.")
        return
    try:
        number = int(user_input)
    except ValueError:
        print("Нужно ввести число")
        return
    if 1 <= number <= len(tasks):
        deleted = tasks.pop(number - 1)
        save_tasks(tasks)
        print(f"Задача '{deleted['task']}' удалена")
    else:
        print("Неверный номер задачи")

# функция отметки выполнено
def toggle_task(tasks):
    show_tasks(tasks)
    if not tasks:
        return
    user_input = input("Введите номер задачи для отметки (или Enter для выхода): ").strip()
    if user_input == "":
        print("Отмена.")
        return
    try:
        num = int(user_input)
    except ValueError:
        print("Нужно ввести число")
        return
    if 1 <= num <= len(tasks):
        tasks[num-1]["Выполнено"] = not tasks[num-1]["Выполнено"]
        save_tasks(tasks)
        print("Статус обновлён")
    else:
        print("Неверный номер")

# функция main menu
def menu():
    tasks = load_tasks()
    while True:
        print("\nМеню:")
        print("1. Добавить задачу")
        print("2. Показать все задачи")
        print("3. Изменить статус задачи")
        print("4. Удалить задачу")
        print("5. Редактировать задачу")
        print("6. Сохранить и выйти")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            add_task(tasks)
        elif choice == "2":
            show_tasks(tasks)
        elif choice == "3":
            toggle_task(tasks)
        elif choice == "4":
            delete_task(tasks)
        elif choice == "5":
            edit_task(tasks)
        elif choice == "6":
            save_tasks(tasks)
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте ещё раз.")
# запуск
menu()