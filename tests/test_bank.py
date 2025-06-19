from board import catanBoard


def test_bank_withdraw_deposit():
    board = catanBoard()
    assert board.withdraw_resource('ORE', 1) is True
    assert board.resourceBank['ORE'] == 18
    assert board.withdraw_resource('ORE', 100) is False
    board.deposit_resource('ORE', 2)
    assert board.resourceBank['ORE'] == 20
