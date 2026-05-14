from src.domain.ticket_components import Comment, ExecutorAssignment


def test_comment_keeps_employee_and_text():
    comment = Comment(employee_id=1, comment="hello")

    assert comment.employee_id == 1
    assert comment.comment == "hello"
    assert comment.comment_id == 0


def test_executor_assignment_keeps_actor_and_executor():
    assignment = ExecutorAssignment(admin_id=1, executor_id=2)

    assert assignment.admin_id == 1
    assert assignment.executor_id == 2
