from os import path
import threading
import requests
import time
import logging
import sys
import re

from lxml import html
from utils.text import millify
from utils.text import trim_string, visual_ljust, visual_rjust

logger = logging.getLogger(__name__)
if __debug__ and not hasattr(sys, 'frozen'):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class MotdUpdater(threading.Thread):

    def __init__(self, server, scoreboard_type):
        self.server = server

        self.scoreboard_type = scoreboard_type
        self.time_interval = 5 * 60
        self.motd = self.load_motd()

        threading.Thread.__init__(self)
    
    def run(self):
        while True:
            self.server.write_all_players()
            try:
                motd_payload = self.get_configuration()
            except requests.exceptions.RequestException:
                continue

            motd = self.render_motd(self.motd)
            motd_payload['ServerMOTD'] = motd.encode("iso-8859-1", "ignore")

            try:
                self.submit_motd(motd_payload)
            except requests.exceptions.RequestException:
                continue

            time.sleep(self.time_interval)

    def submit_motd(self, payload):
        motd_url = "http://" + self.server.address + \
                   "/ServerAdmin/settings/welcome"

        logger.debug("Updating MOTD ({})".format(self.server.name))
        try:
            self.server.session.post(motd_url, data=payload)
            self.server.save_settings()
        except requests.exceptions.RequestException:
            logger.warning("Couldn't submit motd (RequestException) to {}"
                           .format(self.server.name))
            raise

    def load_motd(self):
        if not path.exists(self.server.name + ".motd"):
            logger.warning("No motd file for " + self.server.name)
            return ""
 
        motd_f = open(self.server.name + ".motd")
        motd = motd_f.read()
        motd_f.close()
        return motd

    def render_motd(self, src_motd):
        if self.scoreboard_type in ['kills', 'Kills', 'kill', 'Kill']:
            scores = self.server.database.top_kills()
        elif self.scoreboard_type in ['Dosh','dosh']:
            scores = self.server.database.top_dosh()
        elif self.scoreboard_type in ['KD', 'kd']:
            scores = self.server.database.top_kd()
        elif self.scoreboard_type in ['Multi', 'multi']:
            return self.render_motd_multi(src_motd)
        else:
            logger.error("Bad configuration, scoreboard_type. "
                         "Options are: dosh, kills ({})"
                         .format(self.server.name))
            return

        for player in scores:
            name = player[0].replace("<", "&lt;")
            name = trim_string(name, 12)
            score = player[1]

            src_motd = src_motd.replace("%PLR", name, 1)
            src_motd = src_motd.replace("%SCR", millify(score), 1)

        if "%SRV_K" in src_motd:
            server_kills = self.server.database.server_kills()
            src_motd = src_motd.replace("%SRV_K", millify(server_kills), 1)

        if "%SRV_D" in src_motd:
            server_dosh = self.server.database.server_dosh()
            src_motd = src_motd.replace("%SRV_D", millify(server_dosh), 1)

        return src_motd

    def render_motd_multi(self, src_motd):
        top_kills = self.server.database.top_kills()
        top_dosh = self.server.database.top_dosh()
        top_kd = self.server.database.top_kd()
        
        for m in re.finditer('%(\w+)\[(\d+)\]\.(\w+)(?::([<>])?(\d+))?%', src_motd):
            player = {
                'kills': top_kills,
                'dosh': top_dosh,
                'kd': top_kd
            }.get(m.group(1), ['', 0])[int(m.group(2))]
            
            replacement = {
                'name': player[0].replace("<", "&lt;"),
                'score': '{0}'.format(player[1])
            }.get(m.group(3), [''])
            
            if (m.group(5)):
                replacement = {
                    '<': visual_ljust(replacement, int(m.group(5))),
                    None: visual_ljust(replacement, int(m.group(5))),
                    '>': visual_rjust(replacement, int(m.group(5)))
                }.get(m.group(4))
            
            src_motd = src_motd.replace(m.group(0), replacement);
        
        if "%SRV_K" in src_motd:
            server_kills = self.server.database.server_kills()
            src_motd = src_motd.replace("%SRV_K", millify(server_kills), 1)

        if "%SRV_D" in src_motd:
            server_dosh = self.server.database.server_dosh()
            src_motd = src_motd.replace("%SRV_D", millify(server_dosh), 1)
        
        return src_motd

    def get_configuration(self):
        motd_url = "http://" + self.server.address + \
                   "/ServerAdmin/settings/welcome"

        try:
            motd_response = self.server.session.get(motd_url, timeout=2)
        except requests.exceptions.RequestException as e:
            logger.debug("Couldn't get motd config(RequestException)")
            raise

        motd_tree = html.fromstring(motd_response.content)

        banner_link = motd_tree.xpath('//input[@name="BannerLink"]/@value')[0] 
        web_link = motd_tree.xpath('//input[@name="WebLink"]/@value')[0]
        motto = motd_tree.xpath('//textarea[@name="ClanMotto"]')[0].text

        return {
                'BannerLink': banner_link,
                'ClanMotto': motto,
                'ClanMottoColor': '#FF0000',
                'ServerMOTDColor': '#FF0000',
                'WebLink': web_link,
                'WebLinkColor': '#FF0000',
                'liveAdjust': '1',
                'action': 'save'
        }

