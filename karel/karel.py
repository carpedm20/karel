# Code based on https://github.com/alts/karel
#-*- coding: utf-8 -*-
from __future__ import print_function

import re
import numpy as np
from collections import Counter

from .hero import Hero
from .utils import Tcolors, get_rng

def draw2d(array):
    print("\n".join(["".join(["#" if val > 0 else "." for val in row]) for row in array]))

def border_mask(array, value):
    array[0,:], array[-1,:], array[:,0], array[:,-1] = value, value, value, value

def hero_action(func):
    def fn(*args, **kwargs):
        self = args[0]
        out = func(self)
        if self.debug:
            print(func.__doc__, out)
            self.draw()
        return out
    return fn

def marker_action(func):
    def fn(*args, **kwargs):
        self = args[0]
        out = func(self)
        if self.debug:
            print(func.__doc__, out)
        return out
    return fn

world_condition = marker_action


class Karel(object):
    HERO_CHARS = '<^>v'
    MARKER_CHAR = 'o'
    WALL_CHAR = '#'
    EMPTY_CHAR = '.'

    COLOR_DICT = {
            WALL_CHAR: WALL_CHAR,
            MARKER_CHAR: Tcolors.WARNING + MARKER_CHAR + Tcolors.ENDC,
    }
    #COLOR_DICT.update({
    #        str(num): Tcolors.WARNING + str(num) + Tcolors.ENDC for num in range(9) })
    COLOR_DICT.update({
            char: Tcolors.OKGREEN + char + Tcolors.ENDC for char in HERO_CHARS })

    def __init__(
            self, state=None, world_size=None, world_path=None, rng=None,
            wall_ratio=0.1, marker_ratio=0.1, max_marker_in_cell=1, debug=False):

        self.debug = debug
        self.rng = get_rng(rng)

        self.markers = []
        if state is not None:
            self.parse_state(state)
        elif world_path is not None:
            self.parse_world(world_path)
        elif world_size is not None:
            self.random_world(world_size, max_marker_in_cell, wall_ratio, marker_ratio)
        else:
            raise Exception(" [!] one of `world_size`, `world_path` and `world` should be passed")

        state = np.zeros_like(self.world, dtype=np.int8)

        self.max_marker = 10
        self.hero_direction = 4

        self.zero_state = np.tile(
                np.expand_dims(state, -1),
                [1, 1, self.hero_direction + 1 + (self.max_marker + 1)])

        if self.debug: self.draw()

    def __enter__(self):
        self.start_screen()
        return self

    def __exit__(self, *args):
        self.end_screen()

    def start_screen(self):
        pass

    def end_screen(self):
        pass

    def random_world(self, world_size, max_marker_in_cell, wall_ratio, marker_ratio):
        height, width = world_size

        if height <= 2 or width <= 2:
            raise Exception(" [!] `height` and `width` should be larger than 2")

        # blank world
        self.world = np.chararray((height, width))
        self.world[:] = "."

        # wall
        wall_array = self.rng.rand(height, width)

        self.world[wall_array < wall_ratio] = self.WALL_CHAR
        border_mask(self.world, self.WALL_CHAR)

        # hero
        x, y, direction = self.rng.randint(1, width-1), \
                self.rng.randint(1, height-1), self.rng.randint(4)
        self.hero = Hero((x, y), ((-1, 0), (1, 0), (0, -1), (0, 1))[direction])
        self.world[y, x] = '.'

        # markers
        marker_array = self.rng.rand(height, width)
        marker_array = (wall_array >= wall_ratio) & (marker_array < marker_ratio)
        border_mask(marker_array, False)

        self.markers = []
        for (y, x) in zip(*np.where(marker_array > 0)):
            self.markers.append((x, y))

        self.world = self.world.astype(str).tolist()

    def parse_world(self, world_path):
        directions = {
            '>': (1, 0),
            '^': (0, 1),
            '<': (-1, 0),
            'v': (0, -1),
        }

        world = [[]]
        with open(world_path) as f:
            for y, line in enumerate(f):
                row = []
                for x, char in enumerate(line.strip()):
                    if char in self.HERO_CHARS:
                        self.hero = Hero((x + 1, y + 1), directions[char])
                        char = '.'
                    elif char == self.MARKER_CHAR:
                        self.markers.append((x + 1, y + 1))
                        char = '.'
                    elif char.isdigit():
                        for _ in range(int(char)):
                            self.markers.append((x + 1, y + 1))
                        char = '.'
                    elif char in [self.WALL_CHAR, self.EMPTY_CHAR]:
                        pass
                    else:
                        raise Exception(" [!] `{}` is not a valid character".format(char))
                    row.append(char)
                world.append([self.WALL_CHAR] + row + [self.WALL_CHAR])

        world.append([])
        for _ in range(len(world[1])):
            world[0].append(self.WALL_CHAR)
            world[-1].append(self.WALL_CHAR)

        self.world = world

    def draw(self, prefix="", skip_number=False, with_color=False, no_print=False):
        canvas = np.array(self.world)

        for (x, y), count in Counter(self.markers).items():
            canvas[y][x] = str(count)

        canvas[self.hero.position[1]][self.hero.position[0]] = self.hero_char()

        texts = []
        for idx, row in enumerate(canvas):
            row_text = "".join(row)
            if skip_number:
                row_text = re.sub('\d', self.MARKER_CHAR, row_text)

            if idx == 0:
                if with_color:
                    text = "{}{}{}{}".format(
                            Tcolors.OKBLUE, prefix, Tcolors.ENDC, row_text)
                else:
                    text = "{}{}".format(prefix, row_text)
            else:
                text = "{}{}".format(len(prefix) * " ", row_text)

            if with_color:
                text = re.sub('.'.format(self.WALL_CHAR), lambda x: self._color_fn(x), text)

            if not no_print:
                print(text)
            texts.append(text)

        if no_print:
            return texts

    def _color_fn(self, x):
        char = x.group()
        if char in self.COLOR_DICT:
            return self.COLOR_DICT[char]
        else:
            return char

    @property
    def state(self):
        """
            0: Hero facing North
            1: Hero facing South
            2: Hero facing West
            3: Hero facing East
            4: Wall
            5: 0 marker
            6: 1 marker
            7: 2 marker
            8: 3 marker
            9: 4 marker
            10: 5 marker
            11: 6 marker
            12: 7 marker
            13: 8 marker
            14: 9 marker
            15: 10 marker
        """
        state = self.zero_state.copy()
        state[:,:,5] = 1

        # 0 ~ 3: Hero facing North, South, West, East
        x, y = self.hero.position
        state[y, x, self.facing_idx] = 1

        # 4: wall or not
        for jdx, row in enumerate(self.world):
            for idx, char in enumerate(row):
                if char == self.WALL_CHAR:
                    state[jdx][idx][4] = 1
                elif char == self.WALL_CHAR or char in self.HERO_CHARS:
                    state[:,:,5] = 1

        # 5 ~ 15: marker counter
        for (x, y), count in Counter(self.markers).items():
            state[y][x][5] = 0
            state[y][x][5 + count] = 1
            #state[y][x][min(5 + count, self.max_marker)] = 1

        # draw2d(state[:,:,5])
        return state

    def parse_state(self, state):
        height, width, _ = state.shape

        self.world = np.chararray((height, width))
        self.world[:] = "."

        # wall
        self.world[state[:,:,4] == 1] = self.WALL_CHAR

        # hero
        y, x, facing_idx = zip(*np.where(state[:,:,:4]==1)).__next__()
        self.hero = Hero((x, y), ((0, -1), (0, 1), (-1, 0), (1, 0))[facing_idx])

        # markers
        max_marker = len(state[0,0,6:])
        for num in range(1, max_marker + 1):
            for (y, x) in zip(*np.where(state[:,:,5+num] == 1)):
                for _ in range(num):
                    self.markers.append((x, y))

        self.world = self.world.astype(str).tolist()

    def draw_exception(self, exception):
        pass

    def hero_char(self):
        # index will be in (-2, -1, 1, 2)
        index = self.hero.facing[0] + 2*self.hero.facing[1]
        return ' >v^<'[index]

    @hero_action
    def move(self):
        '''Move'''
        success = True
        if not self._front_is_clear():
            #raise Exception('can\'t move. There is a wall in front of Hero')
            success = False
        else:
            self.hero.move()
        return success

    @hero_action
    def turn_left(self):
        '''Turn left'''
        self.hero.turn_left()

    @marker_action
    def turn_right(self):
        '''Turn right'''
        self.hero.turn_right()

    @marker_action
    def pick_marker(self):
        '''Pick marker'''
        position = self.hero.position
        for i, coord in enumerate(self.markers):
            if coord == self.hero.position:
                del self.markers[i]
                self.hero.pick_marker()
                break
        else:
            #raise Exception('can\'t pick marker from empty location')
            pass

    @marker_action
    def put_marker(self):
        '''Put marker'''
        if not self.hero.holding_markers():
            #raise Exception('can\'t put marker. Hero has none')
            pass
        else:
            self.markers.append(self.hero.position)
            self.hero.put_marker()
        return Counter(self.markers)[self.hero.position]

    @world_condition
    def front_is_clear(self):
        '''Check front is clear'''
        return self._front_is_clear()

    def _front_is_clear(self):
        next_x = self.hero.position[0] + self.hero.facing[0]
        next_y = self.hero.position[1] + self.hero.facing[1]
        return self.world[next_y][next_x] == '.'

    @world_condition
    def left_is_clear(self):
        '''Check left is clear'''
        return self._left_is_clear()

    def _left_is_clear(self):
        next_x = self.hero.position[0] + self.hero.facing[1]
        next_y = self.hero.position[1] - self.hero.facing[0]
        return self.world[next_y][next_x] == '.'

    @world_condition
    def right_is_clear(self):
        '''Check right is clear'''
        return self._right_is_clear()

    def _right_is_clear(self):
        next_x = self.hero.position[0] - self.hero.facing[1]
        next_y = self.hero.position[1] + self.hero.facing[0]
        return self.world[next_y][next_x] == '.'

    @world_condition
    def markers_present(self):
        '''Check markers present'''
        return self.hero.position in self.markers

    @world_condition
    def no_markers_present(self):
        '''Check no markers present'''
        return self.hero.position not in self.markers

    @property
    def facing_north(self):
        return self.hero.facing[1] == -1

    @property
    def facing_south(self):
        return self.hero.facing[1] == 1

    @property
    def facing_west(self):
        return self.hero.facing[0] == -1

    @property
    def facing_east(self):
        return self.hero.facing[0] == 1

    @property
    def facing_idx(self):
        if self.facing_north: # (0, -1)
            return 0
        elif self.facing_south: # (0, 1)
            return 1
        elif self.facing_west: # (-1, 0)
            return 2
        elif self.facing_east: # (1, 0)
            return 3

    frontIsClear = front_is_clear
    leftIsClear = left_is_clear
    rightIsClear = right_is_clear
    markersPresent = markers_present
    noMarkersPresent = no_markers_present

    turnRight = turn_right
    turnLeft = turn_left
    pickMarker = pick_marker
    putMarker = put_marker
