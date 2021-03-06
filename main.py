__author__ = 'dougnappier'

from albummanager import AlbumManager
from sonosmanager import SonosManager
from lightmanager import LightManager
import pychromecast
import time


LASTFM_API_KEY = 'x'
LASTFM_API_SECRET = 'x'
lastfm_username = 'x'
lastfm_password = 'x'
HUE_IP_ADDRESS = '192.168.11.146'
SONOS_SPEAKERS = ['Kitchen', 'Living Room']
USE_CHROMECAST = True
#fill in here with light name or names that you want to use
#HUE_LIGHTS = ['Cabinet Lights', 'Table Bloom']
HUE_LIGHTS = ['Table Bloom']
WHITE = [.3174, .3207]


class ChromecastEmulator(object):
    class MediaControllerEmulator(object):
        def __init__(self):
            pass

        def stop(self):
            return True

        def play_media(self, url, format):
            return True

    def __init__(self):
        self.media_controller = self.MediaControllerEmulator()

    def quit_app(self):
        return True

def setupChromecast(attempts=1000):
    if not USE_CHROMECAST:
        return ChromecastEmulator()
    # setup and connect to the chromecast and return the used cast
    retry = False
    casts = pychromecast.get_chromecasts_as_dict().keys()
    print casts
    if len(casts) > 0:
        cast = pychromecast.get_chromecast(friendly_name=casts[0])
        if cast is None:
            retry = True
    else:
        retry = True

    if retry:
        if not attempts:
            return None
        attempts -= 1
        # If we didn't find any chromecasts then try again
        time.sleep(1)
        print ("Chromecast couldn't be found, %d attempts left" % attempts)
        return setupChromecast(attempts)

    cast.wait()
    return cast

# find the sonos system and pick the highest priority room
sonos = SonosManager(SONOS_SPEAKERS)

album_manager = AlbumManager(LASTFM_API_KEY, LASTFM_API_SECRET,
                            lastfm_username, lastfm_password)

cast = setupChromecast()
castViewer = cast.media_controller
track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
# The 5 used below is for all
light_manager = LightManager(HUE_IP_ADDRESS, hue_lights=HUE_LIGHTS, limitlessled_groups=[5])
duration = ''
failed_album_artwork = False
is_paused = False

while 1:
    # get the current album is being played in currently selected sonos speaker
    track = sonos.wait_for_next_track()
    if not sonos.get_paused_state():
        # if we were paused but are now moving forward
        if is_paused:
            # This means the play button was pressed
            cast = setupChromecast()
            castViewer = cast.media_controller
            # make sure everything gets setup next time
            # track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}

        coverImage = album_manager.get_album_image(**track)
        if coverImage:
            try:
                castViewer.play_media(coverImage, album_manager.get_album_image_format())
            except:
                continue
            print('Casting image %s' % coverImage)
            light_manager.set_color_dominant_colors(coverImage)

    # This means we are paused or just not playing anything
    else:
        # check if progress is being made in the song
        if castViewer:
            light_manager.set_lights(WHITE, 127)

            castViewer.stop()
            cast.quit_app()
            castViewer = None
            is_paused = True



