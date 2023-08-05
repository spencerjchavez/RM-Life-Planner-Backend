from models.Action import Action

PARTIAL_ACTION = Action(
  successful=Action.Success.PARTIAL,
  howMuchAccomplished=1,
  notes="did not finish, but completed 1"
)
UNSUCCESSFUL_ACTION = Action(
    successful=Action.Success.UNSUCCESSFUL
)
SUCCESSFUL_ACTION_1 = Action(
  successful=Action.Success.SUCCESSFUL,
  howMuchAccomplished=1,
  notes="so good"
)
SUCCESSFUL_ACTION_10 = Action(
  successful=Action.Success.SUCCESSFUL,
  howMuchAccomplished=10,
  notes="so good"
)
