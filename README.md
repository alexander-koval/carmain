# Carmain - Система управления техническим обслуживанием автомобилей

<div align="center">
  <img src="carmain/static/img/demo.gif" alt="Demo" />
</div>

Carmain - веб-приложение для управления техническим обслуживанием автомобилей. Отслеживайте историю проведенных работ, получайте напоминания о запланированных процедурах и никогда не забывайте о важном обслуживании.

## Основные возможности

**Управление автомобилями**
- Регистрация неограниченного количества автомобилей
- Хранение информации: марка, модель, год выпуска, текущий пробег
- Персональный гараж для каждого пользователя

**Планирование технического обслуживания**
- Готовый каталог типовых работ (замена масла, фильтров, тормозных колодок и др.)
- Настраиваемые интервалы обслуживания для каждого автомобиля
- Отслеживание последней даты и пробега выполнения работ

**Ведение истории обслуживания**
- Полный журнал выполненных работ с возможностью редактирования
- Запись даты обслуживания, пробега и комментариев
- Удобный поиск и фильтрация записей

**Умные напоминания**
- Автоматическое определение просроченного обслуживания
- Цветовые индикаторы статуса (просрочено, скоро требуется, выполнено)
- Приоритизация наиболее срочных работ

## Технологии

- **Backend**: FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: HTMX, Bootstrap 5, Alpine.js, Jinja2
- **Architecture**: Clean Architecture (Repository + Service layers)
- **Authentication**: Cookie-based sessions
- **Deploy**: Docker, Gunicorn, Nginx

## Быстрый старт

### Установка для разработки

```bash
# Клонирование репозитория
git clone https://github.com/alexander-koval/carmain.git
cd carmain

# Установка зависимостей
poetry install

# Настройка окружения
cp .env.example .env
# Отредактируйте .env с настройками базы данных

# Запуск базы данных
make dev

# В отдельном терминале - выполнение миграций
poetry run alembic upgrade head

# Запуск приложения
poetry run uvicorn carmain.main:carmain --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: `http://localhost:8000`

### Продакшн развертывание

```bash
# Запуск продакшн-версии
make build-prod && make up-prod
```

## Команды разработки

```bash
make help           # Показать все доступные команды
make dev           # Запустить среду разработки
make prod          # Запустить продакшн среду
make logs          # Показать логи
make backup-db     # Создать бэкап базы данных
make clean         # Очистить контейнеры
```

## Настройка окружения

Основные переменные в `.env`:

```env
# Application settings
APP_NAME=Car Maintenance
ADMIN_EMAIL=admin@yourdomain.com
SECRET_KEY=your-super-secret-key-here-generate-with-openssl-rand-hex-32

# Database settings (for development with localhost)
DB_NAME=carmain
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=carmain
POSTGRES_PASSWORD=your-strong-password-here
```

## Лицензия

Распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).
