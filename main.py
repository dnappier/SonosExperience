__author__ = 'dougnappier'

import pylast
import soco
import pychromecast
import time
from colorweave import palette
from rgb_cie import Converter
import phue
import traceback
import colorsys
from wirelesslights import WirelessLights

LASTFM_API_KEY = 'xxxxxxxxxx'
LASTFM_API_SECRET = 'xxxxxxxx'
lastfm_username = 'xxxxxxxxx'
lastfm_password = 'xxxxxxxxxxx'
HUE_IP_ADDRESS = '192.168.1.1'
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


def setupLastFm():
    # setup and connect the last fm servers
    password_hash = pylast.md5(lastfm_password)
    return pylast.LastFMNetwork(api_key=LASTFM_API_KEY, api_secret=LASTFM_API_SECRET,
                                username=lastfm_username, password_hash=password_hash)


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


activeZone = None
activeZoneIndex = -1
zones = list(soco.discover())

for zone in zones:
    activeZoneIndex += 1
    if 'livingroom' in zone.player_name.lower().replace(' ', ''):
        activeZone = zone


def get_new_active_zone(available_zones):
    new_index = 0
    for zone in available_zones:
        current_track = zone.get_current_track_info()
        if current_track['title'] != '' and current_track['artist'] != '':
            return zone, new_index
        new_index += 1
    return None, -1

print ("The sonos room to be used is %s" % activeZone.player_name)

network = setupLastFm()
cast = setupChromecast()
castViewer = cast.media_controller
track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
b = setupHue()
active_hue_lights = b.lights
duration = ''
failed_album_artwork = False
is_paused = True
while 1:
    # get the current album being played
    if activeZone:
        trackNew = activeZone.get_current_track_info()

    if trackNew['title'] != track['title'] or trackNew['artist'] != track['artist'] or trackNew['album'] != track['album']:
        is_paused = False
        track = trackNew
        if ' (' in track['title']:
            # this is usually a featuring, which lastfm doesn't like
            # so we strip off from that space to the end of the string
            title = track['title'][:track['title'].index(' (')]
        else:
            title = track['title']
        album = pylast.Album(track['artist'], title, network)

        print('New Track by: %s, song is %s' % (track['artist'], track['title']))
        if len(title) > 0:
            try:
                coverImage = album.get_cover_image()
            except pylast.WSError:
                coverImage = None
                print("can't find album details for %(title)s by %(artist)s" % track)
            except:
                # usually this is an add in our music stream
                if track['title'] == ' ':
                    continue

                print('unknown failure')
                print(track)
                traceback.print_exc()
                continue
        else:
            print('error: no title')
            activeZone, activeZoneIndex = get_new_active_zone(zones)
            continue
        trying_to_find_image = True
        while trying_to_find_image:
            if coverImage:
                dominant_colors_dict = (palette(url=coverImage, format='css3', n=10))
                print dominant_colors_dict
                dominant_colors = dominant_colors_dict.keys()
                castViewer.play_media(coverImage, 'png')
                print('Casting image %s' % coverImage)
                trying_to_find_image = False
                index = 0
                for light in active_hue_lights:
                    color_str, name = filterColors(dominant_colors_dict)
                    print('Changing Hue color to %s' % name)
                    light.xy = color_str
                    light.on = True
                    light.brightness = 254
                    print('hue %f' %light.hue)
                    print('saturation %f' %light.saturation)
                    index += 1
            else:
                print("failed album: %s " % album.get_url())
                print("Attempted Album name is %(album)s" % track)
                failed_album_artwork = True
                print('we will try to get the artist artwork now')
                artist = network.get_artist(track['artist'])
                coverImage = artist.get_cover_image()
    else:
        # check if progress is being made in the song
        if trackNew['position'] == duration:
            is_paused = True
            if castViewer:
                for light in active_hue_lights:
                    light.xy = color_str
                    light.on = True
                    light.brightness = 127
                castViewer.stop()
                cast.quit_app()
                castViewer = None
        elif is_paused:
            # This means the play button was pressed
            cast = setupChromecast()
            castViewer = cast.media_controller
            # make sure everything gets setup next time
            track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
    time.sleep(1.01)
    duration = trackNew['position']
