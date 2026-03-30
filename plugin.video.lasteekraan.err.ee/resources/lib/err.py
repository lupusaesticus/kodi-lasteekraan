# -*- coding: utf-8 -*-
# Helper functions for ERR services


def get_subtitle_language(setting_value):
    """Map subtitle language setting to language code"""
    lang_map = {
        'et': 'et',
        'en': 'en', 
        'ru': 'ru'
    }
    return lang_map.get(setting_value, 'et')
