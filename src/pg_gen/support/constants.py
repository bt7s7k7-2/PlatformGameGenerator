from .Color import Color

CAMERA_SCALE = 48
GRAVITY = 100
GROUND_VELOCITY = 10
CLIMB_VELOCITY = 4
SLIDE_VELOCITY = 6
AIR_ACCELERATION = 65
JUMP_IMPULSE = 25
ROOM_WIDTH = 18
ROOM_HEIGHT = 11
AIR_DRAG = 50

TEXT_COLOR = Color.WHITE.to_pygame_color()
HIGHLIGHT_1_COLOR = Color.GREEN.to_pygame_color()
HIGHLIGHT_2_COLOR = Color.RED.to_pygame_color()
MUTED_COLOR = (Color.WHITE * 0.4).to_pygame_color()
TEXT_BG_COLOR = Color.BLACK.to_pygame_color(opacity=127)
TEXT_SELECTION_COLOR = Color.BLUE.mix(Color.CYAN, 0.5).to_pygame_color(opacity=191)
