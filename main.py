__author__ = 'dougnappier'

from albummanager import AlbumManager
import soco
from sonosmanager import SonosManager
import pychromecast
import time
from colorweave import palette
import sys
sys.path.insert(0, 'hue-python-rgb-converter')
from rgb_cie import Converter
import phue
import colorsys
from wirelesslights import WirelessLights

LASTFM_API_KEY = 'f6c7a0a15aa64042bfe5367784e120cb'
LASTFM_API_SECRET = '93de2dd7a2d0b009c966f12b81935b7b'
lastfm_username = 'dnappier'
lastfm_password = 'Reyron!120'
HUE_IP_ADDRESS = '192.168.11.146'
WHITE = [.3174, .3207]

active_hue_lights = []

def convertColor(color_str):
    r = int(color_str[:2], 16)/255.0
    g = int(color_str[2:4], 16)/255.0
    b = int(color_str[4:6], 16)/255.0

    hsv = colorsys.rgb_to_hls(r, g, b)
    hsv = [int(round(hsv[0] *360)), int(round(hsv[1] * 100)), int(round(hsv[2]))]
    print('r:%d g:%d b:%d convert to h:%d l:%s s:%s' % (r, g, b, hsv[0], hsv[1], hsv[2]))
    return hsv

def filterColors(color_dict):
    # scan through available colors and look for something not black or grey
    # return a grey if we must though
    color_converter = Converter()
    color_selected = False
    index_col = 0
    keys = color_dict.keys()
    total_colors = len(keys)
    save_for_later = -1
    while not color_selected:
        if 'tan'in color_dict[keys[index_col]]:
            if save_for_later == -1:
                save_for_later = index_col
            index_col += 1
        elif 'brown' in color_dict[keys[index_col]]:
            if save_for_later == -1:
                save_for_later = index_col
            index_col += 1
        elif 'white' in color_dict[keys[index_col]]:
            if save_for_later == -1:
                save_for_later = index_col
            index_col += 1
        elif 'black' in color_dict[keys[index_col]]:
            if save_for_later == -1:
                save_for_later = index_col
            index_col += 1
        elif 'grey' in color_dict[keys[index_col]] or 'gray' in color_dict[keys[index_col]]:
            if save_for_later == -1:
                save_for_later = index_col
            index_col += 1
        else:
            convertColor(keys[index_col][1:])
            return color_converter.hexToCIE1931(keys[index_col][1:]), color_dict[keys[index_col]]

        if index_col == total_colors:
            color_selected = True

    convertColor(keys[save_for_later][1:])
    return color_converter.hexToCIE1931(keys[save_for_later][1:]), color_dict[keys[save_for_later]]

def setupHue():
    # setup and connect to Hue bridge
    b = phue.Bridge(HUE_IP_ADDRESS)
    b.connect()
    return b

def setupChromecast(attempts=1000):
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
sonos = SonosManager(['Living Room', 'Kitchen'])

album_manager = AlbumManager(LASTFM_API_KEY, LASTFM_API_SECRET,
                            lastfm_username, lastfm_password)

cast = setupChromecast()
castViewer = cast.media_controller
track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
b = setupHue()
active_hue_lights = b.lights
duration = ''
failed_album_artwork = False
is_paused = True

while 1:
    # get the current album is being played in currently selected sonos speaker
    track = sonos.wait_for_next_track()
    if not sonos.get_paused_state():
        coverImage = album_manager.get_album_image(**track)

        if coverImage:
            dominant_colors_dict = (palette(url=coverImage, format='css3', n=10))
            print dominant_colors_dict
            dominant_colors = dominant_colors_dict.keys()
            castViewer.play_media(coverImage, album_manager.get_album_image_format())
            print('Casting image %s' % coverImage)

            for light in active_hue_lights:
                color_str, name = filterColors(dominant_colors_dict)
                print('Changing Hue color to %s' % name)
                light.xy = color_str
                light.on = True
                light.brightness = 254

    # This means we are paused or just not playing anything
    else:
        # check if progress is being made in the song
        if castViewer:
            for light in active_hue_lights:
                light.xy = color_str
                light.on = True
                light.brightness = 127
            castViewer.stop()
            cast.quit_app()
            castViewer = None
            is_paused = True

        # if we were paused but are now moving forward
        if is_paused:
            # This means the play button was pressed
            cast = setupChromecast()
            castViewer = cast.media_controller
            # make sure everything gets setup next time
            track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}

