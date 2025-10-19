# 📐 Обзор проекта и архитектура

## Restaurant Reservation System — Highload Backend

---

## 🎯 Цель проекта

Разработать высоконагруженную backend-систему для бронирования столиков в ресторанах, которая способна обрабатывать:
- **10,000+ запросов в секунду** в пиковые часы
- **Конкурентные бронирования** одного столика
- **Миллионы пользователей** по всему миру
- **Real-time уведомления** о статусе бронирования

---

## 🏗️ Архитектура системы

### High-Level архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                      │
│              SSL Termination, Rate Limiting                   │
└────────────┬──────────────────────────────────┬───────────────┘
             │                                  │
    ┌────────▼────────┐              ┌─────────▼──────────┐
    │  Django API #1  │              │  Django API #2     │
    │   (Web Server)  │              │   (Web Server)     │
    └────────┬────────┘              └─────────┬──────────┘
             │                                  │
             └──────────────┬───────────────────┘
                            │
        ┌───────────────────┼───────────────────────┐
        │                   │                       │
        ▼                   ▼                       ▼
┌───────────────┐   ┌──────────────┐      ┌────────────────┐
│  PostgreSQL   │   │    Redis     │      │  ElasticSearch │
│  (Primary DB) │   │    (Cache)   │      │ (Full-text)    │
└───────────────┘   └──────────────┘      └────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    Message Queue (RabbitMQ)               │
└─────────────────────┬─────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│Celery Worker │ │  Celery  │ │  Celery  │
│   #1         │ │ Worker#2 │ │ Worker#3 │
└──────┬───────┘ └────┬─────┘ └────┬─────┘
       │              │            │
       └──────────────┼────────────┘
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
      ┌──────────────┐   ┌──────────┐
      │Email Service │   │  Sentry  │
      │(SendGrid)    │   │ (Errors) │
      └──────────────┘   └──────────┘

        Мониторинг и метрики
┌────────────┐    ┌──────────┐    ┌───────────┐
│ Prometheus │───▶│ Grafana  │    │  Flower   │
│  (Metrics) │    │(Dashboard)    │ (Celery)  │
└────────────┘    └──────────┘    └───────────┘
```

---

## 🗂️ Структура базы данных

### ER-диаграмма

```
┌──────────────────┐
│      User        │
├──────────────────┤
│ id (PK)          │
│ email (unique)   │
│ password_hash    │
│ first_name       │
│ last_name        │
│ phone            │
│ role             │◀────┐
│ is_active        │     │
│ created_at       │     │
└────────┬─────────┘     │
         │               │
         │ 1             │
         │               │ 1
         │ *             │
┌────────▼─────────┐     │
│   Restaurant     │     │
├──────────────────┤     │
│ id (PK)          │     │
│ owner_id (FK)────┼─────┘
│ name             │
│ address          │
│ city             │
│ cuisine_type     │
│ description      │
│ phone            │
│ email            │
│ opening_time     │
│ closing_time     │
│ latitude         │
│ longitude        │
│ average_rating   │
│ total_reviews    │
│ is_active        │
│ created_at       │
└────────┬─────────┘
         │
         │ 1
         │
         │ *
┌────────▼─────────┐
│      Table       │
├──────────────────┤
│ id (PK)          │
│ restaurant_id(FK)│
│ table_number     │
│ capacity         │
│ location_in_rest │
│ is_available     │
└────────┬─────────┘
         │
         │ 1
         │
         │ *
