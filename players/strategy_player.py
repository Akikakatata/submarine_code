import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player


class StrategicPlayer(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        self.field = [[i, j] for i in range(Player.FIELD_SIZE) for j in range(Player.FIELD_SIZE)]
        self.ship_positions = {'w': None, 'c': None, 's': None}
        super().__init__(self.ship_positions)

        # Track the opponent's attacked squares
        self.opponent_attacked = []
        # Track the opponent's ship positions
        self.opponent_ship_positions = []

    def place_ships(self):
        # Ensure that none of your ships overlap with each other
        ship_types = list(self.ships.keys())
        random.shuffle(ship_types)

        for ship_type in ship_types:
            position = random.choice(self.field)

            while self.overlap(position) is not None:
                position = random.choice(self.field)

            self.ship_positions[ship_type] = position
            self.field.remove(position)

        return json.dumps(self.ship_positions)

    def action(self):
        if self.turn == 1:
            # First move advantage: Take the first move
            return json.dumps({'move': 'first_move'})

        if self.turn == 2:
            # Initial attacks: Gather information about opponent's ship positions
            targets = self.get_possible_ship_positions()
            if targets:
                to = random.choice(targets)
                self.opponent_attacked.append(to)
                response = self.attack(to)
                if 'hit' in response:
                    self.opponent_ship_positions.append(response['hit'])
                return json.dumps(response)

        # Prioritize attacking squares around the opponent's ships rather than random locations
        targets = self.get_possible_ship_positions()
        if targets:
            to = self.choose_target(targets)
            self.opponent_attacked.append(to)
            response = self.attack(to)
            if 'hit' in response:
                self.opponent_ship_positions.append(response['hit'])
            return json.dumps(response)

        # Movement: Evade opponent's attacks and strategize ship movements
        move_ship = self.get_moveable_ship()

        if move_ship:
            to = self.get_move_destination(move_ship)
            return json.dumps(self.move(move_ship, to))

    def choose_target(self, targets):
        # Prioritize attacking the opponent's ships with the least remaining endurance
        ship_endurance = {ship.type: ship.endurance for ship in self.opponent.ships.values()}
        targets.sort(key=lambda pos: ship_endurance[self.opponent.overlap(pos)], reverse=True)

        return targets[0]

    def get_possible_ship_positions(self):
        # Get the possible ship positions based on the opponent's attacked squares and own attacks
        possible_positions = []

        for position in self.opponent_attacked + self.opponent_ship_positions:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    x, y = position[0] + i, position[1] + j
                    if self.is_valid_position([x, y]):
                        possible_positions.append([x, y])

        return possible_positions

    def get_moveable_ship(self):
        # Choose a ship to move
        moveable_ships = []

        for ship in self.ships.values():
            if ship.endurance > 0 and not self.is_ship_attacked(ship):
                moveable_ships.append(ship)

        return random.choice(moveable_ships) if moveable_ships else None

    def get_move_destination(self, ship):
        # Get a valid destination for ship movement
        possible_destinations = []

        for i in range(-1, 2):
            for j in range(-1, 2):
                x, y = ship.position[0] + i, ship.position[1] + j
                if self.is_valid_position([x, y]) and not self.is_attacked([x, y]):
                    possible_destinations.append([x, y])

        return random.choice(possible_destinations) if possible_destinations else ship.position

    def is_ship_attacked(self, ship):
        # Check if the ship has been attacked by the opponent
        for position in self.opponent_attacked:
            if ship.position == position:
                return True

        return False

    def is_valid_position(self, position):
        # Check if the position is within the valid field range
        x, y = position
        return 0 <= x < Player.FIELD_SIZE and 0 <= y < Player.FIELD_SIZE

    def is_attacked(self, position):
        # Check if the position has been attacked by the opponent
        return position in self.opponent_attacked


def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            print(get_msg)
            player = StrategicPlayer(seed)
            sockfile.write(player.place_ships() + '\n')

            while True:
                info = sockfile.readline().rstrip()
                print(info)
                if info == "your turn":
                    sockfile.write(player.action() + '\n')
                    get_msg = sockfile.readline()
                    player.update(get_msg)
                elif info == "waiting":
                    get_msg = sockfile.readline()
                    player.update(get_msg)
                elif info == "you win":
                    break
                elif info == "you lose":
                    break
                elif info == "even":
                    break
                else:
                    raise RuntimeError("unknown information")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submarine Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed of the player",
        required=False,
        default=0,
    )
    args = parser.parse_args()

    main(args.host, args.port, seed=args.seed)
