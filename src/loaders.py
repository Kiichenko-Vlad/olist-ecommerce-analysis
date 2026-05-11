"""
src/loaders.py

Запис DataFrames у PostgreSQL через UPSERT.

Чому UPSERT, а не to_sql(if_exists='replace')?
- 'replace' виконує DROP TABLE → знищує всі FK-обмеження!
- 'append' падає на дублях при повторному запуску.
- UPSERT через тимчасову таблицю: зберігає структуру БД і FK,
  оновлює існуючі рядки, додає нові, ігнорує незмінені.
"""

import pandas as pd
from sqlalchemy import Engine, text

__all__ = [
    "upsert",
    "verify_counts",
]


def upsert(
    df: pd.DataFrame,
    table: str,
    key_columns: list[str],
    engine: Engine,
    schema: str = "public",
    chunksize: int = 1000,
) -> None:
    """
    Ідемпотентний UPSERT через тимчасову таблицю.

    Алгоритм:
        1. df → тимчасова таблиця _tmp_<table> (звичайний to_sql, FK немає)
        2. INSERT INTO <table> ... SELECT FROM _tmp_<table>
           ON CONFLICT (<key_columns>) DO UPDATE SET ...
           WHERE <field> IS DISTINCT FROM EXCLUDED.<field>
        3. DROP TABLE _tmp_<table>

    IS DISTINCT FROM — на відміну від <>, коректно порівнює NULL:
        NULL <> NULL → NULL (не True!) — оновлення не спрацює
        NULL IS DISTINCT FROM NULL → False — оновлення не відбудеться (правильно)

    Args:
        df:          DataFrame для запису.
        table:       назва цільової таблиці в БД.
        key_columns: колонки що утворюють PK (для ON CONFLICT).
        engine:      SQLAlchemy engine з get_engine().
        schema:      схема БД (default: public).
        chunksize:   розмір батчу для INSERT у тимчасову таблицю.
    """
    if len(df) == 0:
        print(f"  ⚠ [{table}] DataFrame порожній, пропускаю")
        return

    temp_table = f"_tmp_{table}"
    all_columns = list(df.columns)
    update_columns = [c for c in all_columns if c not in key_columns]

    cols_str = ", ".join(f'"{c}"' for c in all_columns)
    keys_str = ", ".join(f'"{c}"' for c in key_columns)

    if update_columns:
        update_str = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_columns)
        where_str = " OR ".join(
            f'"{schema}"."{table}"."{c}" IS DISTINCT FROM EXCLUDED."{c}"'
            for c in update_columns
        )
        conflict_action = f"DO UPDATE SET {update_str} WHERE {where_str}"
    else:
        conflict_action = "DO NOTHING"

    with engine.begin() as conn:
        # Крок 1: записуємо в тимчасову таблицю
        df.to_sql(
            name=temp_table,
            con=conn,
            schema=schema,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=chunksize,
        )

        # Крок 2: UPSERT з тимчасової в цільову
        sql = f"""
            INSERT INTO "{schema}"."{table}" ({cols_str})
            SELECT {cols_str} FROM "{schema}"."{temp_table}"
            ON CONFLICT ({keys_str}) {conflict_action};
        """
        result = conn.execute(text(sql))
        print(f"  ✓ [{table}] Записано/оновлено: {result.rowcount:,} рядків")

        # Крок 3: прибираємо тимчасову таблицю
        conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{temp_table}";'))


def verify_counts(
    expected: dict[str, int],
    engine: Engine,
    schema: str = "public",
) -> None:
    """
    Верифікація після завантаження: порівнює COUNT(*) у БД
    з очікуваною кількістю рядків (len(df) після трансформацій).

    Args:
        expected: словник {назва_таблиці: очікувана_кількість}.
                  Наприклад: {"customers": 99441, "orders": 99441}
        engine:   SQLAlchemy engine.
        schema:   схема БД.
    """
    print("\n=== ВЕРИФІКАЦІЯ: COUNT(*) у БД ===")
    all_ok = True

    with engine.connect() as conn:
        for table_name, expected_count in expected.items():
            result = conn.execute(
                text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
            )
            actual_count = result.scalar()
            ok = actual_count == expected_count
            status = "✓" if ok else "✗"
            if not ok:
                all_ok = False
            print(
                f"  {status} {table_name:20s}: "
                f"БД={actual_count:>7,} | очікувано={expected_count:>7,}"
            )

    if all_ok:
        print("  ✓ Усі таблиці: кількість рядків відповідає очікуваному")
    else:
        print("  ✗ Є розбіжності! Перевір логи трансформацій.")
