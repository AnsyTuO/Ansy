tasks = []
while True:
    print("\nMenu")
    print("1. Добавить задачу")
    print("2. Показать все задачи")
    print("3. Удалить задачу")
    print("4. Редактировать задачу")
    print("5. Выйти")
    choice = input("Выберите действие: ")
    if choice == "1":
        task = input("Введите задачу: ")
        tasks.append(task)
        print(f"Задача '{task}' добавлена.")
    elif choice == "2":
        if not tasks:
            print("Список пуст.")
        else:
            print("Ваши задачи:")
            for i, task in enumerate(tasks, start=1):
                print(f"{i}. {task}")
    elif choice == "3":
        if not tasks:
            print("Список пуст, удалять нечего.")
            continue
        print("Ваши задачи:")
        for i, task in enumerate(tasks, start=1):
            print(f"{i}. {task}")
        try:
            number = int(input("Введите номер задачи для удаления: "))
        except ValueError:
            print("Нужно ввести число.")
            continue
        if 1 <= number <= len(tasks):
            deleted = tasks.pop(number - 1)
            print(f"Задача '{deleted}' удалена.")
        else:
            print("Неверный номер задачи.")
    elif choice == "4":
        if not tasks:
            print("Список пуст, изменять нечего.")
            continue
        print("Ваши задачи:")
        for i, task in enumerate(tasks, start=1):
            print(f"{i}. {task}")
        try:
            number = int(input("Введите номер задачи для редактирования: "))
        except ValueError:
             print("Нужно ввести число.")
             continue
        if 1 <= number <= len(tasks):
             task_redacted = input("Введите новый текст задачи: ")
             tasks[number-1] = task_redacted
             print(f"Задача {number} обновлена.")
        else:
            print("Неверный номер задачи.")
    elif choice == "5":
        print("До свидания!")
        break
    else:
        print("Неверный выбор. Попробуйте снова.")