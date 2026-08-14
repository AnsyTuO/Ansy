PASSWORD="python123"
x=input("Введите пароль: ")
if x == PASSWORD:
    print("Доступ разрешён")
else:
    print("Неверный пароль")
    answer = input("Хотите попробовать снова? (да/нет) ")
    if answer.lower().strip() in ["да","yes"]:
        x = input("Введите пароль: ")
        if x == PASSWORD:
            print("Доступ разрешён")
        else:
            print("Снова неверный пароль")
            print("До свидания!")
    else:
        print("До свидания!")