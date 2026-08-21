from typing import Annotated, Literal

from pydantic import BaseModel, Field


class CreateCardOp(BaseModel):
    op: Literal["create_card"]
    column_id: str
    title: str
    details: str


class EditCardOp(BaseModel):
    op: Literal["edit_card"]
    card_id: str
    title: str
    details: str


class MoveCardOp(BaseModel):
    op: Literal["move_card"]
    card_id: str
    column_id: str


Operation = Annotated[
    CreateCardOp | EditCardOp | MoveCardOp, Field(discriminator="op")
]


class ChatAIResponse(BaseModel):
    reply: str
    operations: list[Operation]


# Hand-written strict-mode JSON schema for the outbound OpenRouter request.
# Pydantic's auto-generated schema doesn't satisfy strict-mode constraints
# (every object needs additionalProperties: false and a fully-required
# property list) out of the box, so this is maintained by hand and verified
# against ChatAIResponse via model_validate_json on the actual response.
#
# column_id/card_id are constrained with a JSON Schema `enum` of the ids
# actually on the board, rather than left as free-form strings. Without
# this, the model would sometimes emit a plausible-looking but wrong id
# (e.g. "backlog" instead of "col-backlog") that apply_operations then
# silently rejects as a no-op — while its own `reply` text still claims
# success, so the user sees a false "done!". enum eliminates that failure
# mode at the source; apply_operations' validation stays as defense in depth.
def build_chat_response_format(column_ids: list[str], card_ids: list[str]) -> dict:
    create_card_schema = {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": ["create_card"]},
            "column_id": {"type": "string", "enum": column_ids},
            "title": {"type": "string"},
            "details": {"type": "string"},
        },
        "required": ["op", "column_id", "title", "details"],
        "additionalProperties": False,
    }

    edit_card_schema = {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": ["edit_card"]},
            "card_id": {"type": "string", "enum": card_ids},
            "title": {"type": "string"},
            "details": {"type": "string"},
        },
        "required": ["op", "card_id", "title", "details"],
        "additionalProperties": False,
    }

    move_card_schema = {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": ["move_card"]},
            "card_id": {"type": "string", "enum": card_ids},
            "column_id": {"type": "string", "enum": column_ids},
        },
        "required": ["op", "card_id", "column_id"],
        "additionalProperties": False,
    }

    operation_schemas = [create_card_schema]
    # edit_card/move_card need at least one valid card_id to reference —
    # an empty enum makes those branches unsatisfiable, so drop them
    # entirely when the board has no cards yet rather than emit a
    # branch the model can never legally use.
    if card_ids:
        operation_schemas += [edit_card_schema, move_card_schema]

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "chat_ai_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "reply": {"type": "string"},
                    "operations": {
                        "type": "array",
                        "items": {"anyOf": operation_schemas},
                    },
                },
                "required": ["reply", "operations"],
                "additionalProperties": False,
            },
        },
    }
