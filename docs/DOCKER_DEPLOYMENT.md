# 🐳 Docker Deployment Guide

## Обзор

Проект включает полную Docker конфигурацию для development и production окружений.

---

## 📋 Содержание

- [Требования](#требования)
- [Development окружение](#development-окружение)
- [Production окружение](#production-окружение)
- [Makefile команды](#makefile-команды)
- [Настройка переменных окружения](#настройка-переменных-окружения)
- [Troubleshooting](#troubleshooting)

---

## Требования

- Docker 24.0+
- Docker Compose 2.20+
- Make (опционально, для удобных команд)

---

## Development окружение

### Быстрый старт

```bash
# Инициализация (первый запуск)
make init-dev

# Или вручную:
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Сервисы в Development

| Сервис | Порт | Описание |
|--------|------|----------|
| **web** | 8000 | Django API (runserver) |
| **db** | 5432 | PostgreSQL 16 |
| **redis** | 6379 | Redis Cache |
| **celery** | - | Celery Worker |
| **celery-beat** | - | Celery Scheduler |
| **flower** | 5555 | Celery Monitoring |

### Доступ к сервисам

```bash
# API
http://localhost:8000

# Admin Panel
http://localhost:8000/admin

# API Documentation (Swagger)
http://localhost:8000/api/docs/

# Flower (Celery Monitoring)
http://localhost:5555
```

### Полезные команды

```bash
# Логи
make dev-logs              # Все логи
make dev-logs-web          # Только Django
make dev-logs-celery       # Только Celery

# Shell доступ
make dev-shell             # Django shell
make dev-bash              # Bash в контейнере

# База данных
make dev-migrate           # Применить миграции
make dev-makemigrations    # Создать миграции

# Остановка
make dev-down              # Остановить все сервисы
```

---

## Production окружение

### Подготовка

1. **Создать .env файл:**

```bash
cp .env.example .env
```

2. **Настроить переменные окружения:**

```env
# ОБЯЗАТЕЛЬНО ИЗМЕНИТЬ
SECRET_KEY=your-super-secret-key-here-min-50-chars
DB_PASSWORD=strong-database-password
REDIS_PASSWORD=strong-redis-password

# Настроить под ваш домен
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Опционально
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=43200
```

3. **Сгенерировать SECRET_KEY:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Запуск Production

```bash
# Инициализация (первый запуск)
make init-prod

# Или вручную:
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser
```

### Сервисы в Production

| Сервис | Порт | Описание |
|--------|------|----------|
| **web** | - | Django API (Gunicorn) |
| **nginx** | 80, 443 | Reverse Proxy & Load Balancer |
| **db** | - | PostgreSQL 16 |
| **redis** | - | Redis Cache (с паролем) |
| **celery** | - | Celery Worker (4 workers) |
| **celery-beat** | - | Celery Scheduler |

### Доступ к Production

```bash
# Через Nginx
http://your-domain.com
https://your-domain.com  # После настройки SSL
```

### SSL/HTTPS Setup (Let's Encrypt)

```bash
# 1. Установить certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. Получить сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Раскомментировать SSL настройки в nginx/conf.d/default.conf

# 4. Перезапустить Nginx
docker-compose restart nginx
```

---

## Makefile команды

### Development

```bash
make dev-build              # Собрать контейнеры
make dev-up                 # Запустить окружение
make dev-down               # Остановить окружение
make dev-restart            # Перезапустить сервисы
make dev-logs               # Показать логи
make dev-shell              # Django shell
make dev-bash               # Bash shell
make dev-migrate            # Применить миграции
make dev-makemigrations     # Создать миграции
make dev-createsuperuser    # Создать суперпользователя
make dev-test               # Запустить тесты
make dev-collectstatic      # Собрать статику
```

### Production

```bash
make build                  # Собрать контейнеры
make up                     # Запустить окружение
make down                   # Остановить окружение
make restart                # Перезапустить сервисы
make logs                   # Показать логи
make shell                  # Django shell
make bash                   # Bash shell
make migrate                # Применить миграции
make makemigrations         # Создать миграции
make createsuperuser        # Создать суперпользователя
make collectstatic          # Собрать статику
```

### Database

```bash
make db-shell               # PostgreSQL shell
make db-backup              # Создать backup
make db-restore             # Восстановить из backup
```

### Testing

```bash
make test                   # Запустить тесты
make test-coverage          # Тесты с coverage
make lint                   # Проверить код (flake8, black)
make format                 # Форматировать код (black)
```

### Cleanup

```bash
make clean                  # Удалить контейнеры и volumes
make clean-images           # Удалить контейнеры, volumes и images
make prune                  # Полная очистка Docker
```

### Monitoring

```bash
make stats                  # Docker stats (CPU, Memory)
make ps                     # Список запущенных контейнеров
```

---

## Настройка переменных окружения

### Development (.env для docker-compose.dev.yml)

Не требуется, все задано в файле. Для кастомизации создайте `.env`:

```env
DEBUG=True
SECRET_KEY=dev-secret-key
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### Production (.env для docker-compose.yml)

**ОБЯЗАТЕЛЬНО создать файл `.env`:**

```env
# Django
SECRET_KEY=your-50-char-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=strong-db-password-here

# Redis
REDIS_PASSWORD=strong-redis-password-here

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=43200

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Flower (опционально)
# FLOWER_USER=admin
# FLOWER_PASSWORD=secure-password
```

---

## Архитектура

### Development

```
┌─────────────┐
│   Host OS   │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────┐
│         Docker Network                  │
│  ┌──────────┐  ┌──────────┐            │
│  │   Web    │  │   DB     │            │
│  │ :8000    │  │ :5432    │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │  Celery  │  │  Redis   │            │
│  │          │  │ :6379    │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │  Beat    │  │  Flower  │            │
│  │          │  │ :5555    │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

### Production

```
┌──────────────────────────────────────────┐
│              Internet                     │
└──────────────┬───────────────────────────┘
               │
        ┌──────▼──────┐
        │    Nginx    │  :80, :443
        │ (SSL Term)  │
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│  Web1  │ │  Web2  │ │  Web3  │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│   DB   │ │ Redis  │ │ Celery │ │  Beat  │
└────────┘ └────────┘ └────────┘ └────────┘
```

---

## Troubleshooting

### Проблема: Порт уже занят

```bash
# Найти процесс на порту
lsof -ti:8000

# Убить процесс
kill -9 $(lsof -ti:8000)

# Или изменить порт в docker-compose
```

### Проблема: Database connection refused

```bash
# Проверить, запущена ли БД
docker-compose ps

# Посмотреть логи БД
docker-compose logs db

# Перезапустить БД
docker-compose restart db
```

### Проблема: Permission denied

```bash
# Дать права на директории
chmod -R 755 logs media staticfiles

# Или пересобрать с правильными правами
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Проблема: Out of memory

```bash
# Увеличить memory limit в docker-compose.yml
services:
  web:
    mem_limit: 2g

# Или настроить Docker Desktop (Mac/Windows)
# Settings -> Resources -> Memory: 4GB+
```

### Проблема: Медленная сборка

```bash
# Использовать BuildKit
export DOCKER_BUILDKIT=1
docker-compose build

# Или в docker-compose.yml
version: '3.9'
x-build: &build-config
  DOCKER_BUILDKIT: 1
```

### Очистка всего Docker

```bash
# ВНИМАНИЕ: Удалит ВСЁ
docker system prune -af --volumes

# Более безопасно:
make clean  # Только этот проект
```

---

## Мониторинг

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f web
docker-compose logs -f celery

# Последние 100 строк
docker-compose logs --tail=100 web
```

### Ресурсы контейнеров

```bash
# Real-time мониторинг
docker stats

# Makefile команда
make stats
```

### Health Checks

```bash
# Проверка статуса
curl http://localhost/health/

# Статус контейнеров
docker-compose ps
```

---

## Бэкапы

### Автоматический бэкап БД

```bash
# Ручной бэкап
make db-backup

# Cron job для автоматического бэкапа (добавить в crontab)
0 2 * * * cd /path/to/project && make db-backup
```

### Восстановление

```bash
make db-restore
# Введите имя файла бэкапа
```

---

## Production Checklist

- [ ] Изменён SECRET_KEY (минимум 50 символов)
- [ ] DEBUG=False
- [ ] Настроен ALLOWED_HOSTS
- [ ] Настроен CORS_ALLOWED_ORIGINS
- [ ] Установлены сильные пароли для DB и Redis
- [ ] Настроен SSL/HTTPS
- [ ] Настроен firewall (только 80, 443)
- [ ] Настроены автоматические бэкапы
- [ ] Настроен мониторинг (Prometheus/Grafana)
- [ ] Настроены alert rules
- [ ] Протестирован failover
- [ ] Настроен log rotation
- [ ] Обновлены все зависимости

---

**Документ последний раз обновлён: 19 октября 2025**
