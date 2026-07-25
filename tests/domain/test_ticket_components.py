from src.domain.ticket_components import Comment


def test_comment_keeps_employee_and_text():
    comment = Comment(employee_id=1, comment="hello")

    assert comment.employee_id == 1
    assert comment.comment == "hello"
    assert comment.comment_id == 0


