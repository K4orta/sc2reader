# -*- coding: utf-8 -*-
from __future__ import absolute_import

import hashlib

from collections import namedtuple

from sc2reader.constants import *

Location = namedtuple('Location',('x','y'))
MapData = namedtuple('MapData',['gateway','map_hash'])
ColorData = namedtuple('ColorData',['a','r','g','b'])
BnetData = namedtuple('BnetData',['gateway','unknown2','subregion','uid'])

class DepotFile(object):
    url_template = 'http://{0}.depot.battle.net:1119/{1}.{2}'

    def __init__(self, bytes):
        self.server = bytes[4:8].decode('utf-8').strip('\x00 ')
        self.hash = bytes[8:].encode('hex')
        self.type = bytes[0:4]

    @property
    def url(self):
        return self.url_template.format(self.server, self.hash, self.type)

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


class Team(object):
    """
    The team object primarily a container object for organizing :class:`Player`
    objects with some metadata. As such, it implements iterable and can be
    looped over like a list.

    :param interger number: The team number as recorded in the replay
    """

    #: A unique hash identifying the team of players
    hash = str()

    #: The team number as recorded in the replay
    number = int()

    #: A list of the :class:`Player` objects on the team
    players = list()

    #: The result of the game for this team.
    #: One of "Win", "Loss", or "Unknown"
    result = str()

    #: A string representation of the team play races like PP or TPZZ. Random
    #: pick races are not reflected in this string
    lineup = str()

    def __init__(self,number):
        self.number = number
        self.players = list()
        self.result = "Unknown"
        self.lineup = ""

    def __iter__(self):
        return self.players.__iter__()

    @property
    def hash(self):
        raw_hash = ','.join(sorted(p.url for p in self.players))
        return hashlib.sha256(raw_hash).hexdigest()


class Attribute(object):

    def __init__(self, header, attr_id, player, value):
        self.header = header
        self.id = attr_id
        self.player = player

        if self.id not in LOBBY_PROPERTIES:
            raise ValueError("Unknown attribute id: "+self.id)
        else:
            self.name, lookup = LOBBY_PROPERTIES[self.id]
            self.value = lookup[value.strip("\x00 ")[::-1]]

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[%s] %s: %s" % (self.player, self.name, self.value)

class Person(object):
    """
    The person object is never actually instanciated but instead acts as a
    parent class for the :class:`Observer` and :class:`Player` classes.

    :param integer pid: The person's unique id in this game.
    :param string name: The person's battle.net name
    """

    #: The person's unique in this game
    pid = int()

    #: The person's battle.net name
    name = str()

    #: A flag indicating the player's observer status.
    #: Really just a shortcut for isinstance(obj, Observer).
    is_observer = bool()

    #: A flag indicating if the person is a human or computer
    is_human = bool()

    #: A list of :class:`ChatEvent` objects representing all of the chat
    #: messages the person sent during the game
    messages = list()

    #: A list of :class:`Event` objects representing all the game events
    #: generated by the person over the course of the game
    events = list()

    #: A flag indicating if this person was the one who recorded the game.
    recorder = bool()

    #: A flag indicating if the person is a computer or human
    is_human = bool()

    #: The player's region.
    region = str()

    def __init__(self, pid, name):
        self.pid = pid
        self.name = name
        self.is_observer = bool()
        self.messages = list()
        self.events = list()
        self.camera_events = list()
        self.ability_events = list()
        self.selection_events = list()
        self.is_human = bool()
        self.region = str()
        self.recorder = False # Actual recorder will be determined using the replay.message.events file

class Observer(Person):
    """
    A subclass of the :class:`Person` class for observers. Fewer attributes
    are made available for observers in the replay file.

    All Observers are human.
    """

    def __init__(self, pid, name):
        super(Observer,self).__init__(pid, name)
        self.is_observer = True
        self.is_human = True

    def __repr__(self):
        return str(self)
    def __str__(self):
        return "Player {0} - {1}".format(self.pid, self.name)

