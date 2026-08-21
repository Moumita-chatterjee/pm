from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.db import get_or_create_board, load_board, save_board
from app.models import BoardOut

router = APIRouter()


@router.get("/board", response_model=BoardOut)
def get_board(user: dict = Depends(get_current_user)):
    board_id = get_or_create_board(user["id"])
    return load_board(board_id)


@router.put("/board", response_model=BoardOut)
def put_board(body: BoardOut, user: dict = Depends(get_current_user)):
    board_id = get_or_create_board(user["id"])
    current = load_board(board_id)

    existing_column_ids = {column.id for column in current.columns}
    payload_column_ids = {column.id for column in body.columns}
    if payload_column_ids != existing_column_ids:
        raise HTTPException(status_code=400, detail="Unknown or missing column id")

    referenced_card_ids = {
        card_id for column in body.columns for card_id in column.card_ids
    }
    if referenced_card_ids != set(body.cards.keys()):
        raise HTTPException(
            status_code=400, detail="cardIds and cards are out of sync"
        )

    save_board(board_id, body)
    return load_board(board_id)
