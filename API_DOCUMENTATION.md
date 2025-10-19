# API Endpoints Documentation

## Документация API

Проект использует **DRF Spectacular** для автоматической генерации документации OpenAPI 3.0.

### Доступ к документации

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema (JSON)**: http://localhost:8000/api/schema/

---

## Users API (`/api/users/`)

### Аутентификация

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| POST | `/api/users/login/` | Получение JWT токенов | Все |
| POST | `/api/users/token/refresh/` | Обновление access токена | Все |
| POST | `/api/users/register/` | Регистрация нового пользователя | Все |
| POST | `/api/users/logout/` | Выход (blacklist refresh token) | Авторизован |

### Управление профилем

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/users/profile/` | Получение профиля текущего пользователя | Авторизован |
| PUT/PATCH | `/api/users/profile/` | Обновление профиля | Авторизован |
| POST | `/api/users/change-password/` | Изменение пароля | Авторизован |

### Управление пользователями (Admin)

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/users/` | Список всех пользователей | Admin |
| GET | `/api/users/{id}/` | Детали пользователя | Admin/Owner |
| PUT/PATCH | `/api/users/{id}/` | Обновление пользователя | Admin |
| DELETE | `/api/users/{id}/` | Деактивация пользователя | Admin |

**Query параметры для списка**:
- `role` - фильтр по роли (guest, restaurant_owner, admin)
- `is_active` - фильтр по активности (true/false)

---

## Restaurants API (`/api/restaurants/`)

### Рестораны

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/restaurants/restaurants/` | Список ресторанов | Все |
| POST | `/api/restaurants/restaurants/` | Создание ресторана | Авторизован |
| GET | `/api/restaurants/restaurants/{id}/` | Детали ресторана | Все |
| PUT/PATCH | `/api/restaurants/restaurants/{id}/` | Обновление ресторана | Владелец/Admin |
| DELETE | `/api/restaurants/restaurants/{id}/` | Удаление ресторана | Владелец/Admin |

**Query параметры для списка**:
- `cuisine` - фильтр по типу кухни
- `min_rating` - минимальный рейтинг
- `ordering` - сортировка (например: `-created_at`, `name`, `average_rating`)

### Дополнительные endpoints ресторанов

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/restaurants/restaurants/search/?q=query` | Поиск ресторанов | Все |
| GET | `/api/restaurants/restaurants/my-restaurants/` | Мои рестораны | Владелец |
| POST | `/api/restaurants/restaurants/{id}/available-tables/` | Проверка доступных столиков | Все |

**Body для available-tables**:
```json
{
  "date": "2024-01-15",
  "start_time": "19:00",
  "end_time": "21:00",
  "party_size": 4
}
```

### Столики

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/restaurants/tables/` | Список столиков | Все |
| POST | `/api/restaurants/tables/` | Создание столика | Владелец ресторана |
| GET | `/api/restaurants/tables/{id}/` | Детали столика | Все |
| PUT/PATCH | `/api/restaurants/tables/{id}/` | Обновление столика | Владелец ресторана |
| DELETE | `/api/restaurants/tables/{id}/` | Удаление столика | Владелец ресторана |

**Query параметры для списка**:
- `restaurant_id` - фильтр по ресторану

---

## Reservations API (`/api/reservations/`)

### Бронирования

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/reservations/` | Список бронирований | Авторизован |
| POST | `/api/reservations/` | Создание бронирования | Авторизован |
| GET | `/api/reservations/{id}/` | Детали бронирования | Участник |
| PUT/PATCH | `/api/reservations/{id}/` | Обновление бронирования | Участник |
| DELETE | `/api/reservations/{id}/` | Отмена бронирования | Участник |

**Участник** = Пользователь создавший бронирование ИЛИ Владелец ресторана ИЛИ Admin

**Query параметры для списка**:
- `status` - фильтр по статусу (pending, confirmed, seated, completed, cancelled, no_show)
- `restaurant` - фильтр по ресторану (ID)
- `date_from` - бронирования от даты
- `date_to` - бронирования до даты

