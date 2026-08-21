"""Versioned, renderer-neutral exam paper model."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PageMargins(StrictModel):
    top_mm: float = Field(default=15, ge=5, le=40)
    bottom_mm: float = Field(default=15, ge=5, le=40)
    left_mm: float = Field(default=15, ge=5, le=40)
    right_mm: float = Field(default=15, ge=5, le=40)


class Layout(StrictModel):
    columns: Literal[1, 2] = 2
    column_gap_mm: float = Field(default=6, ge=2, le=20)
    margins: PageMargins = Field(default_factory=PageMargins)
    max_lines_per_column: int = Field(default=52, ge=20, le=100)


class Asset(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    path: str = Field(min_length=1, max_length=240)
    alt: str = Field(min_length=1, max_length=240)
    width_mm: float = Field(default=55, gt=0, le=90)


class SupportBox(StrictModel):
    label: str = Field(default="<보기>", min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=4000)


class PassageBlock(StrictModel):
    type: Literal["passage"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    label: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=20000)
    question_ids: list[str] = Field(min_length=1)


class QuestionBlock(StrictModel):
    type: Literal["question"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    number: PositiveInt
    stem: str = Field(min_length=1, max_length=4000)
    choices: list[str] = Field(min_length=2, max_length=5)
    points: int | None = Field(default=None, ge=0, le=100)
    boxes: list[SupportBox] = Field(default_factory=list, max_length=4)
    image_ids: list[str] = Field(default_factory=list, max_length=4)
    keep_together: bool = True


ExamBlock = Annotated[PassageBlock | QuestionBlock, Field(discriminator="type")]


class ExamPaper(StrictModel):
    schema_version: Literal["exam-hwpx-kit/v1"]
    title: str = Field(min_length=1, max_length=200)
    layout: Layout = Field(default_factory=Layout)
    assets: list[Asset] = Field(default_factory=list)
    blocks: list[ExamBlock] = Field(min_length=1)

    @property
    def questions(self) -> list[QuestionBlock]:
        return [block for block in self.blocks if isinstance(block, QuestionBlock)]

    @property
    def passages(self) -> list[PassageBlock]:
        return [block for block in self.blocks if isinstance(block, PassageBlock)]
