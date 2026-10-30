from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class VarRef(BaseModel):
    var: str = Field(description="Имя переменной состояния.")


class EqExpr(BaseModel):
    eq: tuple[Expression, Any] = Field(
        description="Проверка равенства: [выражение, литерал или значение]."
    )


class InExpr(BaseModel):
    in_: tuple[Expression, list[Any]] = Field(
        alias="in",
        description="Проверка принадлежности значения конечному множеству.",
    )


class AndExpr(BaseModel):
    and_: list[Expression] = Field(
        alias="and", description="Конъюнкция подвыражений."
    )


class OrExpr(BaseModel):
    or_: list[Expression] = Field(
        alias="or", description="Дизъюнкция подвыражений."
    )


class NotExpr(BaseModel):
    not_: Expression = Field(alias="not", description="Отрицание подвыражения.")


Expression = VarRef | EqExpr | InExpr | AndExpr | OrExpr | NotExpr

for _cls in (VarRef, EqExpr, InExpr, AndExpr, OrExpr, NotExpr):
    _cls.model_rebuild(force=True)


class Variable(BaseModel):
    name: str = Field(description="Уникальное имя переменной состояния.")
    type: Literal["enum", "boolean", "integer"] = Field(
        description="Тип переменной: enum | boolean | integer."
    )
    values: list[str] | None = Field(
        default=None,
        description="Допустимые значения для type=enum. Для boolean/integer не заполняется.",
    )
    min: int | None = Field(default=None, description="Минимум для type=integer.")
    max: int | None = Field(default=None, description="Максимум для type=integer.")


class Effect(BaseModel):
    set_: tuple[str, Any] = Field(
        alias="set",
        description="Присваивание: [имя_переменной, новое_значение].",
    )


class Transition(BaseModel):
    name: str = Field(description="Уникальное имя перехода.")
    guard: Expression = Field(description="Условие, при котором переход разрешён.")
    effects: list[Effect] = Field(
        description="Изменения состояния при срабатывании перехода."
    )
    related_requirements: list[str] = Field(
        default_factory=list,
        description="Ссылки на исходные требования, из которых выведен переход.",
    )


class Property(BaseModel):
    id: str = Field(description="Уникальный идентификатор свойства, например 'P1'.")
    type: Literal["invariant", "forbidden_state", "reachable", "deadlock_free"] = Field(
        description="Тип проверяемого свойства."
    )
    expression: Expression | None = Field(
        default=None,
        description="Выражение свойства. Не заполняется для type=deadlock_free.",
    )
    description: str | None = Field(
        default=None,
        description="Пояснение свойства на языке исходных требований.",
    )
    related_requirements: list[str] = Field(
        default_factory=list,
        description="Ссылки на исходные требования.",
    )


class BehavioralModel(BaseModel):
    analysis_object: str = Field(
        description="Что именно анализируется (объект, процесс, модуль)."
    )
    variables: list[Variable] = Field(
        description="Переменные, формирующие состояние системы."
    )
    initial: dict[str, Any] = Field(
        description="Начальные значения переменных: {имя: значение}."
    )
    transitions: list[Transition] = Field(description="Список допустимых переходов.")
    properties: list[Property] = Field(
        description="Свойства, которые нужно проверить."
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Допущения, принятые агентом при интерпретации требований.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Уточняющие вопросы пользователю, если требования неоднозначны.",
    )