class MOVING:
    @staticmethod
    def handle_onboard_button_press(elev, dest_floor: int):
        # The below has quite a lot of repetition
        if elev.direction == "UP":
            # If destination is in the direction of movement we will stop there.
            if dest_floor > elev.current_floor:
                elev.stops.add(dest_floor)
            # Otherwise we will stop when we've turned around
            else:  # dest_floor <= elev.current_floor:
                elev.stops_for_later.add(dest_floor)
        elif elev.direction == "DOWN":
            # If destination is in the direction of movement we will stop there.
            if dest_floor < elev.current_floor:
                elev.stops.add(dest_floor)
            # Otherwise we will stop when we've turned around
            else:  # dest_floor >= elev.current_floor:
                elev.stops_for_later.add(dest_floor)

    @staticmethod
    def handle_hallway_button_press(elev, floor, direction):
        # If called from the current floor we cannot stop immediately as we're moving
        # We must see when we need to stop
        if floor == elev.current_floor:
            # if direction is the current one, we will have to stop after later
            # unless this floor would be our lowest or highest stop immediately later
            if elev.direction == direction:
                if elev.direction == "UP":
                    if not elev.stops_for_later or floor <= min(elev.stops_for_later):
                        elev.stops_for_later.add(floor)
                    else:
                        elev.stops_for_after_later.add(floor)
                if elev.direction == "DOWN":
                    if not elev.stops_for_later or floor >= max(elev.stops_for_later):
                        elev.stops_for_later.add(floor)
                    else:
                        elev.stops_for_after_later.add(floor)
            else:
                # We're going in the opposite direction of the press.
                # We will stop later as we've just passed the floor from where the press comes
                elev.stops_for_later.add(floor)
        else:  # Floor is not the one we've just passed
            # If request is for the opposite direction, we will stop when going that direction
            # unless it can be our lowest or highest stop
            if elev.direction != direction:
                if elev.direction == "UP":
                    if floor >= max(elev.stops):
                        elev.stops.add(floor)
                    else:
                        elev.stops_for_later.add(floor)
                if elev.direction == "DOWN":
                    if floor <= min(elev.stops):
                        elev.stops.add(floor)
                    else:
                        elev.stops_for_later.add(floor)
            else:
                # if whoever pressed the button wants to go in our current direction
                # if they're on our way:
                if (elev.direction == "UP" and floor > elev.current_floor) or (
                    elev.direction == "DOWN" and floor < elev.current_floor
                ):
                    elev.stops.add(floor)
                # if they're not on our way, we will stop after later
                # unless it can be our lowest or highest stop for later
                else:
                    # going up
                    if elev.direction == "UP":
                        # floor is the highest of our stops. We can stop now
                        if floor >= max(elev.stops):
                            elev.stops.add(floor)
                        else:
                            elev.stops_for_later.add(floor)
                    if elev.direction == "DOWN":
                        if floor <= min(elev.stops):
                            elev.stops.add(floor)
                        else:
                            elev.stops_for_later.add(floor)

    @staticmethod
    def handle_floor_sensor_input(elev, floor: int):
        if elev.direction == "DOWN":
            if not floor == elev.current_floor - 1:
                raise RuntimeError("Received floor sensor from an unexpected floor")
        elif elev.direction == "UP":
            if not floor == elev.current_floor + 1:
                raise RuntimeError("Received floor sensor from an unexpected floor")
        elev.current_floor = floor
        if floor in elev.stops:
            elev.load()

    @staticmethod
    def handle_loading_complete(elev):
        raise RuntimeError("Received loading complete when MOVING")
