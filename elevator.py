from dataclasses import dataclass
from copy import copy
from typing import Literal

from modes import MOVING, IDLE, LOADING


@dataclass
class ElevatorEvent:
    kind: Literal[
        "ONBOARD_PANEL_BUTTON_PRESS",
        "FLOOR_SENSOR",
        "HALLWAY_BUTTON_PRESS",
        "LOADING_COMPLETE",
    ]
    payload: dict | None = None


# Super dumb class representing the motor control
class MotorController:
    def __init__(self, motor_state="OFF"):
        self.motor_state = motor_state

    def move(self, direction: Literal["UP", "DOWN"]):
        self.motor_state = "ON"

    def stop(self):
        self.motor_state = "OFF"


@dataclass(eq=True, frozen=True)
class ElevatorState:
    mode: Literal["IDLE", "MOVING", "LOADING"]
    direction: Literal["UP", "DOWN"] | None
    current_floor: int


class Elevator:
    TOP_FLOOR = 5
    BOTTOM_FLOOR = 1

    def __init__(self, mode=IDLE, current_floor=1, direction=None):
        self.mode = mode
        self.current_floor = current_floor
        self.direction = direction

        self.motor_controller = MotorController()

        self.stops = set()
        self.stops_for_later = set()
        self.stops_for_after_later = set()

    def __repr__(self):
        return (
            f"Elevator(mode={self.mode.__name__}, {self.current_floor=}, "
            f"{self.direction=}, {self.stops=}, {self.stops_for_later=})"
        )

    def copy(self) -> "Elevator":
        new_elevator = Elevator(
            mode=self.mode, current_floor=self.current_floor, direction=self.direction
        )
        new_elevator.stops = copy(self.stops)
        new_elevator.stops_for_later = copy(self.stops_for_later)
        new_elevator.stops_for_after_later = copy(self.stops_for_after_later)
        return new_elevator

    @property
    def state(self) -> ElevatorState:
        """Return the current state of the Elevator

        These are:
            - mode
            - direction
            - current_floor
        The list of stops will not be part of the state, for now
        """
        curr_state = ElevatorState(
            mode=self.mode.__name__,
            direction=self.direction,
            current_floor=self.current_floor,
        )
        return curr_state

    def invariants(self):
        # TODO: we could be ignoring a button press by mistake. 
        # We should track button presses not just stops
        assert not (
            self.mode == IDLE
            and any((self.stops, self.stops_for_later, self.stops_for_after_later))
        ), "IDLE and with stops to fulfil"
        assert not (
            self.mode == IDLE and self.direction is not None
        ), "IDLE but with a direction"
        assert not (self.current_floor > Elevator.TOP_FLOOR), "Went through roof"
        assert not (self.current_floor < Elevator.BOTTOM_FLOOR), "Went through floor"
        assert not (self.mode == MOVING and not self.stops), "Moving with no stops"
        assert not (
            self.mode == MOVING
            and self.direction == "UP"
            and max(self.stops) <= self.current_floor
        ), "Moving up and stops for now are below"
        assert not (
            self.mode == MOVING
            and self.direction == "DOWN"
            and min(self.stops) >= self.current_floor
        ), "Moving down and stops for now are above"
        assert not (
            self.mode == MOVING
            and self.direction == "DOWN"
            and self.current_floor == Elevator.BOTTOM_FLOOR
        ), "Moving down from the bottom floor"
        assert not (
            self.mode == MOVING
            and self.direction == "UP"
            and self.current_floor == Elevator.TOP_FLOOR
        ), "Moving up from the top floor"
        assert not (
            self.stops.intersection(self.stops_for_later).intersection(
                self.stops_for_after_later
            )
        ), "The same floor can't be in more than one stop lists"

    def handle_event(self, event: ElevatorEvent):
        # input: ElevatorInstruction = ElevatorInstruction() # Translate an input (button press) into an instruction (go to floor N)  # noqa: B950
        if event.kind == "ONBOARD_PANEL_BUTTON_PRESS":
            self.mode.handle_onboard_button_press(
                self, dest_floor=event.payload["dest"]
            )
        elif event.kind == "FLOOR_SENSOR":
            self.mode.handle_floor_sensor_input(self, floor=event.payload["floor"])
        elif event.kind == "HALLWAY_BUTTON_PRESS":
            self.mode.handle_hallway_button_press(
                self,
                floor=event.payload["floor"],
                direction=event.payload["direction"],
            )
        elif event.kind == "LOADING_COMPLETE":
            self.mode.handle_loading_complete(self)
        else:
            raise RuntimeError("Unsupported Event")

    def move(self, direction: Literal["UP", "DOWN"]):
        self.mode = MOVING
        self.direction = direction
        self.motor_controller.move(direction)

    def load(self):
        self.motor_controller.stop()
        self.mode = LOADING
        self.stops.discard(self.current_floor)

    def change_direction(self):
        assert self.direction in ("UP", "DOWN")
        self.direction = "UP" if self.direction == "DOWN" else "DOWN"
        self.stops = copy(self.stops_for_later)
        self.stops_for_later = copy(self.stops_for_after_later)
        self.stops_for_after_later = set()
        self.mode = MOVING

    def go_idle(self):
        self.mode = IDLE
        self.direction = None


def test_scenario():
    # Elevator initialises correctly
    elevator = Elevator()
    assert elevator.mode == IDLE
    assert elevator.direction is None
    assert elevator.current_floor == 1
    print("Elevator initialises fine")

    # Elevator moves correctly when idle
    elevator.handle_event(
        ElevatorEvent(kind="ONBOARD_PANEL_BUTTON_PRESS", payload={"dest": 5})
    )
    assert elevator.mode == MOVING
    elevator.invariants()
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2}))
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3}))
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 4}))
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 5}))
    assert elevator.mode == LOADING
    elevator.invariants()
    elevator.handle_event(ElevatorEvent(kind="LOADING_COMPLETE"))
    assert elevator.mode == IDLE
    elevator.invariants()
    print("Elevator moves up fine if idle")

    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 2, "direction": "DOWN"},
        )
    )
    assert elevator.mode == MOVING
    elevator.invariants()
    print(repr(elevator))
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 4}))
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3}))
    elevator.handle_event(
        ElevatorEvent(kind="ONBOARD_PANEL_BUTTON_PRESS", payload={"dest": 5})
    )
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2}))
    assert elevator.mode == LOADING
    elevator.invariants()
    elevator.handle_event(ElevatorEvent(kind="LOADING_COMPLETE"))
    assert elevator.mode == MOVING
    elevator.invariants()
    print(repr(elevator))
    print("Elevator moves down fine if idle and chains a new movement")

    elevator = Elevator()
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 5, "direction": "DOWN"},
        )
    )
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 4, "direction": "DOWN"},
        )
    )
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 3, "direction": "UP"},
        )
    )
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 1, "direction": "UP"},
        )
    )
    assert elevator.mode == MOVING
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2}))
    assert elevator.stops == {3, 5}
    assert elevator.stops_for_later == {4, 1}
    elevator.handle_event(ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3}))
    assert elevator.mode == LOADING
    assert elevator.stops == {5}
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 3, "direction": "UP"},
        )
    )
    assert elevator.mode == LOADING
    assert elevator.stops == {5}
    elevator.handle_event(ElevatorEvent(kind="LOADING_COMPLETE"))
    assert elevator.mode == MOVING
    elevator.handle_event(
        ElevatorEvent(
            kind="HALLWAY_BUTTON_PRESS",
            payload={"floor": 3, "direction": "UP"},
        )
    )
    assert elevator.stops_for_after_later == {3}


# test_scenario()
