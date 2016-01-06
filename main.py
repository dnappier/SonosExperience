__author__ = 'dougnappier'

import pylast
#import soco
#from sonosmanager import SonosManager
#import pychromecast
import time
#from colorweave import palette
#from rgb_cie import Converter
#import phue
import traceback
#import colorsys
#from wirelesslights import WirelessLights

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

# # find the sonos system and pick the highest priority room
# sonos = SonosManager(['Living Room', 'Kitchen'])

# network = setupLastFm()
# cast = setupChromecast()
# castViewer = cast.media_controller
# track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}
# b = setupHue()
# active_hue_lights = b.lights
# duration = ''
# failed_album_artwork = False
# is_paused = True
# while 1:
#     # get the current album is being played in currently selected sonos speaker
#     track = sonos.wait_for_next_track()
#     if not sonos.get_paused_state():
#         if ' (' in track['title']:
#             # this is usually a featuring, which lastfm doesn't like
#             # so we strip off from that space to the end of the string
#             title = track['title'][:track['title'].index(' (')]
#         else:
#             title = track['title']
#         # get the album information for this track
#         album = pylast.Album(track['artist'], title, network)

#         print('New Track by: %s, song is %s' % (track['artist'], track['title']))
#         # get the coverimage url for the album
#         # make sure its a valid album
#         if len(title) > 0:
#             try:
#                 if not track['album_art']:
#                     coverImage = album.get_cover_image()
#                 else:
#                     coverImage = track['album_art']

#             except pylast.WSError:
#                 coverImage = None
#                 print("can't find album details for %(title)s by %(artist)s" % track)
#             except:
#                 # usually this is an add in our music stream
#                 print('unknown failure')
#                 print(track)
#                 traceback.print_exc()
#                 continue
#         else:
#             print('error: no title')
#             continue

#         trying_to_find_image = True
#         while trying_to_find_image:
#             if coverImage:
#                 dominant_colors_dict = (palette(url=coverImage, format='css3', n=10))
#                 print dominant_colors_dict
#                 dominant_colors = dominant_colors_dict.keys()
#                 castViewer.play_media(coverImage, coverImage[coverImage[-5:].index('.'):])
#                 print('Casting image %s' % coverImage)
#                 trying_to_find_image = False
#                 index = 0
#                 for light in active_hue_lights:
#                     color_str, name = filterColors(dominant_colors_dict)
#                     print('Changing Hue color to %s' % name)
#                     light.xy = color_str
#                     light.on = True
#                     light.brightness = 254
#                     index += 1
#             # we didn't get a valid cover image so now lets get the band image
#             else:
#                 # print("failed album: %s " % album.get_url())
#                 print("Attempted Album name is %(album)s" % track)
#                 failed_album_artwork = True
#                 print('we will try to get the artist artwork now')
#                 artist = network.get_artist(track['artist'])
#                 coverImage = artist.get_cover_image()

#     # This means we are paused or just not playing anything
#     else:
#         # check if progress is being made in the song
#         if castViewer:
#             for light in active_hue_lights:
#                 light.xy = color_str
#                 light.on = True
#                 light.brightness = 127
#             castViewer.stop()
#             cast.quit_app()
#             castViewer = None
#             is_paused = True

#         # if we were paused but are now moving forward
#         if is_paused:
#             # This means the play button was pressed
#             cast = setupChromecast()
#             castViewer = cast.media_controller
#             # make sure everything gets setup next time
#             track = {'title': 'NA', 'artist': 'NA', 'album': 'NA'}

