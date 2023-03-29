class LOADING:
    @staticmethod
    def handle_onboard_button_press(elev, dest_floor: int):
        # The below has quite a lot of repetition
        if elev.direction == "UP":
            # If destination is in the direction of movement we will stop there.
            if dest_floor > elev.current_floor:
                elev.stops.add(dest_floor)
            # Otherwise we will stop when we've turned around
            elif dest_floor < elev.current_floor:
                elev.stops_for_later.add(dest_floor)
            # If dest_floor is the same floor ignore it
            else:
                pass
        elif elev.direction == "DOWN":
            # If destination is in the direction of movement we will stop there.
            if dest_floor < elev.current_floor:
                elev.stops.add(dest_floor)
            # Otherwise we will stop when we've turned around
            elif dest_floor > elev.current_floor:
                elev.stops_for_later.add(dest_floor)
            # If dest_floor is the same floor ignore it
            else:
                pass

    @staticmethod
    def handle_hallway_button_press(elev, floor, direction):
        # If called from the current floor we open the doors
        if floor == elev.current_floor:
            elev.load()
        # If floor is in opposite direction, we will stop when going that direction
        # unless it can be our lowest or highest stop
        if elev.direction != direction:
            if elev.direction == "UP":
                if floor >= max(elev.stops):
                    elev.stops.add(floor)
                else:
                    elev.stops_for_later.add(floor)
            if elev.direction == "DOWN":
                if floor <= max(elev.stops):
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
                if elev.direction == "UP":
                    if floor >= max(elev.stops):
                        elev.stops.add(floor)
                    else:
                        elev.stops_for_later.add(floor)
                if elev.direction == "DOWN":
                    if floor <= max(elev.stops):
                        elev.stops.add(floor)
                    else:
                        elev.stops_for_later.add(floor)

    @staticmethod
    def handle_floor_sensor_input(elev, floor: int):
        raise RuntimeError("Received floor sensor when LOADING")

    @staticmethod
    def handle_loading_complete(elev):
        if not elev.stops:
            if not elev.stops_for_later:
                elev.go_idle()
            else:
                elev.change_direction()
        else:
            elev.move(elev.direction)
