# Hunt the Wumpus
# By Gregory Yob, 1973
# Rewritten in Python by Aleksandra Lipunova
# Python 3.7

import sys
import random


class Cave:
    """ This class creates a cave that consists of 20 rooms, 3 paths each, 
    and other things: flocks of bats, bottomless pits and sleeping Wumpus.
    
    Keyword arguments:
        self.rooms -- a list of room objects in cave
        self.things -- a dict of things (e.g. bats, pits and Wumpus), 
                       the key is a thing name and a value is an object
    
    """


    def __init__(self):
        self.rooms = []
        self.things = {}
        
    def create_cave(self):
        self.create_rooms()
        self.create_things()
    
    def create_rooms(self):
        self.rooms = [Room(room_num) for room_num in range(1,21)]
        increments = [x for x in range(4,10)]+[9]+[x for x in range(9,3,-1)]
        increments_iter = iter(increments)
        for idx, room in enumerate(self.rooms):
            if room.num not in [5, 15, 20]:
                room.set_connection(self.rooms[idx+1])
                self.rooms[idx+1].set_connection(room)
            while room.check_connections_number() < 3:
                increment = next(increments_iter)
                room.set_connection(self.rooms[idx+increment])
                self.rooms[idx+increment].set_connection(room)
    
    def create_things(self):
        things_names = ['Pit1', 'Pit2', 'Bats1', 'Bats2']
        self.things.update({name: Thing(name, 1) for name in things_names})
        self.things.update({'Wumpus': Wumpus('Wumpus', 2)})
        self.things.update({'Player': Player('Player', 0)})
        for things_name in things_names + ['Wumpus', 'Player']:
            thing_obj = self.things[things_name]
            if things_name == 'Wumpus':
                room = random.choice(self.rooms)
            else:
                room = random.choice(self.get_empty_rooms())
            room.place_thing(thing_obj)
            room.set_traces(thing_obj, thing_obj.periphery)
            thing_obj.set_location(room)
    
    def get_empty_rooms(self):
        return [room for room in self.rooms if not room.things]
    
    def get_all_connections(self):
        return {room.num: [nearby.num for nearby in room.connections] \
                for room in self.rooms}


class Room:
    """ This class describes a room connected to other rooms of the cave.
    
    Keyword arguments:
        self.num -- a serial number of the room
        self.connections -- a set that contains objects of nearby rooms
        self.things -- a set that contains things located in the room
        self.affected_by -- a set of surrounding things' objects (each 
                            object has its own radius of influence)
    
    """
    

    def __init__(self, num):
        self.num = num
        self.connections = set()
        self.things = set()
        self.affected_by = set()
        
    def place_thing(self, thing_obj):
        self.things.add(thing_obj)

    def set_traces(self, thing_obj, periphery):
        for circle in range(periphery):
            for room in self.get_room_connections():
                if thing_obj not in room.affected_by:
                    if thing_obj not in room.things:
                        room.affected_by.add(thing_obj)
                room.set_traces(thing_obj, circle)
                
    def remove_traces(self, thing_obj, periphery):
        for circle in range(periphery):
            for room in self.get_room_connections():
                if thing_obj in room.affected_by:
                    room.affected_by.remove(thing_obj)
                room.remove_traces(thing_obj, circle)
        
    def set_connection(self, room_num):
        if room_num not in self.connections:
            self.connections.add(room_num)
       
    def check_connections_number(self):
        return len(self.connections)
    
    def get_room_connections(self):
        return self.connections
       

class Thing:
    """ This class describes all things and creatures located in the cave.
    
    Keyword arguments:
        self.name -- a name of the thing or creature
        self.periphery -- a radius of influence on neightbor rooms
        self.location -- an object of the room where thing currently is
    
    """


    def __init__(self, name, periphery):
        self.name = name
        self.periphery = periphery
        self.location = 0
        
    def set_location(self, room):
        self.location = room
        

class Player(Thing):
    """ This class describes player and all his possible actions. 
    Player's class is inherited from Thing's class so it has same
    keyword arguments.
    
    Additional keyword arguments:
        self.arrows -- a number of arrows player has at the moment
        self.states -- a list of recent events happened with player after
                       they made some actions
    
    """
    

    def __init__(self, name, periphery):
        super().__init__(name, periphery)
        self.arrows = 5
        self.states = []
        
    def move(self, next_room):
        events = []
        for connection in self.location.get_room_connections():
            if connection == next_room:
                self.change_room(next_room)
                event, next_room = self.check_room_things(next_room)
                events.append(event)
                while 'Bats' in event:
                    event, next_room = self.check_room_things(next_room)
                    events.append(event)
                break
        if not events:
            events.append('You can\'t go there.')
        self.states += events
    
    def check_room_things(self, next_room):
        event = ''
        beings = set(being.name for being in next_room.things)
        if {'Bats1', 'Bats2'} & beings:
            for distance in range(random.randint(1, 5)):
                connected = self.location.get_room_connections()
                next_room = random.sample(connected,1)[0]
                self.change_room(next_room)
            event = 'ZAP - Super bat snatch! Elsewheresville for you!'
        if {'Pit1', 'Pit2'} & beings:
            event = 'YYYYIIIIEEEE... Fell in a pit.'
        if {'Wumpus'} & beings:
            event = '...OOPS! Bumped a Wumpus!\nTSK TSK TSK - Wumpus got you!'
        return event, self.location
    
    def change_room(self, next_room):
        self.location.things.remove(self)
        self.location.remove_traces(self, self.periphery)
        next_room.things.add(self)
        next_room.set_traces(self, self.periphery)
        self.location = next_room
        
    def shoot(self, path):
        self.arrows -= 1
        prev_room, left = self.location, 5
        for room in path:
            if left > 0:
                left, correct = self.check_shot(room, prev_room, left)
                if not correct:
                    self.check_missed_shot(prev_room, left)
                    break
        if self.arrows == 0:
            self.states.append('...OOPS! You are out of arrows!')
                    
    def check_shot(self, room, prev_room, left):
        correct = False
        for connection in prev_room.get_room_connections():
            if connection.num == room:
                prev_room, correct = connection, True
                self.check_shot_result(prev_room)
                left -= 1
                break
        return left, correct
                
    def check_missed_shot(self, a_room, left):
        while left > 0:
            a_room = random.sample(a_room.get_room_connections(),1)[0]
            self.check_shot_result(a_room)
            left -= 1
            
    def check_shot_result(self, a_room):
        beings = [thing_obj.name for thing_obj in a_room.things]
        if 'Player' in beings:
            self.states.append('...OOPS! Your arrow returns and kills you!')
        elif 'Wumpus' in beings:
            self.states.append('AHA! You got the Wumpus!')
            
    def get_new_states(self):
        new_states = self.states
        self.states = []
        return new_states
            
            
