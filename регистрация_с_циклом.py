import sys
print("Здравствуйте!")
while True:
    name = input("Введите имя: ")
    if name.strip() != "":
       break
    print("Имя не может быть пустым.")
while True:
    try:
        age = int(input("Ваш возраст: "))
    except ValueError:
        print("Нужно ввести число. Попробуйте ещё раз.")
        continue

    if age < 18:
        print("Регистрация только с 18 лет.")
        sys.exit()
    elif age > 120:
        print("Некорректный возраст. Попробуйте ещё раз.")
    else:
        break
while True:
    password = input("Придумайте пароль: ")
    if len(password)>=6:
        break
    print("Пароль должен быть не короче 6 символов.")
while True:
    password_confirm = input("Повторите пароль: ")
    if password != password_confirm:
        print("Пароли не совпадают. Попробуйте снова.")
    else:
        break
print("Регистрация успешна!")
print(f"Имя: {name}")
print(f"Возраст: {age}")