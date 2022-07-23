# Yatube Social Network

Yatube - лучшая социальная сеть для того, чтобы делиться своими мыслями!

После регистрации Вы сможете писать текстовые посты и посты с изображениями. Доступно редактирование постов.

Вам нравится автор? Подпишитесь на него и следите за его публикациями в отдельной ленте
## Установка

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/sem4kulem4/yatube_social_network
```


Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
