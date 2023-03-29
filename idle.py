class IDLE:
    @staticmethod
    def handle_onboard_button_press(elev, dest_floor: int):
        # If the current floor button is pressed the elevator doesn't moved and opens the doors
        if elev.current_floor == dest_floor:
            elev.load()
        elev.stops.add(dest_floor)
        # in which direction should the elevator move?
        direction = "UP" if dest_floor > elev.current_floor else "DOWN"
        elev.move(direction)

    @staticmethod
    def handle_hallway_button_press(elev, floor, direction):
        if elev.current_floor == floor:
            elev.load()
        else:
            elev.stops.add(floor)
            direction = "UP" if floor > elev.current_floor else "DOWN"
            elev.move(direction)

    @staticmethod
    def handle_floor_sensor_input(elev, floor: int):
        raise RuntimeError("Received floor sensor when IDLE")

    @staticmethod
    def handle_loading_complete(elev):
        raise RuntimeError("Received loading complete when IDLE")
