"""Action sent from a client to the server each frame.

Contains the player's name and their input: movement direction,
whether they are shooting, and their aim angle.
Also includes lobby signals (ready to start, restart request).
Designed to be lightweight and fully picklable for zmq transport.
"""


class Action:
    """Represents a single frame of player input.

    Sent from client to server via zmq every game tick.
    """

    def __init__(self, name, accel_x=0, accel_y=0, shooting=False, aim_angle=0,
                 ready=False, restart=False):
        """Initialize an action.

        Args:
            name: Player name string.
            accel_x: Horizontal acceleration (-1 to 1 scale).
            accel_y: Vertical acceleration (-1 to 1 scale).
            shooting: True if the player is firing.
            aim_angle: Angle in radians the player is aiming.
            ready: True if the player pressed SPACE to start.
            restart: True if the player pressed R to restart.
        """
        self.name = name
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.shooting = shooting
        self.aim_angle = aim_angle
        self.ready = ready
        self.restart = restart

    def __repr__(self):
        return f"Action({self.name}, accel=({self.accel_x:.1f},{self.accel_y:.1f}), shoot={self.shooting})"