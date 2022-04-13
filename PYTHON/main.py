''' Задачи:
Лабиринт:
+ 1. Статичный
+ 2. Бесконечный
+ 3. Генерация: барьеры и путь
+ 4. Агент (координаты)
+ 5. Прохождение
'''

from os import system
from time import sleep, time
from random import choice


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
    top_index = can_actor_step_top()
    step_index = -1

    if top_index >= 0 and world[top_index] == free:
        step_index = top_index
        agent_state['y'] -= 1

    else:
        left_index = can_actor_step_left()

        if world[left_index] == free:
            step_index = left_index
            agent_state['x'] -= 1

        else:
            right_index = can_actor_step_right()

            if world[right_index] == free:
                step_index = right_index
                agent_state['x'] += 1

    agent_state['step_index'] = step_index


def can_actor_step_top():
    return agent_state['x'] + (agent_state['y'] - 1) * len(world_block_empty)


def can_actor_step_left():
    return (agent_state['x'] - 1) + agent_state['y'] * len(world_block_empty)


def can_actor_step_right():
    return (agent_state['x'] + 1) + agent_state['y'] * len(world_block_empty)


def clear_scene(delay=0.5):
    sleep(delay)
    system('clear')


def add_blocks_to_scene():
    if agent_state['y'] == 0:
        agent_state['init'] = False
        agent_state['x'] = -1
        agent_state['y'] = -1

        generate_blocks_to_scene()


def game_loop():
    print(agent_state)

    clear_scene()
    add_blocks_to_scene()
    draw_scene()
    redraw_actor()


generate_blocks_to_scene()

while True:
    game_loop()
