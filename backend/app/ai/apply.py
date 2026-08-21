import secrets

from app.ai.schema import CreateCardOp, EditCardOp, MoveCardOp, Operation
from app.models import BoardOut, CardOut, ColumnOut


def apply_operations(board: BoardOut, operations: list[Operation]) -> BoardOut | None:
    column_ids = {column.id for column in board.columns}
    card_ids = set(board.cards.keys())

    for op in operations:
        if isinstance(op, CreateCardOp) and op.column_id not in column_ids:
            return None
        if isinstance(op, EditCardOp) and op.card_id not in card_ids:
            return None
        if isinstance(op, MoveCardOp) and (
            op.card_id not in card_ids or op.column_id not in column_ids
        ):
            return None

    card_ids_by_column = {
        column.id: list(column.card_ids) for column in board.columns
    }
    cards = dict(board.cards)

    for op in operations:
        if isinstance(op, CreateCardOp):
            new_id = f"card-{secrets.token_hex(6)}"
            cards[new_id] = CardOut(id=new_id, title=op.title, details=op.details)
            card_ids_by_column[op.column_id].append(new_id)
        elif isinstance(op, EditCardOp):
            cards[op.card_id] = CardOut(
                id=op.card_id, title=op.title, details=op.details
            )
        elif isinstance(op, MoveCardOp):
            for ids in card_ids_by_column.values():
                if op.card_id in ids:
                    ids.remove(op.card_id)
            card_ids_by_column[op.column_id].append(op.card_id)

    columns = [
        ColumnOut(
            id=column.id, title=column.title, card_ids=card_ids_by_column[column.id]
        )
        for column in board.columns
    ]
    return BoardOut(columns=columns, cards=cards)
