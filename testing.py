from itertools import product
import copy
from dataclasses import dataclass
from typing import Literal, Any

from elevator import ElevatorEvent, Elevator, ElevatorState
from modes import IDLE, MOVING, LOADING


floors = range(Elevator.BOTTOM_FLOOR, Elevator.TOP_FLOOR + 1)
directions = ["UP", "DOWN"]
#
# # This one can only happen when the elevator is loading
# loading_complete_event = ElevatorEvent(kind="LOADING_COMPLETE")


def get_possible_events(state: ElevatorState) -> list[ElevatorEvent]:
    possible_events = []

    # Let's start with the events that can happen regardless of the elevator state: button presses
    button_presses = []
    for dest in floors:
        payload = {"dest": dest}
        button_presses.append(
            ElevatorEvent(kind="ONBOARD_PANEL_BUTTON_PRESS", payload=payload)
        )
    for direction, floor in product(directions, floors):
        if floor == 1 and direction == "DOWN":
            continue
        if floor == 5 and direction == "UP":
            continue
        button_presses.append(
            ElevatorEvent(
                kind="HALLWAY_BUTTON_PRESS",
                payload={"floor": floor, "direction": direction},
            )
        )
    possible_events.extend(button_presses)

    if state.mode == "IDLE":
        pass
    elif state.mode == "LOADING":
        possible_events.append(ElevatorEvent(kind="LOADING_COMPLETE"))
    elif state.mode == "MOVING":
        if state.direction == "UP":
            payload = {"floor": state.current_floor + 1}
        if state.direction == "DOWN":
            payload = {"floor": state.current_floor - 1}
        possible_events.append(ElevatorEvent(kind="FLOOR_SENSOR", payload=payload))
    return possible_events


def evolve_elevator(elevator: Elevator, visited_states: set):
    for event in get_possible_events(elevator.state):
        new_elevator = elevator.copy()
        new_elevator.handle_event(event)
        new_elevator.invariants()
        new_state = new_elevator.state
        if new_state not in visited_states:
            visited_states.add(new_state)
            evolve_elevator(new_elevator, visited_states)
    return visited_states



elevator = Elevator()
elevators = [elevator]
visited_states = {elevator.state}

visted_states = evolve_elevator(elevator, visited_states)

for s in sorted(visited_states, key=lambda x: (x.mode, x.current_floor)):
    print(s)