### Дополнительные endpoints бронирований

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/reservations/my-reservations/` | Мои бронирования | Авторизован |
| GET | `/api/reservations/upcoming/` | Предстоящие бронирования | Авторизован |
| GET | `/api/reservations/past/` | Прошедшие бронирования | Авторизован |
| PATCH | `/api/reservations/{id}/update-status/` | Обновление статуса | Владелец ресторана/Admin |

**Body для update-status**:
```json
{
  "status": "confirmed",
  "note": "Optional note"
}
```

**Допустимые переходы статусов**:
- pending → confirmed, cancelled
- confirmed → seated, cancelled
- seated → completed
- completed/cancelled/no_show → (финальные статусы)

---

## Reviews API (`/api/reviews/`)

### Отзывы

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/reviews/` | Список отзывов | Все |
| POST | `/api/reviews/` | Создание отзыва | Авторизован |
| GET | `/api/reviews/{id}/` | Детали отзыва | Все |
| PUT/PATCH | `/api/reviews/{id}/` | Обновление отзыва | Автор/Admin |
| DELETE | `/api/reviews/{id}/` | Удаление отзыва | Автор/Admin |

**Query параметры для списка**:
- `restaurant` - фильтр по ресторану (ID)
- `user` - фильтр по пользователю (ID)
- `min_rating` - минимальный рейтинг (1-5)

### Дополнительные endpoints отзывов

| Метод | Endpoint | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/api/reviews/my-reviews/` | Мои отзывы | Авторизован |
| GET | `/api/reviews/latest/` | Последние 20 отзывов | Все |
| GET | `/api/reviews/restaurant/{id}/` | Отзывы ресторана | Все |
| GET | `/api/reviews/restaurant/{id}/stats/` | Статистика отзывов | Все |
| GET | `/api/reviews/restaurant/{id}/can-review/` | Проверка возможности оставить отзыв | Авторизован |

**Response для stats**:
```json
{
  "restaurant_id": 1,
  "total_reviews": 42,
  "average_rating": 4.5,
  "rating_distribution": {
    "5": 20,
    "4": 15,
    "3": 5,
    "2": 1,
    "1": 1
  }
}
```

---

## Аутентификация и права доступа

### JWT Токены

Проект использует **Simple JWT** для аутентификации.

**Получение токенов**:
```bash
POST /api/users/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Использование в запросах**:
```
Authorization: Bearer <access_token>
```

**Обновление токена**:
```bash
POST /api/users/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Роли пользователей

1. **guest** (по умолчанию) - обычный пользователь:
   - Создание бронирований
   - Оставление отзывов
   - Просмотр ресторанов

2. **restaurant_owner** - владелец ресторана:
   - Все права guest
   - Создание и управление ресторанами
   - Управление столиками
   - Просмотр и изменение статусов бронирований своих ресторанов

3. **admin** - администратор:
   - Все права в системе
   - Управление пользователями
   - Модерация контента

### Custom Permissions

- `IsOwnerOrReadOnly` - редактирование только владельцем
- `IsRestaurantOwnerOrReadOnly` - редактирование только владельцем ресторана
- `IsReservationParticipant` - доступ участникам бронирования
- `IsReviewAuthorOrReadOnly` - редактирование только автором отзыва

---

## Примеры использования

### 1. Регистрация и вход

```bash
# Регистрация
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Вход
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123"
  }'
```

### 2. Создание ресторана

```bash
curl -X POST http://localhost:8000/api/restaurants/restaurants/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Italian Dream",
    "description": "Authentic Italian cuisine",
    "cuisine_type": "italian",
    "address": "123 Main St, City",
    "phone_number": "+77001234567",
    "email": "info@italiandream.com",
    "latitude": 51.1605,
    "longitude": 71.4704,
    "opening_time": "10:00",
    "closing_time": "23:00"
  }'
```

### 3. Создание бронирования

```bash
curl -X POST http://localhost:8000/api/reservations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant": 1,
    "table": 5,
    "reservation_date": "2024-12-20",
    "start_time": "19:00",
    "end_time": "21:00",
    "party_size": 4,
    "notes": "Window seat preferred"
  }'
```

### 4. Оставить отзыв

```bash
curl -X POST http://localhost:8000/api/reviews/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant": 1,
    "reservation": 10,
    "rating": 5,
    "comment": "Excellent food and service!"
  }'
```

---

## Коды ответов HTTP

- `200 OK` - успешный GET/PUT/PATCH запрос
- `201 Created` - успешное создание ресурса
- `204 No Content` - успешное удаление
- `400 Bad Request` - ошибка валидации
- `401 Unauthorized` - требуется аутентификация
- `403 Forbidden` - недостаточно прав
- `404 Not Found` - ресурс не найден
- `500 Internal Server Error` - ошибка сервера

---

## Пагинация

Все list endpoints поддерживают пагинацию:

```
GET /api/restaurants/restaurants/?page=2
```

**Response**:
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/restaurants/restaurants/?page=3",
  "previous": "http://localhost:8000/api/restaurants/restaurants/?page=1",
  "results": [...]
}
```

По умолчанию: **20 элементов на страницу** (настраивается в `settings.py`)
