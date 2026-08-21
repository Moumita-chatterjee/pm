from app.ai.apply import apply_operations
from app.ai.schema import CreateCardOp, EditCardOp, MoveCardOp
from app.models import BoardOut, CardOut, ColumnOut


def _board() -> BoardOut:
    return BoardOut(
        columns=[
            ColumnOut(id="col-a", title="A", card_ids=["card-1"]),
            ColumnOut(id="col-b", title="B", card_ids=[]),
        ],
        cards={"card-1": CardOut(id="card-1", title="Existing", details="d")},
    )


def test_create_card_adds_a_new_card():
    board = _board()
    op = CreateCardOp(op="create_card", column_id="col-b", title="New", details="d2")

    result = apply_operations(board, [op])

    assert result is not None
    new_id = next(iter(set(result.cards) - set(board.cards)))
    assert result.cards[new_id].title == "New"
    assert result.cards[new_id].details == "d2"
    assert new_id in result.columns[1].card_ids


def test_create_card_invalid_column_id_is_noop():
    board = _board()
    op = CreateCardOp(op="create_card", column_id="col-missing", title="New", details="d")

    assert apply_operations(board, [op]) is None


def test_edit_card_updates_title_and_details():
    board = _board()
    op = EditCardOp(op="edit_card", card_id="card-1", title="Renamed", details="new details")

    result = apply_operations(board, [op])

    assert result is not None
    assert result.cards["card-1"].title == "Renamed"
    assert result.cards["card-1"].details == "new details"


def test_edit_card_invalid_card_id_is_noop():
    board = _board()
    op = EditCardOp(op="edit_card", card_id="card-missing", title="x", details="y")

    assert apply_operations(board, [op]) is None


def test_move_card_moves_between_columns():
    board = _board()
    op = MoveCardOp(op="move_card", card_id="card-1", column_id="col-b")

    result = apply_operations(board, [op])

    assert result is not None
    assert result.columns[0].card_ids == []
    assert result.columns[1].card_ids == ["card-1"]


def test_move_card_invalid_ids_is_noop():
    board = _board()
    op = MoveCardOp(op="move_card", card_id="card-missing", column_id="col-b")

    assert apply_operations(board, [op]) is None


def test_invalid_operation_makes_the_whole_batch_a_noop():
    board = _board()
    valid_op = CreateCardOp(op="create_card", column_id="col-b", title="New", details="d")
    invalid_op = EditCardOp(op="edit_card", card_id="card-missing", title="x", details="y")

    assert apply_operations(board, [valid_op, invalid_op]) is None
