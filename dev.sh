#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PG_CONTAINER="${PG_CONTAINER:-postgres-17}"
PG_DB="${PG_DB:-docmind}"

get_pg_user() {
  docker exec "$PG_CONTAINER" sh -c 'echo "${POSTGRES_USER:-postgres}"' 2>/dev/null || echo "postgres"
}

cmd="${1:-help}"

case "$cmd" in
  init-db)
    echo ">>> [1/4] Khởi động container $PG_CONTAINER..."
    docker start "$PG_CONTAINER"
    PG_USER="${PG_USER:-$(get_pg_user)}"
    echo ">>> Sử dụng Postgres user: $PG_USER"

    echo ">>> [2/4] Kiểm tra file cài đặt pgvector trong container..."
    docker exec -u root "$PG_CONTAINER" sh -c '
      if [ -f /usr/local/share/postgresql/extension/vector.control ] || [ -f /usr/share/postgresql/17/extension/vector.control ]; then
        echo "Đã có sẵn pgvector trong container."
      else
        echo "Chưa có pgvector, tiến hành cài đặt (chỉ tốn 1 lần đầu tiên)..."
        apk add --no-cache --virtual .build-deps git build-base &&
        rm -rf /tmp/pgvector &&
        git clone --depth 1 --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector &&
        make -C /tmp/pgvector with_llvm=no OPTFLAGS="" &&
        make -C /tmp/pgvector with_llvm=no install &&
        rm -rf /tmp/pgvector &&
        apk del .build-deps
      fi
    '

    echo ">>> [3/4] Tạo database '$PG_DB' (nếu chưa có)..."
    docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$PG_DB'" 2>/dev/null | grep -q 1 \
      || docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$PG_DB'" | grep -q 1 \
      || docker exec -i "$PG_CONTAINER" createdb -U "$PG_USER" "$PG_DB"

    echo ">>> [4/4] Chạy script infra/db/init.sql trên database '$PG_DB'..."
    docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" < infra/db/init.sql
    echo ">>> Hoàn tất init-db!"
    ;;
  up)
    docker compose up -d --build
    ;;
  down)
    docker compose down
    ;;
  logs)
    docker compose logs -f api
    ;;
  test)
    docker compose run --rm api pytest -q
    ;;
  lint)
    docker compose run --rm api ruff check .
    ;;
  fmt)
    docker compose run --rm api ruff format .
    ;;
  psql)
    PG_USER="${PG_USER:-$(get_pg_user)}"
    docker exec -it "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB"
    ;;
  migrate)
    docker compose run --rm api alembic upgrade head
    ;;
  *)
    echo "Cách dùng: ./dev.sh {init-db|up|down|logs|test|lint|fmt|psql|migrate}"
    exit 1
    ;;
esac