class Wumpus(Thing):
    """ This class describes Wumpus sleeping in the depths of the cave.
    Wumpus's class is also inherited from Thing's class so it has same
    keyword arguments.
    
    Additional keyword arguments:
        self.states -- a list of recent events happened with Wumpus after
                       it made some actions
    
    """


    def __init__(self, name, periphery):
        super().__init__(name, periphery)
        self.states = []
    
    def hear(self):
        if random.randint(0,100) > 25:
            self.move()
            
    def move(self):
        self.states.append('HUSH! The Wumpus heard the arrow and woke up.')
        self.location.things.remove(self)
        self.location.remove_traces(self, self.periphery)
        next_room = random.sample(self.location.get_room_connections(),1)[0]
        next_room.things.add(self)
        next_room.set_traces(self, self.periphery)
        self.location = next_room
        beings = [thing_obj.name for thing_obj in next_room.things]
        if 'Player' in beings:
            self.states.append('Wumpus bumped you!')
            self.states.append('TSK TSK TSK - Wumpus got you!')
       
    def get_new_states(self):
        new_states = self.states
        self.states = []
        return new_states


def start_adventure():
    cave = Cave()
    cave.create_cave()
    # print(cave.get_all_connections())
    player = cave.things['Player']
    wumpus = cave.things['Wumpus']
    
    print('HUNT THE WUMPUS\n')
    show_instructions()
    while True:
        cur_room = player.location
        describe_room(cur_room)
        make_action(cave, player, wumpus, cur_room)
        display_events(player, wumpus)


def show_instructions():
    show_help = input('SHOW INSTRUCTIONS (Y-N)? ')
    if isinstance(show_help, str) and show_help in 'YNyn':
        if show_help == 'Y' or show_help == 'y':
            with open('instructions.txt') as f:
                instructions = f.read().splitlines()
                for line in instructions:
                    print(line)


def describe_room(room):
    print(f'\nYou are in room {room.num}')
    clues = set(clue.name for clue in room.affected_by)
    if {'Wumpus'} & clues:
        print('\tI smell a Wumpus!')
    if {'Pit1', 'Pit2'} & clues:
        print('\tI feel a draft!')
    if {'Bats1', 'Bats2'} & clues:
        print('\tI hear flapping!')
    next_rooms = [str(room.num) for room in room.get_room_connections()]
    next_rooms_str = ', '.join(next_rooms)
    print(f'Tunnels lead to {next_rooms_str}.\n')
    
    
def make_action(cave, player, wumpus, cur_room):
    while True:
        shoot_move = input('SHOOT OR MOVE (S-M)? ')
        if isinstance(shoot_move, str) and shoot_move in 'SMsm':
            if shoot_move == 'S' or shoot_move == 's':
                if player_shoots(player, wumpus):
                    break
            else:
                if player_walks(cave, player, cur_room):
                    break
        else:
            print('Please enter S or M to choose action.')


def player_shoots(a_player, a_wumpus):
    rooms_num = input('NO. OF ROOMS (1-5)? ')
    if rooms_num.isdigit() and 0 < int(rooms_num) < 6:
        arrow_path = []
        for num in range(int(rooms_num)):
            arrow_path = choose_rooms(arrow_path)
        print('The arrow disappears into the darkness.')
        a_player.shoot(arrow_path)
        a_wumpus.hear()
        return True
    print('Please enter a number from 1 to 5.')
    return False


def choose_rooms(arrow_path):
    while True:
        room_num = input('ROOM#? ')
        if room_num.isdigit() and 0 < int(room_num) < 21:
            arrow_path.append(int(room_num))
            break
        print('Please enter real room numbers.')
    return arrow_path


def player_walks(cave, player, cur_room):
    move_to = input('WHERE TO? ')
    if move_to.isdigit():
        room_connections = cur_room.get_room_connections()
        connections_nums = [room.num for room in room_connections]
        if int(move_to) in connections_nums:
            player.move(cave.rooms[int(move_to)-1])
            return True
    print('Please enter valid room number.')
    return False


def display_events(player, wumpus):
    for state in player.get_new_states()+wumpus.get_new_states():
        if state:
            print(state)
        for marker in {'...OOPS', 'YYYYIIIIEEEE', 'TSK TSK TSK', 'AHA'}:
            if marker in state:
                if marker == 'AHA':
                    print('HEE HEE HEE - The Wumpus will getcha next time')
                else:
                    print('HA HA HA - You lose')
                sys.exit()


if __name__ == '__main__':
    start_adventure()
    