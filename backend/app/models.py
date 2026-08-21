from pydantic import BaseModel, ConfigDict, Field


class CardOut(BaseModel):
    id: str
    title: str
    details: str


class ColumnOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    card_ids: list[str] = Field(alias="cardIds")


class BoardOut(BaseModel):
    columns: list[ColumnOut]
    cards: dict[str, CardOut]
