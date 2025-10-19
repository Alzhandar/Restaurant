# 🔐 Environment Variables Guide

## Файлы окружения

### 📁 `.env` (локальная разработка)
Используется для запуска без Docker: `python manage.py runserver`

### 📁 `.env.docker.dev` (Docker development)
Используется в `docker-compose.dev.yml`

### 📁 `.env.docker.prod` (Docker production)
Используется в `docker-compose.yml`

### 📁 `.env.example` (шаблон)
Шаблон для копирования, не используется напрямую

---

## Полный список переменных

### Django Settings

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `SECRET_KEY` | ✅ Prod | `django-insecure-...` | Django secret key (мин. 50 символов) |
| `DEBUG` | ✅ | `True` | Режим отладки (`True`/`False`) |
| `ALLOWED_HOSTS` | ✅ Prod | `localhost,127.0.0.1` | Разрешённые хосты (через запятую) |

**Генерация SECRET_KEY:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

### Database Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `DB_ENGINE` | ✅ | `django.db.backends.sqlite3` | Engine базы данных |
| `DB_NAME` | ✅ | `db.sqlite3` | Имя базы данных |
| `DB_USER` | Для PostgreSQL | `postgres` | Пользователь БД |
| `DB_PASSWORD` | ✅ Prod | `postgres` | Пароль БД |
| `DB_HOST` | Для PostgreSQL | `localhost` | Хост БД (`db` в Docker) |
| `DB_PORT` | Для PostgreSQL | `5432` | Порт БД |

**Варианты DB_ENGINE:**
- `django.db.backends.sqlite3` — для локальной разработки
- `django.db.backends.postgresql` — для production

---

### Redis Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `REDIS_HOST` | ✅ | `localhost` | Хост Redis (`redis` в Docker) |
| `REDIS_PORT` | ✅ | `6379` | Порт Redis |
| `REDIS_DB` | ❌ | `0` | Номер БД Redis (0-15) |

---

### Celery Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `CELERY_BROKER_URL` | ✅ | `redis://localhost:6379/1` | URL брокера сообщений |
| `CELERY_RESULT_BACKEND` | ✅ | `redis://localhost:6379/2` | URL бэкенда результатов |

**Формат:**
```
redis://[password@]host:port/db_number
```

---

### JWT Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `JWT_ACCESS_TOKEN_LIFETIME` | ❌ | `15` | Время жизни access token (минуты) |
| `JWT_REFRESH_TOKEN_LIFETIME` | ❌ | `43200` | Время жизни refresh token (минуты, 30 дней) |

---

### Email Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `EMAIL_BACKEND` | ❌ | `console` | Backend для отправки email |
| `EMAIL_HOST` | Для SMTP | `smtp.gmail.com` | SMTP хост |
| `EMAIL_PORT` | Для SMTP | `587` | SMTP порт |
| `EMAIL_USE_TLS` | Для SMTP | `True` | Использовать TLS |
| `EMAIL_HOST_USER` | Для SMTP | - | Email адрес отправителя |
| `EMAIL_HOST_PASSWORD` | ✅ Prod SMTP | - | Пароль приложения |

**Email backends:**
- `django.core.mail.backends.console.EmailBackend` — вывод в консоль (dev)
- `django.core.mail.backends.smtp.EmailBackend` — отправка через SMTP (prod)
- `django.core.mail.backends.filebased.EmailBackend` — сохранение в файлы

---

### CORS Configuration

| Переменная | Обязательно | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `CORS_ALLOWED_ORIGINS` | ❌ | `http://localhost:3000,...` | Разрешённые origins (через запятую) |

---

## Примеры конфигураций

### Локальная разработка (`.env`)

```bash
# Минимальная конфигурация
SECRET_KEY=dev-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite (по умолчанию)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Redis (если запущен локально)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Docker Development (`.env.docker.dev`)

```bash
# Django
SECRET_KEY=dev-secret-key-for-docker
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### Docker Production (`.env.docker.prod`)

```bash
# Django - ⚠️ ИЗМЕНИТЬ ВСЕ!
SECRET_KEY=your-super-secret-key-minimum-50-characters-long-random-string
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# PostgreSQL - ⚠️ СИЛЬНЫЙ ПАРОЛЬ!
DB_ENGINE=django.db.backends.postgresql
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=YourStrongPassword123!@#
DB_HOST=db
DB_PORT=5432

# Redis - ⚠️ ДОБАВИТЬ ПАРОЛЬ!
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=YourRedisPassword123

# Celery
CELERY_BROKER_URL=redis://:YourRedisPassword123@redis:6379/1
CELERY_RESULT_BACKEND=redis://:YourRedisPassword123@redis:6379/2

# Email - ⚠️ НАСТРОИТЬ!
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# CORS - ⚠️ ВАШИ ДОМЕНЫ!
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Загрузка переменных в Django

В `settings.py` используется `python-dotenv`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка .env файла
load_dotenv(BASE_DIR / '.env')

# Использование переменных
SECRET_KEY = os.getenv('SECRET_KEY', 'default-value')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
```

---

## Security Best Practices

### ✅ DO:

1. **Используйте сильные пароли**
   ```bash
   DB_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Генерируйте уникальные SECRET_KEY**
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

3. **Используйте secrets manager в production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Docker Secrets

4. **Разные .env для каждого окружения**
   - `.env` — локально
   - `.env.docker.dev` — dev
   - `.env.docker.prod` — prod

5. **Добавьте .env в .gitignore**
   ```gitignore
   .env
   .env.local
   !.env.example
   ```

### ❌ DON'T:

1. ❌ Не коммитьте `.env` файлы с секретами
2. ❌ Не используйте `DEBUG=True` в production
3. ❌ Не используйте слабые пароли (`postgres`, `admin`, `123456`)
4. ❌ Не храните секреты в коде
5. ❌ Не используйте один SECRET_KEY везде

---

## Проверка конфигурации

### Проверить загруженные переменные

```python
# Django shell
python manage.py shell

from django.conf import settings
print(settings.DEBUG)
print(settings.DATABASES)
print(settings.ALLOWED_HOSTS)
```

### Проверить в Docker

```bash
# Показать все переменные в контейнере
docker-compose exec web env | grep -E "DB_|REDIS_|SECRET"

# Проверить конкретную переменную
docker-compose exec web sh -c 'echo $DB_HOST'
```

---

## Troubleshooting

### Проблема: переменные не загружаются

**Решение:**
1. Проверьте, что файл `.env` существует
2. Проверьте путь к файлу в `load_dotenv()`
3. Проверьте синтаксис в `.env` (без пробелов вокруг `=`)

```bash
# ✅ Правильно
DEBUG=True

# ❌ Неправильно
DEBUG = True
```

### Проблема: Docker не видит .env

**Решение:**
Используйте `env_file` в docker-compose:
```yaml
services:
  web:
    env_file:
      - .env.docker.dev
```

### Проблема: ошибка подключения к БД

**Решение:**
Проверьте:
1. `DB_HOST=db` (не `localhost` в Docker!)
2. Сервис БД запущен: `docker-compose ps`
3. Правильный пароль в `POSTGRES_PASSWORD` и `DB_PASSWORD`

---

## Миграция настроек

### Из `python-decouple` в `python-dotenv`

**Было:**
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='...')
DEBUG = config('DEBUG', default=True, cast=bool)
```

**Стало:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', '...')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

---

**Последнее обновление:** 19 октября 2025