class Player(Person):
    """
    A subclass of the :class:`Person` class for players.
    """

    URL_TEMPLATE = "http://%s.battle.net/sc2/en/profile/%s/%s/%s/"

    #: A reference to the player's :class:`Team` object
    team = None

    #: A reference to a :class:`Color` object representing the player's color
    color = None

    #: The race the player picked prior to the game starting.
    #: Protoss, Terran, Zerg, Random
    pick_race = str()

    #: The race the player ultimately wound up playing.
    #: Protoss, Terran, Zerg
    play_race = str()

    #: The difficulty setting for the player. Always Medium for human players.
    #: Very easy, East, Medium, Hard, Very hard, Insane
    difficulty = str()

    #: The player's handicap as set prior to game start, ranges from 50-100
    handicap = int()

    #: The subregion with in the player's region
    subregion = int()

    #: The player's bnet uid for his region/subregion.
    #: Used to construct the bnet profile url. This value can be zero for games
    #: played offline when a user was not logged in to battle.net.
    uid = int()

    def __init__(self, pid, name):
        super(Player,self).__init__(pid, name)
        self.is_observer = False

    @property
    def url(self):
        """The player's battle.net profile url"""
        return self.URL_TEMPLATE % (self.gateway, self.uid, self.subregion, self.name)

    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid, self.name, self.play_race)

    @property
    def result(self):
        """The game result for this player: Win, Loss, Unknown"""
        return self.team.result if self.team else "Unknown"

    def format(self, format_string):
        return format_string.format(**self.__dict__)

    def __repr__(self):
        return str(self)


class PlayerSummary():

    #: The index of the player in the game
    pid = int()

    #: The index of the players team in the game
    teamid = int()

    #: The race the player played in the game.
    play_race = str()

    #: The race the player picked in the lobby.
    pick_race = str()

    #: If the player is a computer
    is_ai = False

    #: If the player won the game
    is_winner = False

    #: Battle.Net id of the player
    bnetid = int()

    #: Subregion id of player
    subregion = int()

    #: The player's gateway, such as us, eu
    gateway = str()

    #: The player's region, such as na, la, eu or ru.  This is
    # provided for convenience, but as of 20121018 is strictly a
    # function of gateway and subregion.
    region = str()

    #: unknown1
    unknown1 = int()

    #: unknown2
    unknown2 = dict()

    #: :class:`Graph` of player army values over time (seconds)
    army_graph = None

    #: :class:`Graph` of player income over time (seconds)
    income_graph = None

    #: Stats from the game in a dictionary
    stats = dict()

    def __init__(self, pid):
        self.unknown2 = dict()
        self.pid = pid

    def __str__(self):
        if not self.is_ai:
            return '{0} - {1} - {2}/{3}/'.format(self.teamid, self.play_race, self.subregion, self.bnetid)
        else:
            return '{0} - {1} - AI'.format(self.teamid, self.play_race)

    def __repr__(self):
        return str(self)

    def get_stats(self):
        s = ''
        for k in self.stats:
            s += '{0}: {1}\n'.format(self.stats_pretty_names[k], self.stats[k])
        return s.strip()

BuildEntry = namedtuple('BuildEntry',['supply','total_supply','time','order','build_index'])

# TODO: Are there libraries with classes like this in them
class Graph():
    """A class to represent a graph on the score screen."""

    #: Times in seconds on the x-axis of the graph
    times = list()

    #: Values on the y-axis of the graph
    values = list()

    def __init__(self, x, y, xy_list=None):
        self.times = list()
        self.values = list()

        if xy_list:
            for x, y in xy_list:
                self.times.append(x)
                self.values.append(y)
        else:
            self.times = x
            self.values = y

    def as_points(self):
        """ Get the graph as a list of (x, y) tuples """
        return zip(self.times, self.values)

    def __str__(self):
        return "Graph with {0} values".format(len(self.times))

