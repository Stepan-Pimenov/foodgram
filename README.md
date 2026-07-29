# Foodgram

![Main Foodgram workflow](https://github.com/Stepan-Pimenov/foodgram/actions/workflows/main.yml/badge.svg)

Сайт для публикации рецептов. Пользователи могут делиться своими рецептами,
добавлять чужие в избранное, подписываться на авторов и собирать список
покупок с продуктами для выбранных блюд.

## Возможности

- Регистрация и авторизация по токену.
- Публикация, редактирование и удаление своих рецептов.
- Избранное и подписки на авторов.
- Список покупок с выгрузкой файла (продукты суммируются).
- Фильтрация рецептов по тегам, поиск продуктов по названию.
- Короткие ссылки на рецепты.

## Стек

Python 3.12, Django, Django REST framework, Djoser, PostgreSQL, Docker,
Nginx, Gunicorn, GitHub Actions.

## Запуск проекта локально

Клонировать репозиторий и перейти в его папку:

```
git clone https://github.com/Stepan-Pimenov/foodgram.git
cd foodgram
```

Создать файл `.env` в корне проекта (пример - в `.env.example`):

```
SECRET_KEY=ваш-секретный-ключ
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
```

Запустить контейнеры:

```
docker compose up -d
```

Выполнить миграции, собрать статику и загрузить данные:

```
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py import_data
docker compose exec backend python manage.py fill_test_data
```

Проект будет доступен по адресу http://localhost:8000/

## Наполнение базы данными

- `import_data` - загружает продукты и теги из `backend/data/`.
- `fill_test_data` - создаёт администратора, тестовых пользователей и рецепты.

## Развёрнутый проект

https://foodgram-by-stepan.duckdns.org

Админка: https://foodgram-by-stepan.duckdns.org/admin/

## Автор

Степан Пименов, [Stepan-Pimenov](https://github.com/Stepan-Pimenov)
