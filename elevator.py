from dataclasses import dataclass
from copy import copy
from typing import Literal, Union, Optional

from modes import MOVING, IDLE, LOADING


# Is it a good idea to have some sort of class structure for the different inputs possible?
# for ex: ElevatorInput, OnboardButton, HallwayButton
# Could this also encapsulate the floor sensor messages?
# Let's try
@dataclass
class ElevatorInput:
    source: Union[Literal["ONBOARD_PANEL", "FLOOR_SENSOR"], int]
    command: Union[Literal["UP", "DOWN"], int]  # This name is really bad


@dataclass
class ElevatorEvent:
    kind: Literal[
        "ONBOARD_PANEL_BUTTON_PRESS",
        "FLOOR_SENSOR",
        "HALLWAY_BUTTON_PRESS",
        "LOADING_COMPLETE",
    ]
    payload: Optional[dict] = None


# Not sure about this one
@dataclass
class ElevatorInstruction:
    kind: Literal["MOVE"]
    dest_floor: int  # Should be between 0 and 5. Where do we control this?


# Super dumb class representing the motor control
class MotorController:
    def __init__(self, motor_state="OFF"):
        self.motor_state = motor_state

    def move(self, direction: Literal["UP", "DOWN"]):
        self.motor_state = "ON"

    def stop(self):
        self.motor_state = "OFF"


class Elevator:
    def __init__(self, mode=IDLE, current_floor=1, direction=None):
        self.mode = mode
        self.current_floor = current_floor
        self.direction = direction

        self.motor_controller = MotorController()

        self.stops = set()
        self.stops_for_later = set()
        self.stops_for_after_later = set()

        self.invariants()

    def __repr__(self):
        return (
            f"Elevator(mode={self.mode.__name__}, {self.current_floor=}, "
            f"{self.direction=}, {self.stops=}, {self.stops_for_later=})"
        )

    def invariants(self):
        assert not (
            self.mode == IDLE
            and any(
                (self.stops, self.stops_for_later, self.stops_for_after_later)
            )
        ), "IDLE and with stops to fulfil"
        assert not (
            self.mode == IDLE and self.direction is not None
        ), "IDLE but with a direction"
        assert not (self.current_floor > 5), "Went through roof"
        assert not (self.current_floor < 1), "Went through floor"
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
            self.mode.handle_floor_sensor_input(
                self, floor=event.payload["floor"]
            )
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

    # def _open_doors(self):
    #     ...
    #
    # def _finish_loading(self):
    #     ...

    # def _continue_or_idle(self):
    #     assert self.mode == "LOADING"
    #     if not self.stops():
    #         if
    #     if not any(self.destinations, self.up_requests, self.down_requests):
    #         self.mode = "IDLE"
    #
    # def _open_doors(self):
    #     self.doors_open = True
    #
    # def _close_doors(self):
    #     self.doors_open = False
    #
    # # Not sure that we need this one
    # def enqueue_instruction(self, instruction: ElevatorInstruction):
    #     # Depending on the pending instructions the new one will go to the end of the queue
    #     # or somewhere else
    #     ...
    #
    # # Dave recommends that the motor is dumb. That meaning we control it more from the
    # # elevator instead of sending it messages that might have more context such as
    # # destination floors or the likes
    # # On a second thought, my approach might not be too bad, but the messages might
    # # be better if they're simpler than how I initially had conceived them
    # # example: "up", "down", "stop" might be better messages than "go to floor 3" etc.
    # def fulfil_instruction(self, instruction: ElevatorInstruction):
    #     """Send message to the control system so it fulfils an instruction"""
    #     ...


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
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2})
    )
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3})
    )
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 4})
    )
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 5})
    )
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
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 4})
    )
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3})
    )
    elevator.handle_event(
        ElevatorEvent(kind="ONBOARD_PANEL_BUTTON_PRESS", payload={"dest": 5})
    )
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2})
    )
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
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 2})
    )
    assert elevator.stops == {3, 5}
    assert elevator.stops_for_later == {4, 1}
    elevator.handle_event(
        ElevatorEvent(kind="FLOOR_SENSOR", payload={"floor": 3})
    )
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


test_scenario()

# Invariants:
# I'll write the ones that I spot in my current implementation here
# We can't have empty destinations and mode != "IDLE"
