print("Здравствуйте!")
name=input("Как Вас зовут? ")
if name.strip()=="":
    print("Имя не может быть пустым")
else:
    age=int(input("Сколько Вам целых лет? "))
    if age < 18:
        print("Регистрация только с 18 лет")
    elif age > 120:
        print("Некорректный возраст")
    else:
        password=input("Придумайте пароль: ")
        if len(password) < 6:
            print("Пароль слишком короткий")
        else:
            password_confirm=input("Введите пароль ещё раз: ")
            if password_confirm != password:
                print("Пароли не совпадают")
            else:
                print("Регистрация успешна!")
                print(f"Имя: {name}")
                print(f"Возраст: {age}")