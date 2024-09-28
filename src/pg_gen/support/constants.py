from .Color import Color

CAMERA_SCALE = 40
GRAVITY = 100
GROUND_VELOCITY = 10
AIR_ACCELERATION = 40
JUMP_IMPULSE = 25
ROOM_WIDTH = 18
ROOM_HEIGHT = 9
AIR_DRAG = 25

TEXT_COLOR = Color.WHITE.to_pygame_color()
HIGHLIGHT_1_COLOR = (Color.GREEN * 0.5).to_pygame_color()
HIGHLIGHT_2_COLOR = (Color.RED * 0.5).to_pygame_color()
TEXT_BG_COLOR = Color.BLACK.to_pygame_color(opacity=127)
TEXT_SELECTION_COLOR = Color.BLUE.mix(Color.CYAN, 0.5).to_pygame_color(opacity=127)
