"""
src/validators.py

Перевірки консистентності даних між DataFrames.

Виконуються після трансформацій, перед завантаженням у БД.
Якщо є порушення — або видаляємо проблемні рядки (м'який режим),
або зупиняємо пайплайн з помилкою (суворий режим).
"""

import pandas as pd

__all__ = [
    "validate_fk",
    "validate_not_null",
    "validate_unique",
    "validate_score_range",
]


def validate_fk(
    child_df: pd.DataFrame,
    child_fk_col: str,
    parent_df: pd.DataFrame,
    parent_pk_col: str,
    child_name: str = "child",
    parent_name: str = "parent",
    drop_orphans: bool = True,
) -> pd.DataFrame:
    """
    Перевіряє referential integrity: всі значення child_df[child_fk_col]
    мають існувати в parent_df[parent_pk_col].

    Сироти (orphans) — рядки в дочірній таблиці, FK яких не знайдено
    в батьківській. PostgreSQL відхилить їх при INSERT з FK-constraint.

    Args:
        child_df:     дочірній DataFrame (наприклад orders).
        child_fk_col: назва FK-колонки в child (наприклад "customer_id").
        parent_df:    батьківський DataFrame (наприклад customers).
        parent_pk_col: назва PK-колонки в parent (наприклад "customer_id").
        child_name:   ім'я для логів.
        parent_name:  ім'я для логів.
        drop_orphans: True  → видалити сиріт (м'який режим, рекомендовано).
                      False → зупинити пайплайн з ValueError (суворий режим).

    Returns:
        child_df без сиріт (або оригінал якщо сиріт не було).

    Raises:
        ValueError: якщо drop_orphans=False і знайдено сиріт.
    """
    # Крок 1: спочатку прибираємо рядки з NULL у FK-колонці —
    # вони не є «сиротами», вони просто порожні, і це окрема проблема.
    fk_nulls = child_df[child_fk_col].isna().sum()
    if fk_nulls > 0:
        print(f"  ⚠ [{child_name}] {fk_nulls} рядків з NULL у {child_fk_col}")
        child_df = child_df[child_df[child_fk_col].notna()].copy()

    # Крок 2: тепер перевіряємо сиріт (NaN вже немає)
    valid_parent_ids = set(parent_df[parent_pk_col].dropna())
    orphan_mask = ~child_df[child_fk_col].isin(valid_parent_ids)
    orphan_count = orphan_mask.sum()

    if orphan_count > 0:
        print(
            f"  ⚠ [{child_name}] {orphan_count} сиріт по {child_fk_col} "
            f"(не знайдено в {parent_name}.{parent_pk_col})"
        )
        # Показуємо приклади — корисно для дебагу
        examples = child_df.loc[orphan_mask, child_fk_col].value_counts().head(3)
        print(f"    Приклади: {examples.to_dict()}")

        if drop_orphans:
            child_df = child_df[~orphan_mask].copy()
            print(f"    ✓ Видалено {orphan_count} сиріт")
        else:
            raise ValueError(
                f"[{child_name}] {orphan_count} сиріт по {child_fk_col}. "
                f"Перевір дані або встанови drop_orphans=True."
            )
    else:
        print(f"  ✓ [{child_name}] → [{parent_name}]: усі {child_fk_col} валідні")

    return child_df


def validate_not_null(
    df: pd.DataFrame,
    columns: list[str],
    name: str = "df",
) -> None:
    """
    Перевіряє відсутність NaN у вказаних колонках.
    Відповідає NOT NULL constraint у DDL схемі БД.

    Args:
        df:      DataFrame для перевірки.
        columns: список колонок які мають бути NOT NULL.
        name:    ім'я таблиці для логів.

    Raises:
        ValueError: якщо знайдено NULL у будь-якій з колонок.
    """
    for col in columns:
        nulls = df[col].isna().sum()
        if nulls > 0:
            raise ValueError(
                f"[{name}] Колонка '{col}' містить {nulls} NULL — "
                f"порушення NOT NULL constraint у БД!"
            )
    print(f"  ✓ [{name}] NOT NULL {columns} — ОК")


def validate_unique(
    df: pd.DataFrame,
    columns: list[str],
    name: str = "df",
) -> None:
    """
    Перевіряє унікальність вказаних колонок.
    Відповідає PRIMARY KEY або UNIQUE constraint у DDL схемі БД.

    Args:
        df:      DataFrame для перевірки.
        columns: список колонок що утворюють PK або composite PK.
        name:    ім'я таблиці для логів.

    Raises:
        ValueError: якщо знайдено дублікати.
    """
    duplicates = df.duplicated(subset=columns).sum()
    if duplicates > 0:
        raise ValueError(
            f"[{name}] Знайдено {duplicates} дублів по {columns} — "
            f"порушення PRIMARY KEY constraint у БД!"
        )
    print(f"  ✓ [{name}] UNIQUE {columns} — ОК")


def validate_score_range(
    df: pd.DataFrame,
    col: str,
    low: int,
    high: int,
    name: str,
) -> None:
    """
    Перевіряє що числова колонка містить тільки значення в діапазоні [low, high].
    Використовується для review_score: має бути тільки 1, 2, 3, 4 або 5.

    Args:
        df:   DataFrame для перевірки.
        col:  назва числової колонки.
        low:  мінімальне допустиме значення (включно).
        high: максимальне допустиме значення (включно).
        name: ім'я таблиці для логів.

    Raises:
        ValueError: якщо знайдено значення поза діапазоном.
    """
    out_of_range = (~df[col].between(low, high)).sum()
    if out_of_range > 0:
        raise ValueError(
            f"[{name}] Колонка '{col}': {out_of_range} значень поза [{low}, {high}]!"
        )
    print(f"  ✓ [{name}] {col} ∈ [{low}, {high}] — ОК")
