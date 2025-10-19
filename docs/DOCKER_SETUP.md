# 🐳 Docker Setup Guide

## Быстрый старт

### Development (с hot-reload)

```bash
# 1. Создать .env файл из примера
cp .env.example .env.docker.dev

# 2. Отредактировать .env.docker.dev если нужно

# 3. Собрать и запустить контейнеры
make dev-up

# Или без Makefile:
docker-compose -f docker-compose.dev.yml up --build
```

Сервисы будут доступны:
- **API:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **Flower (Celery):** http://localhost:5555 (admin/admin123)
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### Production

```bash
# 1. Создать .env файл для production
cp .env.example .env.docker.prod

# 2. ОБЯЗАТЕЛЬНО изменить:
#    - SECRET_KEY
#    - DB_PASSWORD
#    - ALLOWED_HOSTS
#    - DEBUG=False

# 3. Собрать и запустить
make prod-up

# Или без Makefile:
docker-compose up -d --build
```

---

## Структура .env файлов

### `.env` — локальная разработка (без Docker)
Используется при запуске `python manage.py runserver`

### `.env.docker.dev` — Docker development
Используется в `docker-compose.dev.yml`
- SQLite можно заменить на PostgreSQL
- DEBUG=True
- Горячая перезагрузка кода

### `.env.docker.prod` — Docker production
Используется в `docker-compose.yml`
- PostgreSQL обязателен
- DEBUG=False
- Gunicorn вместо runserver

---

## Переменные окружения

### Обязательные для Production:

```bash
# Django
SECRET_KEY=your-super-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_PASSWORD=your_strong_password
POSTGRES_PASSWORD=your_strong_password

# Flower (если используется)
FLOWER_USER=admin
FLOWER_PASSWORD=strong_password
```

### Опциональные:

```bash
# Redis
REDIS_PASSWORD=redis_password  # для production

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## Основные команды

### Development

```bash
# Запуск
make dev-up              # Запустить в foreground
make dev-up-d            # Запустить в background

# Остановка
make dev-down            # Остановить контейнеры
make dev-restart         # Перезапустить

# Логи
make dev-logs            # Показать все логи
docker-compose -f docker-compose.dev.yml logs web -f  # Только web

# Shell
make dev-shell           # Python shell
make dev-bash            # Bash в контейнере

# База данных
make migrate             # Применить миграции
make makemigrations      # Создать миграции
make createsuperuser     # Создать суперпользователя

# Тесты
make dev-test            # Запустить тесты

# Очистка
make dev-clean           # Остановить и удалить volumes
```

### Production

```bash
# Запуск
make prod-up             # Запустить
make prod-down           # Остановить
make prod-restart        # Перезапустить

# Логи
make prod-logs

# Мониторинг
make ps                  # Статус контейнеров
make stats               # Статистика ресурсов

# Backup
make db-backup           # Создать backup БД
make db-restore FILE=backups/backup_file.sql  # Восстановить

# Очистка
make prod-clean          # Очистить (БЕЗ удаления данных)
```

---

## Архитектура Docker

### Development (`docker-compose.dev.yml`)

```
┌─────────────┐
│   Host OS   │
└──────┬──────┘
       │
   ┌───┴────┐
   │ Docker │
   └───┬────┘
       │
       ├──▶ db (PostgreSQL:5432)
       ├──▶ redis (Redis:6379)
       ├──▶ web (Django:8000) ← hot-reload
       ├──▶ celery (Worker)
       ├──▶ celery-beat (Scheduler)
       └──▶ flower (Monitoring:5555)
```

### Production (`docker-compose.yml`)

```
┌──────────┐
│ Internet │
└─────┬────┘
      │
      ▼
┌───────────┐
│   Nginx   │ :80, :443
│   (SSL)   │
└─────┬─────┘
      │
      ▼
┌───────────┐
│    web    │ Gunicorn
│  Django   │ 4 workers
└─────┬─────┘
      │
   ┌──┴──┬────────┬─────────┐
   ▼     ▼        ▼         ▼
 ┌──┐  ┌────┐  ┌──────┐  ┌──────┐
 │db│  │redis│ │celery│  │beat  │
 └──┘  └────┘  └──────┘  └──────┘
```

---

## Volumes (данные)

### Development
- `postgres_data_dev` — база данных
- `redis_data_dev` — Redis persistence
- `static_volume` — статические файлы
- `media_volume` — загруженные файлы

### Production
- `postgres_data` — **КРИТИЧНО!** Не удалять
- `redis_data` — Redis persistence
- `static_volume` — CDN или Nginx
- `media_volume` — файлы пользователей

**⚠️ Важно:** `prod-clean` НЕ удаляет volumes!

---

## Troubleshooting

### Ошибка: порт занят

```bash
# Проверить занятые порты
lsof -i :8000
lsof -i :5432

# Остановить процесс
kill -9 <PID>
```

### Ошибка: cannot connect to database

```bash
# Проверить, что БД запущена
docker-compose ps

# Проверить логи БД
docker-compose logs db

# Пересоздать БД (⚠️ ПОТЕРЯ ДАННЫХ)
docker-compose down -v
docker-compose up db
```

### Ошибка: миграции не применяются

```bash
# Вручную применить миграции
docker-compose exec web python manage.py migrate

# Проверить состояние
docker-compose exec web python manage.py showmigrations
```

### Очистка всего Docker

```bash
# ⚠️ ОСТОРОЖНО: удалит ВСЕ контейнеры и volumes
make prune

# Или:
docker system prune -af --volumes
```

---

## Best Practices

### Development

✅ Используйте `.env.docker.dev` для настроек
✅ Volumes для hot-reload кода
✅ Отдельные порты (8000, 5432, 6379)
✅ `runserver` для удобства отладки

❌ Не используйте production secrets
❌ Не коммитьте `.env` файлы

### Production

✅ Используйте секреты из CI/CD или secrets manager
✅ Настройте SSL/TLS через Nginx
✅ Используйте Gunicorn с несколькими workers
✅ Регулярные backups БД
✅ Мониторинг (Flower, Grafana)
✅ Log rotation

❌ DEBUG=False обязательно
❌ Не используйте слабые пароли
❌ Не храните secrets в .env файлах в репозитории

---

## Миграция с SQLite на PostgreSQL

```bash
# 1. Сделать backup SQLite
python manage.py dumpdata > db_backup.json

# 2. Изменить .env на PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=restaurant_db
# ... остальные DB_* переменные

# 3. Запустить PostgreSQL
docker-compose up -d db

# 4. Применить миграции
python manage.py migrate

# 5. Загрузить данные
python manage.py loaddata db_backup.json
```

---

## Мониторинг

### Проверка здоровья контейнеров

```bash
docker-compose ps
```

Все контейнеры должны быть в статусе `healthy` или `running`.

### Логи в реальном времени

```bash
# Все сервисы
docker-compose logs -f

# Только web
docker-compose logs -f web

# Только errors
docker-compose logs | grep ERROR
```

### Flower (Celery UI)

http://localhost:5555

- Мониторинг задач
- История выполнения
- Статистика workers
- Логин: admin/admin123 (dev)

---

## Дополнительные ресурсы

- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

**Последнее обновление:** 19 октября 2025
