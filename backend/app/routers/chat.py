from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ai.apply import apply_operations
from app.ai.openrouter import call_openrouter
from app.ai.schema import ChatAIResponse, build_chat_response_format
from app.auth import get_current_user
from app.db import get_or_create_board, load_board, save_board
from app.models import BoardOut

router = APIRouter()

SYSTEM_PROMPT = (
    "You are the AI assistant for a single-board Kanban app. You are given "
    "the current board as JSON (fixed columns with ids/titles, cards keyed "
    "by id) and a user message. The user refers to columns and cards by "
    "their human-readable title, never by id — you must look up the "
    "matching column_id/card_id yourself from the board JSON below before "
    "writing an operation; never ask the user for an id, and never invent "
    "one that isn't in the board JSON. Reply conversationally in `reply`, "
    "and express any board changes as `operations`, each one of: "
    "create_card {op, column_id, title, details}; "
    "edit_card {op, card_id, title, details} (title/details are the card's "
    "full new values, not a diff); "
    "move_card {op, card_id, column_id} (moves the card to the end of that "
    "column). "
    "If no board change is needed, return operations: []."
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponseOut(BaseModel):
    reply: str
    board: BoardOut


@router.post("/chat", response_model=ChatResponseOut)
def chat(body: ChatRequest, user: dict = Depends(get_current_user)):
    board_id = get_or_create_board(user["id"])
    board = load_board(board_id)

    column_lookup = "\n".join(
        f"- {column.title!r} -> column_id {column.id!r}" for column in board.columns
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Columns on the board (title -> column_id):\n{column_lookup}\n\n"
                f"Full board state (JSON): {board.model_dump_json(by_alias=True)}"
            ),
        },
        *[{"role": m.role, "content": m.content} for m in body.history],
        {"role": "user", "content": body.message},
    ]

    response_format = build_chat_response_format(
        column_ids=[column.id for column in board.columns],
        card_ids=list(board.cards.keys()),
    )
    raw_reply = call_openrouter(messages, response_format=response_format)
    ai_response = ChatAIResponse.model_validate_json(raw_reply)

    updated_board = apply_operations(board, ai_response.operations)
    if updated_board is not None:
        save_board(board_id, updated_board)
        board = updated_board

    return ChatResponseOut(reply=ai_response.reply, board=board)
