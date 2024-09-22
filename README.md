# Проект «Фудграм»

Проект «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Адрес работающего сервера - https://tstst.zapto.org

## Требования

Для запуска проекта вам понадобятся:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Установка и запуск

### 1. Клонирование репозитория

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Mask763/foodgram.git
```

```
cd foodgram
```

### 2. Настройка переменных окружения

Создайте файл .env в корневой директории проекта и добавьте в него необходимые переменные окружения. Пример можно посмотреть в файле .env.example

### 3. Запуск контейнеров

Запустите контейнеры с помощью docker-compose:

```
docker-compose up
```

Эта команда загрузит образы и запустит контейнеры. После завершения процесса вы сможете получить доступ к приложению по адресу http://localhost:8000.

### 4. Сбор статики и выполнение миграций

```
docker compose exec backend python manage.py collectstatic --no-input
docker compose exec backend python manage.py migrate
```

### 5. Загрузите теги и ингредиенты

```
docker compose exec backend python manage.py load_ingredients_from_json
docker compose exec backend python manage.py load_tags_from_json
```

### 6. Создание суперпользователя

```
docker compose exec backend python manage.py createsuperuser
```

## Основной стек

Проект написан с использованием Python 3.9, Django, Django REST Framework и Docker.

## Автор проекта

[Mask763](https://github.com/Mask763)
