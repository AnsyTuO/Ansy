#Список дел
import json
import os

FILENAME = "tasks.json"

from datetime import date

from colorama import init, Fore, Back, Style
init(autoreset=True)  # сбрасывает цвет после каждого вывода

# функция загрузки данных
def load_tasks():
    if not os.path.exists(FILENAME):
        return []
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        return tasks
    except (json.JSONDecodeError, ValueError, OSError):
        return []

# функция сохранения данных
def save_tasks(tasks):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# обработка ежедневных задач
def check_daily_reset(tasks):
    if not tasks:
        return tasks
    today = date.today().isoformat() # строка вида "2025-08-22"
    changed = False
    for task in tasks:
        if task.get("ежедневная"):
            if task.get("дата_сброса") != today:
                task["Выполнено"] = False
                task["дата_сброса"] = today
                changed = True
    if changed:
        save_tasks(tasks)
        print("Ежедневные задачи сброшены на новый день.")
    return tasks

# функция показа всех задач
def show_tasks(tasks):
    if not tasks:
        print(Fore.YELLOW + "Активных задач не найдено")
    else:
        print("Ваши задачи: ")
        for i, task in enumerate(tasks, start=1):
            if task["Выполнено"]:
                # зелёный для выполненных: крестик и текст
                status = Fore.GREEN + "[x]"
                text = Fore.GREEN + task['task']
            else:
                # без цвета для невыполненных
                status = "[ ]"
                text = task['task']

            daily_mark = ""
            if task.get("ежедневная"):
                daily_mark = Fore.CYAN + " (ежедневная)"

            print(f"{i}. {status} {text}{daily_mark}")

# ENTER для выхода и защита ошибки
def get_task_number(tasks, prompt):
    user_input = input(prompt).strip()
    if user_input == "":
        print("Отмена.")
        return None
    try:
        number = int(user_input)
    except ValueError:
        print("Нужно ввести число")
        return None
    if 1 <= number <= len(tasks):
        return number
    else:
        print("Неверный номер задачи")
        return None

# функция добавления задачи
def add_task(tasks):
    task = input("Введите задачу (или Enter для выхода): ").strip()
    if task == "":
        print("Отмена.")
        return

    daily = input("Сделать задачу ежедневной? (да/нет): ").strip().lower()
    is_daily = daily in ["да", "yes", "y", "д"]
    new_task = {
        "task": task,
        "Выполнено": False,
        "ежедневная": is_daily,
        "дата_сброса": date.today().isoformat() if is_daily else None
    }

    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Задача '{task}' добавлена.")

# функция редактирования задачи
def edit_task(tasks):
    if not tasks:
        print(Fore.YELLOW + "Активных задач не найдено")
        return
    show_tasks(tasks)
    number = get_task_number(tasks, "Введите номер задачи для редактирования (или Enter для выхода): ")
    if number is None:
        return
    new_text = input("Введите новый текст задачи: ")
    if new_text == "":
        print("Отмена редактирования.")
        return
    tasks[number - 1]["task"] = new_text
    save_tasks(tasks)
    print(f"Задача {number} обновлена")

# функция удаления задачи
def delete_task(tasks):

    if not tasks:
        print(Fore.YELLOW + "Активных задач не найдено")
        return

    show_tasks(tasks)

    user_input = input("Введите номера задач для удаления (или Enter для отмены): ").strip()
    if user_input == "":
        print("Отмена.")
        return
    
    parts = user_input.replace(",", " ").split()  # замена запятых на пробелы и разделение
    numbers = []

    for part in parts:
        if "-" in part:
            # диапазон: "2-4"
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start > end:
                    print(f"Диапазон '{part}' некорректен (начало больше конца). Пропущено.")
                    continue
                numbers.extend(range(start, end + 1))
            except ValueError:
                print(f"'{part}' не является корректным диапазоном. Пропущено.")
        else:
            # одиночное число
            try:
                num = int(part)
                numbers.append(num)
            except ValueError:
                print(f"'{part}' не является числом и будет пропущено.")

    if not numbers:
        print("Не введено ни одного корректного номера.")
        return

    unique_numbers = sorted(set(numbers), reverse=True)

    deleted_texts = []
    invalid_numbers = []
    for num in unique_numbers:
        if 1 <= num <= len(tasks):
            deleted = tasks.pop(num - 1)
            deleted_texts.append(deleted['task'])
        else:
            invalid_numbers.append(num)

    save_tasks(tasks)

    if deleted_texts:
        print(f"Удалено задач: {len(deleted_texts)}")
        for text in deleted_texts:
            print(f" - {text}")
    if invalid_numbers:
        print(f"Неверные номера (пропущены): {invalid_numbers}")

# функция отметки выполнено
def toggle_task(tasks):
    if not tasks:
        print(Fore.YELLOW + "Активных задач не найдено")
        return
    show_tasks(tasks)
    number = get_task_number(tasks, "Введите номер задачи для отметки (или Enter для выхода): ")
    if number is None:
        return
    tasks[number - 1]["Выполнено"] = not tasks[number - 1]["Выполнено"]
    save_tasks(tasks)
    print("Статус обновлён")

# функция поиска по слову
def find_task(tasks):
    if not tasks:
        print(Fore.YELLOW + "Активных задач не найдено")
        return

    query = input("Введите слово для поиска: ").strip().lower()
    if not query:
        print(Fore.YELLOW + "Поиск отменён.")
        return

    found = []
    for i, task in enumerate(tasks, start=1):
        if query in task["task"].lower():
            found.append((i, task))

    if not found:
        print(Fore.YELLOW + "Ничего не найдено.")
    else:
        print(f"Найдено задач: {len(found)}")
        for i, task in found:
            if task["Выполнено"]:
                status = Fore.GREEN + "[x]"
                text = Fore.GREEN + task['task']
            else:
                status = "[ ]"
                text = task['task']
            daily_mark = Fore.CYAN + " (ежедневная)" if task.get("ежедневная") else ""
            print(f"{i}. {status} {text}{daily_mark}")

# функция main menu
def menu():
    print("\nЗдравствуйте!")
    
    tasks = load_tasks()
    if tasks is None:
        tasks = []
    check_daily_reset(tasks)
    
    while True:
        print("\nМеню:")
        print("1. Показать все задачи")
        print("2. Добавить задачу")
        print("3. Изменить статус задачи")
        print("4. Редактировать задачу")
        print("5. Поиск задачи")
        print("6. Удалить задачу")
        print("7. Выйти")

        choice = input("\nВыберите действие: ").strip()

        if choice == "1":
            show_tasks(tasks)
            input("\nНажмите Enter, чтобы вернуться в меню...")
        elif choice == "2":
            add_task(tasks)
            input("\nНажмите Enter...")
        elif choice == "3":
            toggle_task(tasks)
            input("\nНажмите Enter...")
        elif choice == "4":
            edit_task(tasks)
            input("\nНажмите Enter...")
        elif choice == "5":
           find_task(tasks)
           input("\nНажмите Enter...")
        elif choice == "6":
            delete_task(tasks)
            input("\nНажмите Enter...")
        elif choice == "7":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте ещё раз.")
# запуск
menu()