┌────────▼─────────────┐         ┌──────────────┐
│    Reservation       │         │    Review    │
├──────────────────────┤         ├──────────────┤
│ id (PK)              │    ┌───▶│ id (PK)      │
│ user_id (FK)─────────┼────┘    │ user_id (FK) │
│ restaurant_id (FK)   │         │ restaurant(FK│
│ table_id (FK)        │         │ reservation  │
│ date                 │         │ rating       │
│ time_slot            │         │ comment      │
│ guests_count         │         │ created_at   │
│ status               │         └──────────────┘
│ special_requests     │
│ confirmation_sent    │
│ reminder_sent        │
│ created_at           │
│ updated_at           │
└──────────────────────┘
```

### Индексы для производительности

```sql
-- User
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_role ON users(role);

-- Restaurant
CREATE INDEX idx_restaurant_city ON restaurants(city);
CREATE INDEX idx_restaurant_cuisine ON restaurants(cuisine_type);
CREATE INDEX idx_restaurant_owner ON restaurants(owner_id);
CREATE INDEX idx_restaurant_location ON restaurants USING GIST(point(latitude, longitude));

-- Table
CREATE INDEX idx_table_restaurant ON tables(restaurant_id);
CREATE INDEX idx_table_capacity ON tables(capacity);

-- Reservation
CREATE INDEX idx_reservation_user ON reservations(user_id);
CREATE INDEX idx_reservation_restaurant ON reservations(restaurant_id);
CREATE INDEX idx_reservation_table ON reservations(table_id);
CREATE INDEX idx_reservation_date ON reservations(date);
CREATE INDEX idx_reservation_status ON reservations(status);
CREATE INDEX idx_reservation_datetime ON reservations(date, time_slot);

-- Review
CREATE INDEX idx_review_restaurant ON reviews(restaurant_id);
CREATE INDEX idx_review_user ON reviews(user_id);
CREATE INDEX idx_review_rating ON reviews(rating);
```

---

## 🔄 Поток данных

### 1. Создание бронирования (Happy Path)

```
Клиент                Django API              PostgreSQL        Redis           RabbitMQ          Celery
  │                       │                       │                │                │               │
  ├──POST /reservations──▶│                       │                │                │               │
  │                       │                       │                │                │               │
  │                       ├──Валидация данных─────┤                │                │               │
  │                       │                       │                │                │               │
  │                       ├──Проверка доступности─┤                │                │               │
  │                       │  (table available?)   │                │                │               │
  │                       │◀──────────────────────┤                │                │               │
  │                       │                       │                │                │               │
  │                       ├──BEGIN TRANSACTION────▶│                │                │               │
  │                       │                       │                │                │               │
  │                       ├──INSERT reservation───▶│                │                │               │
  │                       │                       │                │                │               │
  │                       ├──COMMIT───────────────▶│                │                │               │
  │                       │◀──────────────────────┤                │                │               │
  │                       │                       │                │                │               │
  │                       ├──Invalidate cache─────┼───────────────▶│                │               │
  │                       │  (available_tables)   │                │                │               │
  │                       │                       │                │                │               │
  │                       ├──Publish task─────────┼────────────────┼───────────────▶│               │
  │                       │  (send_confirmation)  │                │                │               │
  │                       │                       │                │                │               │
  │◀──201 Created─────────┤                       │                │                │               │
  │   {reservation_data}  │                       │                │                │               │
  │                       │                       │                │                │               │
  │                       │                       │                │                ├──Task picked──▶│
  │                       │                       │                │                │               │
  │                       │                       │                │                │     Send      │
  │                       │                       │                │                │     Email     │
  │                       │                       │                │                │               │
  │                       │                       │                │                │◀──Task done───┤
```

### 2. Поиск доступных столиков с кэшем

```
Клиент                Django API              Redis           PostgreSQL
  │                       │                       │                │
  ├──GET /available───────▶│                       │                │
  │  ?date=2025-12-20     │                       │                │
  │  &time=19:00          │                       │                │
  │                       │                       │                │
  │                       ├──Check cache──────────▶│                │
  │                       │  key: available_...   │                │
  │                       │                       │                │
  │                       │◀──CACHE MISS──────────┤                │
  │                       │                       │                │
  │                       ├──Complex query────────┼───────────────▶│
  │                       │  (check reservations) │                │
  │                       │                       │                │
  │                       │◀──Result──────────────┼────────────────┤
  │                       │                       │                │
  │                       ├──Set cache────────────▶│                │
  │                       │  TTL: 60 sec          │                │
  │                       │                       │                │
  │◀──200 OK──────────────┤                       │                │
  │  [available_tables]   │                       │                │
```

### 3. Обработка No-Show

```
Scheduler            Celery Worker         PostgreSQL        RabbitMQ
  │                       │                    │                │
  ├──Every 5 minutes──────▶│                    │                │
  │  check_no_shows()     │                    │                │
  │                       │                    │                │
  │                       ├──Find reservations─▶│                │
  │                       │  WHERE status='confirmed'            │
  │                       │  AND time < NOW() - 30min            │
  │                       │                    │                │
  │                       │◀──Result───────────┤                │
  │                       │                    │                │
  │                       ├──For each:         │                │
  │                       │  UPDATE status     │                │
  │                       │  = 'no_show'       │                │
  │                       │                    │                │
  │                       ├──Publish event─────┼───────────────▶│
  │                       │  (no_show_detected)│                │
  │                       │                    │                │
  │                       ├──Send notification │                │
  │                       │  to restaurant     │                │
```

---

## 🚀 Масштабируемость

### Горизонтальное масштабирование

**API Servers (Stateless):**
```
Load Balancer
    │
    ├──▶ Django API #1 (2 CPU, 4GB RAM)
    ├──▶ Django API #2 (2 CPU, 4GB RAM)
    ├──▶ Django API #3 (2 CPU, 4GB RAM)
    └──▶ Django API #N ...
```

**Преимущества:**
- Добавление серверов при росте нагрузки
- Zero downtime deployment (rolling update)
- Fault tolerance (падение одного сервера не критично)

**Celery Workers (Background Tasks):**
```
RabbitMQ
    │
    ├──▶ Worker #1 (email tasks)
    ├──▶ Worker #2 (email tasks)
    ├──▶ Worker #3 (report tasks)
    └──▶ Worker #N ...
```

### Вертикальное масштабирование

**Database (Master-Slave Replication):**
```
┌──────────────────┐
│  PostgreSQL      │
│  Master          │◀───── Writes only
│  (8 CPU, 32GB)   │
└────────┬─────────┘
         │
    Replication
         │
    ┌────┴─────┬──────────┐
    │          │          │
┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│ Slave1 │ │ Slave2 │ │ Slave3 │◀── Reads
└────────┘ └────────┘ └────────┘
```

**Redis Cluster:**
```
┌────────────┐
│ Redis #1   │ (Shard 1: keys 0-5000)
└────────────┘
┌────────────┐
│ Redis #2   │ (Shard 2: keys 5001-10000)
└────────────┘
┌────────────┐
│ Redis #3   │ (Shard 3: keys 10001-15000)
└────────────┘
```

---

## ⚡ Производительность

### Целевые метрики

| Метрика | Целевое значение | Критическое |
|---------|------------------|-------------|
| Response Time (p50) | < 100ms | < 200ms |
| Response Time (p95) | < 500ms | < 1s |
| Response Time (p99) | < 1s | < 2s |
| Throughput | 10,000 req/s | 5,000 req/s |
| Error Rate | < 0.1% | < 1% |
| Availability | > 99.9% | > 99% |

### Оптимизации

**1. Database Query Optimization:**
```python
# ❌ Плохо (N+1 query problem)
restaurants = Restaurant.objects.all()
for r in restaurants:
    print(r.owner.email)  # Дополнительный запрос для каждого!

# ✅ Хорошо (1 query with JOIN)
restaurants = Restaurant.objects.select_related('owner').all()
for r in restaurants:
    print(r.owner.email)  # Уже загружено!
```

**2. Caching Strategy:**
```python
# Кэширование результатов тяжёлых запросов
def get_available_tables(restaurant_id, date, time_slot):
    cache_key = f"available:{restaurant_id}:{date}:{time_slot}"
    
    # Попытка получить из кэша
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    # Тяжёлый запрос к БД
    result = complex_database_query()
    
    # Сохранить в кэш на 1 минуту
    cache.set(cache_key, result, timeout=60)
    return result
```

**3. Database Connection Pooling:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Переиспользование соединений
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30s timeout
        }
    }
}
```

**4. Async Background Tasks:**
```python
# Не блокировать API response
@api_view(['POST'])
def create_reservation(request):
    reservation = Reservation.objects.create(...)
    
    # Асинхронная отправка email (не ждём)
    send_confirmation_email.delay(reservation.id)
    
    # Сразу возвращаем ответ
    return Response(status=201)
```

---

## 🔒 Безопасность

### Defense in Depth (многоуровневая защита)

**1. Network Level:**
- Firewall rules (только 80/443 порты открыты)
- DDoS protection (Cloudflare)
- VPN для доступа к БД

**2. Application Level:**
- JWT токены (короткое время жизни)
- Rate limiting (100 req/min per IP)
- Input validation (Django forms/serializers)
- SQL Injection защита (ORM)
- XSS защита (auto-escaping)

**3. Data Level:**
- Encrypted passwords (bcrypt/PBKDF2)
- Encrypted sensitive data at rest
- SSL/TLS for data in transit
- Regular backups (каждые 6 часов)

**4. Monitoring:**
- Failed login attempts tracking
- Suspicious activity alerts
- Audit logs для критических операций

### OWASP Top 10 Compliance

| Уязвимость | Защита |
|------------|--------|
| Injection | Django ORM, prepared statements |
| Broken Authentication | JWT, strong passwords, MFA ready |
| Sensitive Data Exposure | Encryption at rest & transit |
| XML External Entities | JSON only, no XML parsing |
| Broken Access Control | Role-based permissions on every endpoint |
| Security Misconfiguration | Hardened settings, security headers |
| XSS | Auto-escaping, Content Security Policy |
| Insecure Deserialization | Safe serializers (DRF) |
| Using Components with Known Vulnerabilities | Automated dependency scanning |
| Insufficient Logging | Structured logging всех операций |

---

## 📊 Мониторинг

### Метрики (Prometheus)

**Application Metrics:**
```python
# HTTP запросы
http_requests_total{method="POST", endpoint="/reservations", status="201"}
http_request_duration_seconds{endpoint="/restaurants"}

# Business Metrics
reservations_created_total
reservations_cancelled_total
no_show_rate_percentage
average_booking_lead_time_hours

# Database
database_queries_total
database_query_duration_seconds
database_connections_active
```

**Infrastructure Metrics:**
```
# CPU, Memory, Disk
node_cpu_usage_percent
node_memory_usage_bytes
node_disk_usage_percent

# Redis
redis_connected_clients
redis_used_memory_bytes
redis_keyspace_hits_total
redis_keyspace_misses_total

# Celery
celery_task_received_total
celery_task_succeeded_total
celery_task_failed_total
celery_task_runtime_seconds
```

### Дашборды (Grafana)

**1. System Health Dashboard:**
- Request rate (req/s)
- Error rate (%)
- Response time (p50, p95, p99)
- CPU/Memory usage

**2. Business Metrics Dashboard:**
- Бронирования за день
- No-show rate
- Популярные рестораны
- Peak hours

**3. Database Dashboard:**
- Query performance
- Slow queries (> 1s)
- Connection pool usage
- Cache hit rate

---

## 🚨 Обработка сбоев

### Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_external_geocoding_api(address):
    """
    Вызов внешнего API для геокодирования.
    Если 5 ошибок подряд → circuit открывается на 60 секунд
    """
    response = requests.get(f"https://maps.api/geocode?address={address}")
    response.raise_for_status()
    return response.json()

def geocode_restaurant_address(address):
    try:
        return call_external_geocoding_api(address)
    except CircuitBreakerError:
        # Fallback: использовать кэшированные координаты
        return get_cached_coordinates(address)
    except Exception:
        # Graceful degradation: продолжаем без геолокации
        return {"lat": None, "lon": None}
```

### Retry Strategy

```python
from celery import Task

class RetryableTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True  # Exponential backoff: 1s, 2s, 4s

@celery.task(base=RetryableTask)
def send_email(reservation_id):
    """
    Попытка отправить email с retry при временных сбоях
    """
    reservation = Reservation.objects.get(id=reservation_id)
    email_service.send(
        to=reservation.user.email,
        subject="Reservation Confirmation",
        body=render_template(reservation)
    )
```

---

## 🧪 Тестирование

### Test Pyramid

```
           ╱╲
          ╱  ╲
         ╱ E2E╲         < 10% (полные сценарии)
        ╱──────╲
       ╱        ╲
      ╱Integration      ~ 30% (API тесты)
     ╱────────────╲
    ╱              ╲
   ╱  Unit Tests    ╲  ~ 60% (логика, модели)
  ╱──────────────────╲
```

**Unit Tests:**
```python
def test_reservation_validation():
    """Тест валидации бронирования"""
    reservation = Reservation(
        date=timezone.now().date() - timedelta(days=1)  # Прошедшая дата
    )
    with pytest.raises(ValidationError):
        reservation.full_clean()
```

**Integration Tests:**
```python
def test_create_reservation_api(client, user_token):
    """Тест создания бронирования через API"""
    response = client.post('/api/reservations/', {
        'restaurant_id': 1,
        'date': '2025-12-20',
        'time_slot': '19:00',
        'guests_count': 4
    }, headers={'Authorization': f'Bearer {user_token}'})
    
    assert response.status_code == 201
    assert 'id' in response.json()
```

**Load Tests (Locust):**
```python
class ReservationUser(HttpUser):
    @task
    def create_reservation(self):
        self.client.post('/api/reservations/', json={...})
    
    @task(3)  # 3x чаще
    def search_restaurants(self):
        self.client.get('/api/restaurants/')
```

---

## 📈 Планы развития

### Phase 1 (Текущая) — MVP
- ✅ CRUD API
- ✅ JWT аутентификация
- ✅ Базовое кэширование
- ✅ Email уведомления

### Phase 2 — Производительность
- 🔄 Микросервисная архитектура
- 🔄 ElasticSearch для поиска
- 🔄 Prometheus + Grafana
- 🔄 Database replication

### Phase 3 — Advanced Features
- 📅 Онлайн-заказ еды
- 💳 Интеграция с платёжными системами
- 📱 Mobile push notifications
- 🗺️ Advanced геопоиск

### Phase 4 — ML/AI
- 🤖 Рекомендательная система
- 📊 Предсказание no-show
- ⏰ Оптимизация временных слотов
- 💡 Динамическое ценообразование

---

## 📚 Технические решения

### Почему PostgreSQL?

✅ **ACID транзакции** — критично для бронирований (конкуренция за столики)
✅ **Foreign keys & constraints** — целостность данных
✅ **Complex queries** — JOIN, агрегации для отчётов
✅ **JSON support** — гибкость для расширений (special_requests)
✅ **PostGIS** — геопространственные запросы
✅ **Mature & reliable** — проверено годами

### Почему Redis?

✅ **In-memory** — микросекундные latency
✅ **Pub/Sub** — real-time обновления
✅ **TTL support** — автоматическое истечение кэша
✅ **Data structures** — lists, sets, sorted sets
✅ **Session storage** — быстрое хранение сессий

### Почему Celery + RabbitMQ?

✅ **Distributed tasks** — масштабирование workers
✅ **Priority queues** — важные задачи первыми
✅ **Retry mechanism** — автоматические повторы
✅ **Monitoring** — Flower UI
✅ **Django integration** — нативная поддержка

---

## 🎓 Выводы

### Что было сложно:

1. **Race conditions** при конкурентных бронированиях → решение: database locks
2. **Cache invalidation** при изменении данных → решение: event-driven invalidation
3. **Idempotency** фоновых задач → решение: state tracking в БД
4. **Testing async tasks** → решение: eager mode в тестах

### Что было интересно:

1. Реализация Circuit Breaker pattern
2. Оптимизация database queries (N+1 проблема)
3. Настройка мониторинга и alert rules
4. Горизонтальное масштабирование API

### Навыки получены:

- ✅ Проектирование highload систем
- ✅ Работа с distributed systems
- ✅ Performance optimization
- ✅ Monitoring & observability
- ✅ Security best practices

---

**Документ последний раз обновлён: 19 октября 2025**
