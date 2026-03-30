# -*- coding: utf-8 -*-
import sys

if sys.version_info[0] >= 3:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
else:
    from urllib2 import Request, urlopen, URLError


def download_url(url):
    """Download content from URL"""
    try:
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        response = urlopen(req, timeout=30)
        
        if sys.version_info[0] >= 3:
            content = response.read().decode('utf-8')
        else:
            content = response.read()
        
        return content
    except URLError as e:
        return None
    except Exception as e:
        return None


def get_subtitle_language(lang_code):
    """Map language codes"""
    lang_map = {
        'et': 'et',
        'en': 'en',
        'ru': 'ru',
        'VA': 'et'  # Estonian subtitles code
    }
    return lang_map.get(lang_code, 'et')
