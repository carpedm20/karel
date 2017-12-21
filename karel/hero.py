# Code based on https://github.com/alts/karel

class Hero(object):
    def __init__(self, position, facing, marker_bag=None):
        self.position = position
        self.facing = facing
        self.marker_bag = None

    def move(self):
        self.position = (
            self.position[0] + self.facing[0],
            self.position[1] + self.facing[1]
        )

    def turn_left(self):
        self.facing = (
            self.facing[1],
            -self.facing[0]
        )

    def turn_right(self):
        self.turn_left()
        self.turn_left()
        self.turn_left()

    def holding_markers(self):
        return (self.marker_bag is None) or self.marker_bag > 0

    def pick_marker(self):
        if self.marker_bag is not None:
            self.marker_bag += 1

    def put_marker(self):
        if self.marker_bag is not None:
            self.marker_bag -= 1
