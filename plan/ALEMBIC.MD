# Alembic — шпаргалка проекта

Alembic хранит историю изменений схемы PostgreSQL в файлах `alembic/versions/`. Миграция описывает переход схемы вперёд в `upgrade()` и обратный переход в `downgrade()`.

В этом проекте Alembic берёт строку подключения из `settings.database_url` в `alembic/env.py`. Значения для неё читаются из `.env`; пароль в `alembic.ini` не хранится.

## Перед началом

Все команды выполняются из корня репозитория, где лежат `pyproject.toml` и `alembic.ini`.

PostgreSQL должен быть запущен:

```bash
docker compose up -d apartment_db
docker compose ps
```

Проверить подключение к базе можно так:

```bash
docker compose exec apartment_db psql -U vladimir -d apartment
```

В интерактивной консоли PostgreSQL список таблиц выводит команда:

```sql
\dt
```

Для выхода используйте `\q`.

## Создание Alembic и первой миграции

Этот раздел нужен только один раз — когда в проекте ещё нет каталога `alembic/` и файла `alembic.ini`.

### 1. Инициализировать Alembic

```bash
uv run alembic init alembic
```

Команда создаёт:

```text
alembic/
├── env.py          # настройка подключения и metadata моделей
├── script.py.mako  # шаблон файлов миграций
└── versions/       # история миграций
alembic.ini         # техническая конфигурация Alembic
```

### 2. Подключить настройки и модели

В `alembic/env.py` нужно передать Alembic URL из единого источника настроек и metadata SQLAlchemy:

```python
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.models.account import Account

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

Импорт `Account` обязателен: он регистрирует таблицу в `Base.metadata`, и тогда Alembic увидит её при автогенерации.

### 3. Описать первую модель

Например, первая модель аккаунта в `backend/app/models/account.py` создаёт будущую таблицу `accounts`:

```python
class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### 4. Создать и применить первую миграцию

```bash
uv run alembic revision --autogenerate -m "create accounts table"
uv run alembic upgrade head
```

Первая команда создаёт файл миграции. Вторая выполняет его `upgrade()` и создаёт таблицы `accounts` и `alembic_version` в PostgreSQL.

Проверка:

```bash
docker compose exec apartment_db psql -U vladimir -d apartment -c '\dt'
uv run alembic current
```

## Обычный цикл последующих изменений схемы

```text
Изменить SQLAlchemy-модель
        ↓
Создать миграцию Alembic
        ↓
Проверить upgrade() и downgrade()
        ↓
Применить миграцию
        ↓
Проверить БД и состояние Alembic
```

### 1. Изменить модель

Например, после первой миграции добавьте поле отображаемого имени аккаунта в `backend/app/models/account.py`:

```python
name: Mapped[str] = mapped_column(String(100), nullable=False)
```

Чтобы автогенерация увидела модель, она должна быть импортирована в `alembic/env.py`. Сейчас там уже импортирован `Account`.

### 2. Создать следующую миграцию

```bash
uv run alembic revision --autogenerate -m "понятное описание изменения"
```

Примеры из проекта:

```bash
uv run alembic revision --autogenerate -m "create accounts table"
uv run alembic revision --autogenerate -m "add account name"
uv run alembic revision --autogenerate -m "increase account name length"
```

Команда создаёт новый файл в `alembic/versions/`. Она не изменяет таблицы в PostgreSQL.

### 3. Проверить сгенерированный файл

Откройте новую миграцию и прочитайте обе функции:

```python
def upgrade() -> None:
    # Применяет изменение схемы.
    ...

def downgrade() -> None:
    # Откатывает именно это изменение.
    ...
```

Пример добавления колонки:

```python
def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("name", sa.String(length=50), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("accounts", "name")
```

Пример изменения длины колонки:

```python
def upgrade() -> None:
    op.alter_column(
        "accounts",
        "name",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=100),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "accounts",
        "name",
        existing_type=sa.String(length=100),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
```

Автогенерация — только заготовка. Особенно внимательно проверяйте удаление таблиц, колонок и ограничений.

### 4. Применить миграции

```bash
uv run alembic upgrade head
```

`head` — последняя миграция в цепочке. Alembic применит только ещё не применённые миграции.

### 5. Проверить результат

Текущая версия базы:

```bash
uv run alembic current
```

Ожидаемый вид результата:

```text
bae062a837f9 (head)
```

Проверка, что модель и схема не требуют новой миграции:

```bash
uv run alembic check
```

Успешный результат:

```text
No new upgrade operations detected.
```

Проверка структуры конкретной таблицы:

```bash
docker compose exec apartment_db psql -U vladimir -d apartment -c '\d+ accounts'
```

В результате для имени аккаунта должно быть:

```text
name | character varying(100) | ... | not null
```

## История и откат

Посмотреть все миграции:

```bash
uv run alembic history
```

Откатить одну последнюю миграцию:

```bash
uv run alembic downgrade -1
```

Вернуть её обратно:

```bash
uv run alembic upgrade head
```

Перед откатом на рабочей базе проверьте `downgrade()`: он может удалить колонку и её данные.

## Важные правила

- Не переписывайте уже применённые миграции, включая первую `create accounts table`.
- Для каждого нового изменения схемы создавайте новый файл миграции.
- Не добавляйте `.env` в Git; он содержит секреты. Добавляйте `alembic/`, `alembic.ini` и файлы из `alembic/versions/`.
- Если в таблице уже есть строки, добавление `NOT NULL`-колонки без значения может завершиться ошибкой. Безопасный путь: добавить временно nullable-колонку → заполнить существующие строки → отдельной миграцией сделать `NOT NULL`.
- Перед коммитом запускайте `uv run alembic check` и просматривайте `git diff` новой миграции.
