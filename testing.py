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


def get_new_elevators(elevator, visited_states):
    new_elevators = []
    for event in get_possible_events(elevator.state):
        # print(event)
        new_elevator = elevator.copy()
        new_elevator.handle_event(event)
        new_elevator.invariants()
        # print(new_elevator.state)
        # print(new_elevator.stops)
        if new_elevator.state not in visited_states:
            new_elevators.append(new_elevator)
    if not new_elevators:
        return
    new_states = set(e.state for e in new_elevators)
    visited_states
    # TODO: if no extra states then return
    for elevator in new_elevators:
        new_elevators = get_new_elevators(elevator, visited_states)
    # return new_elevators

elevators = [Elevator()]
visited_states = []

for elevator in elevators:
    new_elevators = get_new_elevators(elevator, visited_states)
