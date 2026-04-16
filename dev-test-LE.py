print("DEV_TEST.PY IS RUNNING")
import sys
import os
from unittest.mock import MagicMock

# 1. DEFINE FAKE KODI CLASSES
class FakeListItem:
    def __init__(self, label=''):
        self.label = label
        self.art = {}
        self.info = {}
        self.properties = {}

    def getLabel(self):
        return self.label

    # Fix: Make 'key' optional so getArt() returns the whole dict
    def getArt(self, key=None):
        if key:
            return self.art.get(key, '')
        return self.art

    def setArt(self, art_dict):
        self.art.update(art_dict)

    def setInfo(self, info_type, info_labels):
        self.info[info_type] = info_labels

    def setProperty(self, key, value):
        self.properties[key] = value

    def getVideoInfoTag(self):
        class FakeTag:
            def setTitle(self, title): pass
            def setPlot(self, plot): pass
            def setYear(self, year): pass
        return FakeTag()

# 2. MOCK THE KODI SUBSYSTEM
# We must do this BEFORE importing the addon or any Kodi modules
mock_gui = MagicMock()
mock_gui.ListItem = FakeListItem

sys.modules['xbmc'] = MagicMock()
sys.modules['xbmcaddon'] = MagicMock()
sys.modules['xbmcplugin'] = MagicMock()
sys.modules['xbmcgui'] = mock_gui
sys.modules['inputstreamhelper'] = MagicMock()

# Now we can safely import the mocks for use in our test logic
import xbmc, xbmcplugin

# 3. CONFIGURE PATHS
# Finds the absolute path of the 'plugin.video.lasteekraan.err.ee' subfolder
addon_dir = 'plugin.video.lasteekraan.err.ee'
addon_path = os.path.join(os.path.dirname(__file__), addon_dir)
sys.path.append(addon_path)

# 4. IMPORT THE ADDON CLASS
try:
    from lasteekraan_addon import Lasteekraan
    print(f"[+] Successfully imported Lasteekraan from {addon_dir}")
except ImportError as e:
    print(f"[-] Failed to import: {e}")
    sys.exit(1)

# 5. TEST UTILITIES
def print_mock_results(header_text):

    # --- NEW: Catch Errors from xbmc.log ---
    if xbmc.log.called:
        print(f"\n[!] LOG ENTRIES FOUND during {header_text}:")
        for call in xbmc.log.call_args_list:
            msg, level = call[0]
            # Only print if it's an Error or Warning
            if level in [xbmc.LOGERROR, xbmc.LOGWARNING]:
                print(f"    ERROR: {msg}")
        xbmc.log.reset_mock() # Clear logs for next step

    """Inspects the xbmcplugin mock to see what the addon tried to display."""
    if not xbmcplugin.addDirectoryItems.called:
        print(f"  [!] No items were sent to Kodi for: {header_text}")
        return

    print(f"\n{header_text}")
    print("-" * 40)

    # args[1] contains the list of (url, listitem, is_folder)
    args, _ = xbmcplugin.addDirectoryItems.call_args
    items = args[1] 

    for url, listitem, is_folder in items:
        label = listitem.getLabel()
        thumb = listitem.getArt().get('thumb', 'No Thumb')
        print(f"  > {label:<35} | ID: {url.split('=')[-1]}")
     #   print(f"  > {label:<35}  | ID: {url.split('=')[-1]} | {thumb}")
    
    # Clear the mock memory so the next step starts clean
    xbmcplugin.addDirectoryItems.reset_mock()

