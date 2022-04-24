from os import system
from time import sleep
from random import choice
import operator
import tensorflow as tf

free = ' '
ghost = '*'
wall = '|'
barrier = '-'
agent = '^'

world = []
world_len = 42
world_blocks_row_quantity = 2

world_block_keys = ['0', '1']
world_blocks = {
    '0:0': [
        '*', '|', '|', ' ', '-', '|', '|',
        '*', '|', '|', ' ', '-', '|', '|',
        '*', '|', '|', ' ', '-', '|', '|',
    ],
    '0:1': [
        '*', '|', '|', ' ', '-', '|', '|',
        '*', '|', '|', ' ', ' ', '|', '|',
        '*', '|', '|', '-', ' ', '|', '|',
    ],
    '1:0': [
        '*', '|', '|', '-', ' ', '|', '|',
        '*', '|', '|', ' ', ' ', '|', '|',
        '*', '|', '|', ' ', '-', '|', '|',
    ],
    '1:1': [
        '*', '|', '|', '-', ' ', '|', '|',
        '*', '|', '|', '-', ' ', '|', '|',
        '*', '|', '|', '-', ' ', '|', '|',
    ],
}
world_block_empty = ['*', '|', '|', ' ', ' ', '|', '|']
world_block_key_current = '0:0'

world_block_row_count = len(world_blocks['0:0']) // len(world_block_empty)

indexes_last_free_cells = [-4, -2]
agent_state = {'init': False, 'x': -1, 'y': -1, 'step_index': -1}

# ML Configure
models = tf.keras.models
layers = tf.keras.layers

inputs = []  # [[]] - world
labels = []  # [[]] - top, left, right

model = models.Sequential([
    layers.Dense(world_len, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(10, activation='relu'),
    layers.Dense(3, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='mse',
    metrics=['mae']  # mae | accuracy
)


def generate_blocks_to_scene():
    global world
    global world_block_key_current

    world = []

    for _ in range(world_blocks_row_quantity):
        [left, _] = world_block_key_current.split(':')
        right = choice(world_block_keys)
        world_block_key_current = f'{left}:{right}'
        world.extend(world_blocks[world_block_key_current])

        if left != right:
            world.extend(world_block_empty)

    # Удаление строки с двумя пробелами.
    # if world[-len(world_block_empty):].count(free) == len(world_block_keys):
    #     del world[-len(world_block_empty):]

    # Хак, чтобы генерировался мир всегда с одинаковым количеством элементов.
    world = world[:world_len]


def draw_scene():
    x = 0
    y = -1

    for cell_index, cell in enumerate(world):
        x += 1

        if cell_index % len(world_block_empty) == 0:
            x = 0
            y += 1

            print()

        else:
            last_index = cell_index - len(world)
            [l, r] = indexes_last_free_cells

            # Инициализация положения агента в свободной ячейке.
            if not agent_state['init'] and last_index >= l and last_index <= r and cell == free:
                agent_state['init'] = True
                agent_state['x'] = x
                agent_state['y'] = y

                print(agent, end='')

            elif x == agent_state['x'] and y == agent_state['y']:
                print(agent, end='')

            else:
                print(cell, end='')

    print()


# Алгоритм прохождения.
def redraw_actor():
    top_index = get_actor_step_top()
    step_index = -1

    if top_index >= 0 and world[top_index] == free:
        step_index = top_index
        agent_state['y'] -= 1

    else:
        left_index = get_actor_step_left()

        if world[left_index] == free:
            step_index = left_index
            agent_state['x'] -= 1

        else:
            right_index = get_actor_step_right()

            if world[right_index] == free:
                step_index = right_index
                agent_state['x'] += 1

    agent_state['step_index'] = step_index


# ML алгоритм прохождения.
def redraw_actor_ml():
    global model
    step_index = -1

    top_index = get_actor_step_top()
    left_index = get_actor_step_left()
    right_index = get_actor_step_right()

    world_numbers = []

    for cell in world:
        if cell == free:
            world_numbers.append(0.7)
        else:
            world_numbers.append(0.01)

    [pred] = model.predict([world_numbers])

    pred_dir_index, pred_value = max(
        enumerate(pred),
        key=operator.itemgetter(1))

    print(pred_dir_index, pred_value)

    try:
        if pred_dir_index == 0 and world[top_index] == free:  # top
            step_index = top_index
            agent_state['y'] -= 1

            labels.append([0.99, 0.3, 0.3])

        else:
            if pred_dir_index == 1 and world[left_index] == free:  # left
                step_index = left_index
                agent_state['x'] -= 1

                labels.append([0.3, 0.99, 0.3])

            else:
                if pred_dir_index == 2 and world[right_index] == free:  # right
                    step_index = right_index
                    agent_state['x'] += 1

                    labels.append([0.3, 0.3, 0.99])

        if step_index == -1:
            learning(-1)

        else:
            agent_state['step_index'] = step_index

    except:
        pass
        # print('except')
        # learning(-1)


def get_actor_step_top():
    return agent_state['x'] + (agent_state['y'] - 1) * len(world_block_empty)


def get_actor_step_left():
    return (agent_state['x'] - 1) + agent_state['y'] * len(world_block_empty)


def get_actor_step_right():
    return (agent_state['x'] + 1) + agent_state['y'] * len(world_block_empty)


def clear_scene(delay):
    sleep(delay)
    system('clear')


def replace_blocks_to_scene():
    if agent_state['y'] == 0:
        reset_actor()
        generate_blocks_to_scene()


def reset_actor():
    agent_state['init'] = False
    agent_state['x'] = -1
    agent_state['y'] = -1


def learning(pred_dir_index):
    # print('learning...')

    reset_actor()
    generate_blocks_to_scene()

    world_numbers = []

    for cell in world:
        if cell == free:
            world_numbers.append(0.99)
        else:
            world_numbers.append(0.01)

    inputs.append(world_numbers)

    if pred_dir_index == -1:
        labels.append([0.01, 0.01, 0.01])

    elif pred_dir_index == 0:
        labels.append([0.01, 0.5, 0.5])

    elif pred_dir_index == 1:
        labels.append([0.5, 0.01, 0.5])

    elif pred_dir_index == 2:
        labels.append([0.5, 0.5, 0.01])

    model.fit(inputs, labels, epochs=1)
    inputs = []
    labels = []


def game_loop():
    clear_scene(delay=0.001)
    replace_blocks_to_scene()

    # if tick % 1000 == 0:
    draw_scene()

    # redraw_actor()
    redraw_actor_ml()


generate_blocks_to_scene()

while True:
    game_loop()
