__author__ = 'dougnappier'

import phue
from wirelesslights import WirelessLights
import sys
sys.path.insert(0, 'hue-python-rgb-converter')
from rgb_cie import Converter
import colorsys
from colorweave import palette
from wirelesslights import WirelessLights

class LightManager(object):
    """
    sets hue and limitlessled lights to match dominant
    colors of an image. Also filters out the difficult colors
    """

    def convert_color(self, color_str):
        r = int(color_str[:2], 16)/255.0
        g = int(color_str[2:4], 16)/255.0
        b = int(color_str[4:6], 16)/255.0

        hsv = colorsys.rgb_to_hls(r, g, b)
        hsv = [int(round(hsv[0] *360)), int(round(hsv[1] * 100)), int(round(hsv[2]))]
        print('r:%d g:%d b:%d convert to h:%d l:%s s:%s' % (r, g, b, hsv[0], hsv[1], hsv[2]))
        return hsv

    def _filter_colors(self, color_dict, skip_colors=[]):
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
            elif color_dict[keys[index_col]] in skip_colors:
                if save_for_later == -1:
                    save_for_later = index_col
                index_col += 1
            else:
                return keys[index_col], color_dict[keys[index_col]]

            if index_col == total_colors:
                color_selected = True

        return keys[save_for_later], color_dict[keys[save_for_later]]

    def _get_hue_lights(self, lights_list):
        lights = self.hue_bridge.get_light_objects('list')
        for light_name in lights_list:
            for light in lights:
                if light.name.lower().replace(' ', '') == light_name.lower().replace(' ', ''):
                    self.hue_lights.append(light)

    def __init__(self, ip_address, hue_lights=None, limitlessled_groups=None):
        # setup and connect to Hue bridge
        self.limitless_groups = []
        self.hue_lights = []
        self.lights = []
        if hue_lights:
            b = phue.Bridge(ip_address)
            b.connect()
            self.hue_bridge = b
            self._get_hue_lights(hue_lights)

        if limitlessled_groups:
            for group in limitlessled_groups:
                w = WirelessLights(group)
                self.limitless_groups.append(w)

        self.lights = self.hue_lights + self.limitless_groups

    def set_lights(self, color, brightness_percent=100):
        for light in self.lights:
            self.set_light_color(light, color)
            if type(light) is phue.Light:
                light.brightness = int((brightness_percent / 100.0) * 254)
            elif type(light) is WirelessLights:
                light.setBrightness(brightness_percent)

    def set_light_color(self, light, color):
        color_converter = Converter()
        if type(light) is phue.Light:
            light.on = True
            if type(color) is list:
                light.xy = color
            else:
                light.xy = color_converter.hexToCIE1931(color)
            light.brightness = 254
        elif type(light) is WirelessLights:
            light.on()
            if type(color) is list:
                # limitless can't handle this
                light.white()
            elif type(color) is int:
                light.setColorInt(color)
            else:
                light.setColorHSL(self.convert_color(color))
            light.setBrightness(100)

    def set_color_dominant_colors(self, url):
        dominant_colors_dict = (palette(url=url, format='css3', n=10))
        print dominant_colors_dict

        skip_list = []
        for light in self.lights:
            color_str, name = self._filter_colors(dominant_colors_dict, skip_colors=skip_list)
            print('Changing light to color to %s' % name)
            skip_list.append(name)
            # the hex string has # in front but that messes up everything
            self.set_light_color(light, color_str[1:])