# 6. EXECUTION
if __name__ == "__main__":
    addon = Lasteekraan()
    print("\n" + "="*50)
    print("STARTING EXTERNAL TEST")
    print("="*50)

   
    # STEP 1: Categories
    slugs = addon.list_categories()
    print_mock_results("[STEP 1] CATEGORIES FOUND")
    
    # STEP 2: Shows
    if slugs:
        test_slug = 'multikad'
        # We need to capture the items to get a real ID for Step 3
        addon.browse_shows(test_slug)
        
        # Get the ID of the first show found to test episodes
        import xbmcplugin
        args, _ = xbmcplugin.addDirectoryItems.call_args
        first_item_url = args[1][0][0] # Get URL of first show: "plugin://...?seriesId=123"
        import urllib.parse
        parsed = urllib.parse.urlparse(first_item_url)
        params = urllib.parse.parse_qs(parsed.query)
       # test_series_id = 1038631# first_item_url.split('seriesId=')[-1] if 'seriesId=' in first_item_url else None

        print_mock_results(f"[STEP 2] SHOWS IN '{test_slug}'")

        # STEP 3: Season List (Hei, Kutsa!)
        test_series_id = 1038631
        addon.list_series_episodes(test_series_id)
        print_mock_results(f"[STEP 3] SEASON LIST FOR ID '{test_series_id}'")

    # STEP 3.1: Season 3 (Active by default with 1038631)
        test_s3_id = 1038631 
        addon.browse_season(test_s3_id)
        print_mock_results(f"[STEP 3.1] EPISODES IN S3")

        # STEP 3.2: Season 4 (Activated by its firstContentId)
        test_s4_id = 1609787687 
        addon.browse_season(test_s4_id)
        print_mock_results(f"[STEP 3.2] EPISODES IN S4")

        # STEP 4: Single Movie (Tigu ja vaal)
        test_movie_id = 1211272
        addon.list_series_episodes(test_movie_id)
        print_mock_results(f"[STEP 4] SINGLE MOVIE FOR ID '{test_movie_id}'")


        print("\n" + "="*50)
        print("STARTING TOKEN EXTRACTION TEST")
        print("="*50)

#   # STEP 5: Get Token and Metadata for a specific Episode
#         test_content_id = "1609163321" 

#         print(f"\n[TESTING EXTRACTION] Content ID: {test_content_id}")
#         print("-" * 40)
        
#         try:
#             # Capturing the full return from your get_media_location method
#             result = addon.get_media_location(test_content_id)
            
#             if result:
#                 url, subs, token, license_server = result
                
#                 print(f"  > Stream URL:    {url}")
#                 print(f"  > Subtitles:     {subs if subs else 'None found'}")
#                 print(f"  > License SRV:   {license_server}")
#                 print(f"  > Token (JWT):   {token[:50]}...[truncated]") # Prints start of token
                
#                 if token and license_server:
#                     print("\n[+] VALIDATION: Both Token and License Server present.")
#             else:
#                 print("  [!] FAILED: get_media_location returned None.")

#         except Exception as e:
#             print(f"  [!] ERROR during extraction: {str(e)}")
            
#         # STEP 6: Simulate Kodi's license_key construction
#         print("="*50)
#         print("STEP 6: KODI LICENSE KEY CONSTRUCTION")
#         print("="*50)
        
#         if token and license_server:
#             # This mirrors the exact logic in your play_stream function
#             # Format: LicenseURL | Headers | Challenge | Flags
#             # Note: We use .format or f-string with double braces for {{SSM}}
            
#             headers = f"X-AxDRM-Message={token}"
#             challenge = "R{SSM}" # Literal string Kodi expects
            
#             # The final string sent to item.setProperty()
#             constructed_key = f"{license_server}|{headers}|{challenge}|"
            
#             print(f"CONSTRUCTED KEY:\n{constructed_key}\n")
            
#             # Validation Checks
#             parts = constructed_key.split('|')
#             print(f"Pipe count: {len(parts) - 1} (Should be 3 or 4)")
#             print(f"Header check: {'OK' if 'X-AxDRM-Message=' in constructed_key else 'FAIL'}")
#             print(f"SSM check: {'OK' if '{SSM}' in constructed_key else 'FAIL'}")
#         else:
#             print("SKIP: Missing token or license_server for construction.")

