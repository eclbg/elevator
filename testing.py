from dataclasses import dataclass
from typing import Literal, Any

from elevator import ElevatorEvent, Elevator
from modes import IDLE, MOVING, LOADING


floors = range(Elevator.BOTTOM_FLOOR, Elevator.TOP_FLOOR + 1)
directions = ["UP", "DOWN"]
possible_events = []

# Let's start with the events that can happen regardless of the elevator state: button presses

button_presses = []
for floor in floors:
    button_presses.append(
        ElevatorEvent(kind="ONBOARD_PANEL_BUTTON_PRESS", payload={"floor": floor})
    )
for direction in directions:
    for floor in floors:
        button_presses.append(
            ElevatorEvent(
                kind="HALLWAY_BUTTON_PRESS",
                payload={"floor": floor, "direction": direction},
            )
        )


@dataclass
class Condition:
    attr_name: Literal["mode", "direction", "current_floor"]
    value: Any

    def elevator_meets_condition(self, elevator: Elevator):
        return getattr(elevator, self.attr_name) == self.value


# Let's use a list of tuples: (ElevatorEvent, List[conditions])
conditional_events = []

# The events below can only happen when the elevator is on some states

# # These ones can only happen when the elevator is moving towards a floor
kind = "FLOOR_SENSOR"
for floor in floors:
    for direction in directions:
        curr_floor_value = floor + 1 if direction == "DOWN" else floor - 1
        if not Elevator.BOTTOM_FLOOR <= curr_floor_value <= Elevator.TOP_FLOOR:
            continue
        conditions = [
            Condition(attr_name="mode", value=MOVING),
            Condition(attr_name="direction", value=direction),
            Condition(attr_name="current_floor", value=curr_floor_value),
        ]
        conditional_events.append(
            (ElevatorEvent(kind=kind, payload={"floor": floor}), conditions)
        )
#
# # This one can only happen when the elevator is loading
# loading_complete_event = ElevatorEvent(kind="LOADING_COMPLETE")
