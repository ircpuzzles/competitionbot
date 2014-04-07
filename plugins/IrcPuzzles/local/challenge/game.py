
import os
from os.path import join, isfile
import json
import logging
logger = logging.getLogger('ircpuzzles')

import dateutil.parser # pip install dateutil

from puzzle import Puzzle
from channel import Channel

class Game(object):
    def __init__(self, filename):
        """Initialize game, parse definition files into internal structures.

        Args:
           filename (str): Path to the game.json file.
        """
        self.filename = filename
        self.path = os.path.dirname(filename)
        self.puzzles = {}
        self.tracks = []

        self.read_puzzles()
        self.read_game()

    def read_puzzles(self):
        """Read all puzzle files for this game."""
        puzzle_path = join(self.path, 'puzzle')
        for filename in os.listdir(puzzle_path):
            path = join(puzzle_path, filename)
            if isfile(path) and filename.endswith('.json'):
                puzzle = Puzzle(self, path)
                self.puzzles[puzzle.id] = puzzle

    def read_game(self):
        """Read game file."""
        logger.info('reading game definition file: %s', self.filename)
        with open(self.filename) as f:
            parsed = json.load(f)
        self.name = parsed['name']
        # NOTE: make sure timezone information is maintained,
        # 2008-08-12T12:20:30+0200
        self.begin = dateutil.parser.parse(parsed['begin'])
        self.end = dateutil.parser.parse(parsed['end'])
        self.channel_prefix = parsed['channel_prefix']
        for parsed_track in parsed['tracks']:
            self.tracks.append(Track(self, parsed_track))
        self.lobby = Channel(self.prefix_channel(parsed['lobby']['channel']),
            parsed['lobby']['topic'])

    def prefix_channel(self, channel):
        return self.channel_prefix + channel

class Track(object):
    def __init__(self, game, parsed_track):

        self.channel = []
        self.puzzles = []
        for puzzle_id in parsed_track['puzzles']:
            if puzzle_id in game.puzzles:
                self.puzzles.append(game.puzzles[puzzle_id])
            else:
                logger.warn('puzzle for track not found: %s', puzzle_id)

        self.channel = []
        for i in xrange(0, len(self.puzzles)):
            # the channel name is the correct solution 
            # of the previous level:
            if i == 0: # start channel (without a solution to put in the name)
                name = game.prefix_channel(parsed_track['start']['channel'])
            else:
                name = self.puzzles[i-1].get_correct_channel_name()

            topic = self.puzzles[i].get_topic()

            self.channel.append(Channel(name, topic))

        # append the finish channel:
        self.channel.append(Channel(self.puzzles[-1].get_correct_channel_name(),
                parsed_track['finish']['topic']))

        # generate channel for incorrect solutions:
        self.incorrect_channel = []
        for puzzle in self.puzzles:
            self.incorrect_channel += puzzle.get_incorrect_channel()

    def get_start(self):
        return self.channel[0]

    def get_finish(self):
        return self.channel[-1]

if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    # usage example:
    ########################################

    # from local.challenge import Game

    game = Game('example/game.json')

    # to access tracks:
    print len(game.tracks) #> 2
    first_track = game.tracks[0]
    print len(first_track.channel) #> list of all (correct) channels in this track

    # get tracks:
    for chan in game.tracks[0].channel:
        print '%s || %s' % (chan.name, chan.topic)
    print
    for chan in game.tracks[0].incorrect_channel:
        print '%s || %s' % (chan.name, chan.topic)
    print
    for chan in game.tracks[1].channel:
        print '%s || %s' % (chan.name, chan.topic)
    print
    for chan in game.tracks[1].incorrect_channel:
        print '%s || %s' % (chan.name, chan.topic)

    # get lobby channel
    #lobby = game.getLobby()
    #print lobby.name # => "####_TEST_LOBBY"
    #print lobby.topic # => "Choose your path: join #first_path or #second_path to begin."

