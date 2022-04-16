from os import system
from time import sleep
from random import choice

import tensorflow as tf
import numpy as np
import operator

free = ' '
ghost = '*'
wall = '|'
barrier = '-'
agent = '^'

world = []
world_blocks_row_quantity = 2

world_block_keys = ['0', '1']
world_blocks = {
    '0:0': [
        '*', '|', ' ', '-', '|',
        '*', '|', ' ', '-', '|',
        '*', '|', ' ', '-', '|',
    ],
    '0:1': [
        '*', '|', ' ', '-', '|',
        '*', '|', ' ', ' ', '|',
        '*', '|', '-', ' ', '|',
    ],
    '1:0': [
        '*', '|', '-', ' ', '|',
        '*', '|', ' ', ' ', '|',
        '*', '|', ' ', '-', '|',
    ],
    '1:1': [
        '*', '|', '-', ' ', '|',
        '*', '|', '-', ' ', '|',
        '*', '|', '-', ' ', '|',
    ],
}
world_block_empty = ['*', '|', ' ', ' ', '|']
world_block_key_current = '0:0'

world_block_row_count = len(world_blocks['0:0']) // len(world_block_empty)

indexes_last_free_cells = [-3, -1]
agent_state = {'init': False, 'x': -1, 'y': -1, 'step_index': -1}

# ML Configure
models = tf.keras.models
layers = tf.keras.layers

inputs = []  # [[]]
labels = []  # [[]]

model = models.Sequential([
    layers.Dense(3, activation='relu'),
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
    if world[-len(world_block_empty):].count(free) == len(world_block_keys):
        del world[-len(world_block_empty):]


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


def redraw_actor_ml():
    top_index = get_actor_step_top()
    left_index = get_actor_step_left()
    right_index = get_actor_step_right()

    [pred] = model.predict([[top_index, left_index, right_index]])
    pred_index, pred_value = max(enumerate(pred), key=operator.itemgetter(1))
    print(pred_index, pred_value)

    # todo проверка пересечения с перегородкой, куда собирается перейти агент
    # вызывать при попадании в перегородку: model.fit(inputs, labels, epochs=16)
    if pred_index == 0:
        agent_state['y'] -= 1

    elif pred_index == 1:
        agent_state['x'] -= 1

    elif pred_index == 2:
        agent_state['x'] += 1

    print(agent_state)

    agent_state['step_index'] = pred_index

    # ///

    inputs.append([top_index, left_index, right_index])

    # todo выходит за пределы поля
    labels.append([
        1 if top_index >= 0 and world[top_index] == free else 0.1,
        1 if world[left_index] == free else 0.1,
        1 if world[right_index] == free else 0.1,
    ])


def get_actor_step_top():
    return agent_state['x'] + (agent_state['y'] - 1) * len(world_block_empty)


def get_actor_step_left():
    return (agent_state['x'] - 1) + agent_state['y'] * len(world_block_empty)


def get_actor_step_right():
    return (agent_state['x'] + 1) + agent_state['y'] * len(world_block_empty)


def clear_scene(delay=0.1):
    sleep(delay)
    system('clear')


def add_blocks_to_scene():
    if agent_state['y'] == 0:
        agent_state['init'] = False
        agent_state['x'] = -1
        agent_state['y'] = -1

        generate_blocks_to_scene()


def game_loop():
    clear_scene()
    add_blocks_to_scene()
    draw_scene()
    # redraw_actor()
    redraw_actor_ml()


generate_blocks_to_scene()

while True:
    game_loop()
