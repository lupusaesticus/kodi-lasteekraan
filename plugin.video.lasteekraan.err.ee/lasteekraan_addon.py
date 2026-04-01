# -*- coding: utf-8 -*-
import json
import locale
import os
import sys
import urllib.request

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

import inputstreamhelper
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    locale.setlocale(locale.LC_ALL, 'et_EE.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')

# Setup
ADDON = xbmcaddon.Addon(id='plugin.video.lasteekraan.err.ee')
KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
DRM = 'com.widevine.alpha'
is_helper = inputstreamhelper.Helper('mpd', drm=DRM)

# define category ID specific icons
CATEGORY_ICONS = {
    'multikad': 'multikad.png',
}


def download_url(url):
    """Core fetcher for the ERR API."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        xbmc.log(f"[Lasteekraan] Network Error: {e} | URL: {url}", xbmc.LOGERROR)
        return None


class LasteekraanException(Exception):
    pass


class Lasteekraan(object):

    def __init__(self, handle=None, path=None):
        self.handle = handle if handle is not None else 1
        self.path = path if path is not None else "plugin://plugin.video.lasteekraan.err.ee/"
        
        self.addon = xbmcaddon.Addon()
        self.fanart = os.path.join(self.addon.getAddonInfo('path'), 'resources', 'fanart.jpg')
        self.logo = os.path.join(self.addon.getAddonInfo('path'), 'resources', 'logo.png')
        
    def list_categories(self):

        url = 'https://services.err.ee/api/v2/category/getByUrl?url=vaata-ja-kuula&domain=lasteekraan.err.ee&page=web'
        html = download_url(url)
        if not html: return []

        data = json.loads(html)
        items = []
        slugs = []

        blacklist = ['minulasteekraan', 'voistlused', '1608952901', '1608964987', '1608953698', 'ajakiri-taheke', 'mangud', '1038081', '1608957599']
        title_blacklist = ['Viimati lisatud multikad', 'Viimati lisatud saated ja filmid']

        try:
            sections = data.get('data', {}).get('category', {}).get('frontPage', [])
            for section in sections:
                title = section.get('header')
                slug = section.get('headerUrl', '').strip('/')
                
                if not slug or slug in blacklist or slug.startswith('http'):
                    continue
                if title in title_blacklist:
                    continue
                
                if title and slug:
                    item = xbmcgui.ListItem(title)
                    icon_file = CATEGORY_ICONS.get(slug, 'logo.png')
                    icon_path = os.path.join(self.addon.getAddonInfo('path'), 'resources', icon_file)
                    item.setArt({'icon': icon_path, 'thumb': icon_path})
                   # item.setArt({'icon': self.logo, 'thumb': self.logo})
                    items.append((f"{self.path}?action=browse&category_id={slug}", item, True))
                    slugs.append(slug)

                    
        except Exception as e:
            xbmc.log(f"[Lasteekraan] Category Parse Error: {e}", xbmc.LOGERROR)

        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)
        return slugs

    def browse_shows(self, category_id):
        xbmcplugin.setContent(self.handle, 'tvshows')
        url = f'https://services.err.ee/api/v2/category/getByUrl?url={category_id}&domain=lasteekraan.err.ee&page=web'
        html = download_url(url)
        if not html: return []

        data = json.loads(html)
        items, show_ids = [], []
        try:
            category_items = data.get('data', {}).get('category', {}).get('items', [])
            for show in category_items:
                title, s_id, s_type = show.get('heading'), show.get('id'), show.get('type')
                
                # Get specific URLs
                v_url = self._get_best_thumb(show, mode='vertical')
                h_url = self._get_best_thumb(show, mode='horizontal')

                # Ensure the poster isn't empty if v_url failed
                poster = v_url if v_url else (h_url if h_url else self.fanart)
                landscape = h_url if h_url else (v_url if v_url else self.fanart)

                item = xbmcgui.ListItem(title)
                
                # Apply to Kodi
                item.setArt({
                    'poster': poster,    # Vertical .png
                    'icon': poster,      # Vertical .png
                    'thumb': landscape,  # Horizontal .jpg
                    'fanart': landscape  # Horizontal .jpg
                })

                action = "watch&contentId" if s_type in ['movie', 'video'] else "series&seriesId"
                is_folder = s_type not in ['movie', 'video']
                
                if not is_folder:
                    item.setProperty('IsPlayable', 'true')

                items.append((f"{self.path}?action={action}={s_id}", item, is_folder))
                show_ids.append(s_id)
        except Exception as e:
            xbmc.log(f"[Lasteekraan] Browse Error: {e}", xbmc.LOGERROR)

        # sort
        items.sort(key=lambda x: x[1].getLabel())
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)
        return show_ids
    
    def browse_season(self, season_id):
        xbmcplugin.setContent(self.handle, 'episodes')
        url = f"https://services.err.ee/api/v2/vodContent/getContentPageData?contentId={season_id}&page=web"
        response = download_url(url)
        if not response: return

        data = json.loads(response).get('data', {})
        items = []
        
        season_data = data.get('seasonList', {})
        seasons = season_data.get('items', []) if isinstance(season_data, dict) else []
        
        active_episodes = []
        for s in seasons:
            if s.get('contents'):
                active_episodes = s.get('contents')
                break

        if not active_episodes:
            active_episodes = data.get('mainContent', {}).get('contents', [])

        main = data.get('mainContent', {})
        root_thumb = self._get_best_thumb(main, mode='horizontal')

        for ep in active_episodes:
            self._add_video_item(items, ep, fallback_thumb=root_thumb)

        # sort
        items.sort(key=lambda x: x[1].getLabel())
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def list_series_episodes(self, series_id):
        url = f'https://services.err.ee/api/v2/vodContent/getContentPageData?contentId={series_id}&page=web'
        response = download_url(url)
        if not response: return

        data = json.loads(response).get('data', {})
        items = []
        main = data.get('mainContent', {})
      

        season_data = data.get('seasonList')
        seasons = season_data.get('items', []) if isinstance(season_data, dict) else []

        if len(seasons) > 1:
            xbmcplugin.setContent(self.handle, 'seasons')
            seasons.sort(key=lambda s: int(s.get('name', '0')) if str(s.get('name', '0')).isdigit() else 0)
            for season in seasons:
                root_thumb = self._get_best_thumb(main, mode='vertical')
                season_name = season.get('name', 'Unknown')
                s_id = season.get('firstContentId')
                
                url = f"{self.path}?action=browse_season&season_id={s_id}"
              

                item = xbmcgui.ListItem(f"Season {season_name}")
                item.setArt({'thumb': root_thumb, 'fanart': self.fanart})
                items.append((url, item, True))
        else:
            xbmcplugin.setContent(self.handle, 'episodes')
            root_thumb = self._get_best_thumb(main, mode='horizontal')
            ep_list = seasons[0].get('contents', []) if seasons else []
            if not ep_list and main:
                self._add_video_item(items, main, fallback_thumb=root_thumb)
            for ep in ep_list:
                self._add_video_item(items, ep, fallback_thumb=root_thumb)
            items.sort(key=lambda x: x[1].getLabel())

        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def _add_video_item(self, items, data_dict, fallback_thumb=""):
        title = data_dict.get('subHeading') or data_dict.get('heading', 'Unknown')
        
        season = data_dict.get('season')
        season = int(season) if str(season).isdigit() else None

        episode = data_dict.get('episode')
        episode = int(episode) if str(episode).isdigit() else None

        display_label = f"S{season:02d}E{episode:02d} - {title}" if season and isinstance(season, int) else title

        item = xbmcgui.ListItem(display_label)
        
        content_id = data_dict.get('id')
        plot = data_dict.get('lead', '').replace('<p>', '').replace('</p>', '')
        year = int(data_dict.get('year', 0)) if str(data_dict.get('year', '')).isdigit() else 0

        info = {
            'title': title,
            'plot': plot,
            'mediatype': 'episode' if season else 'movie'
        }
        if year: info['year'] = year
        if episode: info['episode'] = episode
            
        item.setInfo('video', info)

        # thumb = self._get_best_thumb(data_dict) or fallback_thumb
        # item.setArt({'thumb': thumb, 'fanart': thumb, 'poster': thumb})

        # Call the helper with the specific parameter
        thumb_v = self._get_best_thumb(data_dict, mode='vertical') or fallback_thumb
        thumb_h = self._get_best_thumb(data_dict, mode='horizontal') or fallback_thumb

        # Map them to the correct Kodi art keys
        item.setArt({
            'poster': thumb_v,   # Vertical
            'icon': thumb_v,     # Vertical fills the square better
            'thumb': thumb_h,    # Horizontal
            'fanart': thumb_h    # Horizontal
        })

        
        item.setProperty('IsPlayable', 'true')
        url = f"{self.path}?action=watch&contentId={content_id}"
        items.append((url, item, False))

    # def _get_best_thumb(self, data_dict):
    #     photos = data_dict.get('photos', [])
    #     if photos:
    #         types = photos[0].get('photoTypes', {})
    #         return types.get('2', {}).get('url') or types.get('48', {}).get('url')
    #     return ""

    def _get_best_thumb(self, data_dict, mode='horizontal'):
        photo_list = data_dict.get('verticalPhotos' if mode == 'vertical' else 'horizontalPhotos', [])
        
        url = ""
        if photo_list and isinstance(photo_list, list):
            url = photo_list[0].get('photoUrlOriginal', "")
        
        if not url:
            generic = data_dict.get('photos', [])
            url = generic[0].get('photoUrlOriginal', "") if generic else ""
                
        return str(url)

    def get_media_location(self, content_id):
        url = f"https://services.err.ee/api/v2/vodContent/getContentPageData?contentId={content_id}"
        response = download_url(url)
        if not response:
            return None, None, None, None

        data = json.loads(response).get('data', {})
        main = data.get('mainContent', {})
        
        # 1. Access the media list (mainContent -> medias)
        medias = main.get('medias', [])
        saade = None
        token = None
        license_server = None

        if medias:
            # Grab the first media entry
            m = medias[0]
            
            # The manifest URLs are inside the 'src' dictionary
            src = m.get('src', {})
            saade = src.get('dashNew') or src.get('dash') or src.get('hls')
            
            # Protocol fix: the JSON uses "//", so we add "https:"
            if saade and saade.startswith('//'):
                saade = 'https:' + saade

            # 2. DRM - The token is in the 'jwt' key
            token = m.get('jwt')
            # The license servers are in 'licenseServerUrl'
            license_urls = m.get('licenseServerUrl', {})
            license_server = license_urls.get('widevine')

            # 3. Subtitles
            subs = []
            raw_subtitles = m.get('subtitles', [])
            
            for s in raw_subtitles:
                s_url = s.get('src', '')
                # Normalizing the URL
                if s_url.startswith('//'):
                    s_url = 'https:' + s_url
                
                # Grabbing the language (srclang)
                s_lang = s.get('srclang', 'et') 
                
                # Append as the tuple your return expects
                subs.append((s_url, s_lang))

        return saade, subs, token, license_server

    def play_stream(self, content_id):
        saade, subs, token, license_server = self.get_media_location(content_id)
        if not saade: 
            return


        # Pre-check manifest accessibility
        # try:
        #     req = urllib.request.Request(saade, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
        #     urllib.request.urlopen(req, timeout=10)
        # except urllib.error.HTTPError as e:
        #     if e.code == 403:
        #         xbmcgui.Dialog().ok('Lasteekraan', 'Error 403: Access Denied (Geoblock Likely)')
        #         xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
        #         return
        # except Exception:
        #     pass  # let ISA handle other errors normally

        #manifest_with_header = f"{saade}|X-AxDRM-Message={token}"
        #item = xbmcgui.ListItem(path=manifest_with_header)

        item = xbmcgui.ListItem(path=saade)
        item.setProperty('inputstream', 'inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        
        # Ensure 'item' is the ListItem you are working with
        if token and license_server:
            item.setContentLookup(False)
            item.setMimeType('application/dash+xml')
            burl = 'https://lasteekraan.err.ee'
            license_key = f"{license_server}|Content-Type=application/octet-stream&X-AxDRM-Message={token}|R{{SSM}}|"

            # Necessary for Kodi 19+ to ensure the addon is triggered
            is_addon = 'inputstream.adaptive'
            if KODI_VERSION_MAJOR >= 19:
                item.setProperty('inputstream', 'inputstream.adaptive')
            else:
                item.setProperty('inputstreamaddon', 'inputstream.adaptive')

           
            # Use 'mpd' for older Kodi or 'dash' for newer; 'mpd' is generally safer
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            item.setProperty('inputstream.adaptive.license_key', license_key)
            

        if subs:
            # Kodi expects a list of URLs and a list of languages
            sub_urls = [s[0] if s[0].startswith('http') else 'https:' + s[0] for s in subs]
            item.setSubtitles(sub_urls)
     

        xbmcplugin.setResolvedUrl(self.handle, True, item)
        
        # Subs off by default regardless of kodi settings - Wait for playback to actually start, then force subs off
        if subs:
            player = xbmc.Player()
            for _ in range(50):  # Wait up to 5 seconds
                if player.isPlayingVideo():
                    player.showSubtitles(False)
                    break
                xbmc.sleep(100)

    def display_error(self, message='n/a'):
        heading = ''
        line1 = ADDON.getLocalizedString(200)
        line2 = ADDON.getLocalizedString(201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    handle = int(sys.argv[1])
    base_url = sys.argv[0]
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    
    # FIX 3: Passed variables in the correct order
    addon = Lasteekraan(handle, base_url)
    action = params.get('action')

    try:
        if not action:
            addon.list_categories()
        elif action == 'all_categories':
            addon.list_all_categories()
        elif action == 'browse':
            addon.browse_shows(params.get('category_id'))
        elif action == 'series':
            addon.list_series_episodes(params.get('seriesId'))
        elif action == 'browse_season':
            # FIX 4: Corrected variable name from season_url to season_id
            addon.browse_season(params.get('season_id'))
        elif action == 'watch':
            addon.play_stream(params.get('contentId'))
            
    except Exception as e:
        xbmcgui.Dialog().notification('Lasteekraan Error', str(e), xbmcgui.NOTIFICATION_ERROR, 5000)