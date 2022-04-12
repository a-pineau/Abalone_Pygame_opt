import math
import random
import pygame

from pygame import gfxdraw
from pygame.locals import *
from constants import *
from copy import deepcopy

pygame.init()


class Game(pygame.sprite.Sprite):
    """
    A class used to represent a standard Abalone board.
    Both players have 14 marbles.
    A player loses whenever 6 of his marbles are out.
    
    Attributes
    ----------

    Methods
    -------


    Static Methods
    --------------

    """
    
    # Constructor
    # -----------
    def __init__(self, configuration=STANDARD):
        """Constructor.

        Calls the parent constructor and initializes all the attributes.
        It also builds to marbles to their initial positions with respect to
        the chosen configuration.

        Parameter
        ---------
        configuration: list (optional, default=STANDARD)
            Initial positions of the marbles on the board.
            the STANDARD configuration is the one commonly used in
            mainstream abalone games.
        """
        
        super().__init__()
        self.data = configuration
        self.current_color = 2 # Change to random choice
        self.rect_marbles = {}
        self.rect_coordinates = []
        self.colors_2_change = {}
        self.marbles_2_change = {}
        self.range_distance = None
        self.compute_rect_coordinates()
        
    def compute_rect_coordinates(self):   
        """TODO

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        for i_row, row in enumerate(self.data):
            # Number of marbles in the current row
            for i_col in range(len(row)):
                # The value 5 corresponds to the number of marbles in the first row
                # The board's position is defined w/ respect to the top-left marble (first marble of top-row)
                x = FIRST_TOP_LEFT_X - MARBLE_SIZE * (0.5 * (len(self.data[i_row]) - 5) - i_col)
                y = FIRST_TOP_LEFT_Y + MARBLE_SIZE * i_row
                self.rect_coordinates.append((x, y))

    def display_marbles(self, screen) -> None:
        """TODO

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        
        screen.fill(BACKGROUND)
        iter_rect_coordinates = iter(self.rect_coordinates)
        for i_row, row in enumerate(self.data):
            for i_col, value in enumerate(row):
                x, y = next(iter_rect_coordinates)
                screen.blit(MARBLE_IMGS[value], (x, y))
                self.rect_marbles[(i_row, i_col)] = MARBLE_IMGS[value].get_rect(topleft = (x, y))
                pygame.draw.rect(screen, RED2, pygame.Rect(x, y, 72, 72), 1) # Debug
            
    def normalize_coordinates(self, position) -> tuple:
        """TODO

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        
        x, y = position
        r = (y - FIRST_TOP_LEFT_Y) // MARBLE_SIZE
        if r in range(0, 9):
            c = (x - (FIRST_TOP_LEFT_X - 0.5 * (len(self.data[r]) - 5) * MARBLE_SIZE)) // MARBLE_SIZE
            if int(c) in range(0, 9):
                return r, int(c)
        return None, None
    
    def is_out_of_bounds(self, origin_x, origin_y) -> bool:
        """TODO

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        if (origin_x, origin_y) != (None, None):
            try:
                self.data[origin_x][origin_y]
            except IndexError:
                return True
            else:
                return False 
        return True
    
    def check_pick_validity(self, origin_x, origin_y) -> dict:
        """TODO.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        move_data = {
            "valid": False, 
            "origin_value": None,
            "origin_marble": None,
            "origin_center": None,
        }
        if not self.is_out_of_bounds(origin_x, origin_y):
            move_data["origin_value"] = self.data[origin_x][origin_y]
            move_data["valid"] = True
            move_data["origin_marble"] = self.rect_marbles[(origin_x, origin_y)]
            move_data["origin_center"] = move_data["origin_marble"].center
        return move_data       
    
    def move_single_marble(self, origin_x, origin_y, origin_center, 
                           target_x, target_y, target_center) -> bool:
        """TODO.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        self.marbles_2_change.clear()
        self.marbles_2_change[(origin_x, origin_y)] = 1
        buffer_target_x, buffer_target_y = target_x, target_y
        enemy = self.enemy()
        colors_seen = [self.current_color] # To keep track of the colors we meet
        valid_move = False
        sumito = False        
        end_move = False
        
        while not end_move:
            # Checking if we are killing a marble (out of bounds)
            try:
                self.rect_marbles[(target_x, target_y)].center
            except KeyError:
                self.marbles_2_change[(origin_x, origin_y)] = self.current_color
                valid_move = True
                break
            else:
                target_center = self.rect_marbles[(target_x, target_y)].center
                target_value = self.data[target_x][target_y]
                
            if target_value in (enemy, self.current_color):
                colors_seen.append(target_value)
            own_marble = target_value == self.current_color
            other_marble = target_value in (enemy, 1)
            # Cannot push more than 3 marbles
            too_much_marbles = colors_seen.count(self.current_color) > 3
            sumito = enemy in colors_seen
            wrong_sumito = (colors_seen.count(enemy) >= colors_seen.count(self.current_color)
                            or enemy in colors_seen and target_value == self.current_color)
            
            if too_much_marbles or wrong_sumito:
                valid_move = False # Impossible move
                break
            # If we keep finding our own marbles
            if own_marble and (target_x, target_y) not in self.marbles_2_change.keys():
                self.marbles_2_change[(target_x, target_y)] = self.current_color
            # Meeting an enemy or a free spot
            elif other_marble:
                if sumito:
                    self.marbles_2_change[(origin_x, origin_y)] = self.current_color
                    self.marbles_2_change[(target_x, target_y)] = enemy
                else:
                    self.marbles_2_change[(target_x, target_y)] = self.current_color
                # Loop ends if a free spot is reached
                if target_value == 1:
                    valid_move = True
                    end_move = True
            # Getting the next spot
            next_spot = self.compute_next_spot(origin_center, target_center)
            # Updating origin/target positions
            origin_center = target_center
            origin_x, origin_y = self.normalize_coordinates(origin_center)
            target_x, target_y = self.normalize_coordinates(next_spot)
            
        if not valid_move:
            self.colors_2_change[(buffer_target_x, buffer_target_y)] = MARBLE_RED
        return valid_move
    
    def move_multiple_marbles(self, mouse_position):
        """TODO.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        # No need to check as a possibility (valid or not) has been found already
        if MARBLE_GREEN in self.colors_2_change.values():
            return True
        elif MARBLE_RED in self.colors_2_change.values():
            return False 
        
        norm_x, norm_y = self.normalize_coordinates(mouse_position)
        new_range_coords = []
        # Incorrect selection
        if self.is_out_of_bounds(norm_x, norm_y):
            return False
        local_value = self.data[norm_x][norm_y]
        if local_value == self.current_color:
            self.marbles_2_change[(norm_x, norm_y)] = 1
        coordinates = [self.rect_marbles[(x, y)].center 
                       for x, y in self.marbles_2_change.keys()
                       if self.marbles_2_change[(x, y)] == 1]
        # Checking first self marbles range validity
        if local_value == self.current_color:
            if self.check_range_validity(coordinates):
                self.colors_2_change[(norm_x, norm_y)] = MARBLE_PURPLE 
            else:
                self.marbles_2_change.pop((norm_x, norm_y))
                return False
        
        # Computing the new marbles positions
        range_length = len(coordinates)
        if local_value != self.current_color and coordinates and range_length <= 3:
            new_x, new_y = self.rect_marbles[(norm_x, norm_y)].center
            norm_x, norm_y = self.normalize_coordinates((new_x, new_y))
            new_range_coords.append((norm_x, norm_y))
            j = - 1 if new_x > coordinates[0][0] else 1
            k = 0 if coordinates[0][1] == coordinates[1][1] else 1
            for _ in range(range_length - 1): 
                new_x = new_x + MARBLE_SIZE * j
                new_y = new_y + MARBLE_SIZE * k
                norm_x, norm_y = self.normalize_coordinates((new_x, new_y))
                new_range_coords.append((norm_x, norm_y))
                if (self.is_out_of_bounds(norm_x, norm_y) or # Out of bound found: invalid new range
                    any(self.data[x][y] != 1 for x, y in new_range_coords)): # Non-free marble: invalid new range
                    if MARBLE_RED not in self.colors_2_change.values():
                        self.colors_2_change[new_range_coords[0]] = MARBLE_RED
                    self.marbles_2_change.clear()
                    return False
                        
        # Updating status and color
        for coords in new_range_coords:
            self.colors_2_change[coords] = MARBLE_GREEN # Move OK
            self.marbles_2_change[coords] = self.current_color
        return True

    def check_range_validity(self, coordinates) -> bool:
        """TODO.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        if len(coordinates) == 3:
            d_first_2_second = self.compute_distance_marbles(coordinates[0], coordinates[1])
            d_second_2_last = self.compute_distance_marbles(coordinates[-1], coordinates[-2])
            if d_second_2_last != d_first_2_second:
                return False # A misaligned marble results in a invalid range
        elif len(coordinates) > 3:
            return False # A range of more than 3 marbles is invalid
        return True 
    
    def update_game(self, valid_move):
        """Save a snapshot of the current grid to the SNAP_FOLDER.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        if valid_move:
            for pos, value in self.marbles_2_change.items():
                print("LOL")
                x, y = pos
                self.data[x][y] = value
        self.marbles_2_change.clear()
        self.colors_2_change.clear()

    @staticmethod
    def compute_next_spot(origin, target):
        """Compute the next spot of given marble coordinates.

        Parameters
        ----------
        origin: tuple of integers (required)
            Initial marble
        target: tuple of integers (required)
            Targetted marble
        Returns
        -------
        spot_x, spot_y: tuple of integers
            Coordinates of the next spot
        """
        
        spot_x = 2 * target[0] - origin[0]
        spot_y = 2 * target[1] - origin[1]
        return spot_x, spot_y
    
    def enemy(self) -> int:
        """Returns the enemy of the current color being played."""
        return 3 if self.current_color == 2 else 2
    
    
    # Static Methods
    # --------------
    
    @staticmethod
    def record_game(screen) -> None:
        """Save a snapshot of the current grid to the SNAP_FOLDER.

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """

        global n_snap
        n_snap += 1
        extension = "png"
        file_name = f"snapshot_{n_snap}.{extension}"
        pygame.image.save(screen, os.path.join(SNAP_FOLDER, file_name))
        
        
    @staticmethod
    def compute_distance_marbles(p1, p2):
        """TODO

        Parameter
        ---------
        screen: pygame.Surface (required)
            Game window
        """
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def main():
    game = Game()

if __name__ == "__main__":
    main()




