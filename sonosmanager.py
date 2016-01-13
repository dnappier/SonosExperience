import soco
import time

class NoZonesException(Exception):
    def __init__(self, message, errors=None):
        super(RuntimeError, self).__init__(message)
        self.errors = errors

class SonosManager(object):
    '''
    This is the class that manages all of the sonos speakers and abstracts
    tracking speaker and song states
    '''
    # poll duration is amount of time to sleep
    POLL_DURATION = .2
    # paused count * sleep duration is how long we let passed without noticeable
    # progress in song before marked as paused
    PAUSED_COUNT = 6
    def __init__(self, priority_table):
        """
        The Expected Priority table is a list with highest priority room first,
        space and capital letters will be removed during parsing
        """
        self.zones = list(soco.discover())

        if len(self.zones) == 0:
            raise NoZonesException("There are no available zones on this network")

        self.priority_table = priority_table
        # this is just an arbitrary selection for the moment
        self.active_zone = self.zones[0]
        self.active_zone = self._find_highest_priority_active_room()
        self._is_paused = False
        self.track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
        print (self.track)

    def get_current_track(self):
        return self.active_zone.get_current_track_info()

    def get_new_active_zone(self):
        zone_save = self.active_zone
        for i in range(len(self.priority_table)):
            zone = self._find_highest_priority_active_room(skip_current=True,
                                                           priority_table=self.priority_table[i:])
            track = zone.get_current_track_info()
            if len(track['title']) > 0:
                self.active_zone = zone
                return zone

        self.active_zone = zone_save
        print("Sonos Manager: switching to %s" % zone_save.player_name)
        return zone_save

    def get_paused_state(self):
        return self._is_paused

    def _find_highest_priority_active_room(self, skip_current=False, priority_table=None):
        if not priority_table:
            priority_table = self.priority_table

        for room in priority_table:
            for zone in self.zones:
                # get a different sonos zone then the current one
                # If we want a DIFFERENT zone then continue past the current one
                if skip_current and zone.player_name == self.active_zone.player_name:
                    continue
                if room.lower().replace(' ', '') == zone.player_name.lower().replace(' ', ''):
                    return zone

        # if we never found a new one
        return self.active_zone

    def wait_for_next_track(self):
        waiting = True
        is_paused_count = 0
        position = '0'
        while waiting:
            track = self.get_current_track()
            if len(track['title']) == 0:
                self.get_new_active_zone()
                # print('Error no title for this song, probably not playing')
            # check if this is an add
            elif track['title'] == ' ':
                self.get_new_active_zone()
            # this means a new song is playing
            elif track['title'] != self.track['title'] \
                or track['artist'] != self.track['artist'] \
                    or track['album'] != self.track['album']:
                self.track = track
                duration = track['duration']
                print ("New Song '%(title)s' by %(artist)s on album '%(album)s'" % track)
                self._is_paused = False
                return self.track
            # check to see if we are currently paused
            elif track['position'] == position:
                # return None if paused or nothing playing
                # if we have gone over a second with noticable progress
                if is_paused_count == self.PAUSED_COUNT:
                    self._is_paused = True
                    is_paused_count = 0
                    return {'paused': True}

                else:
                    is_paused_count += 1
            # same song, still playing
            else:
                is_paused_count = 0

            position = track['position']
            time.sleep(self.POLL_DURATION)
