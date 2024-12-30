"""
steam_queue_creator.py
Creates Steam Super Packer queues with rate limiting.
Requires settings.json and language.txt in the same directory.
"""

import requests
import re
import time
import os
import json
from datetime import datetime
from pathlib import Path

class SteamGameProcessor:
    def __init__(self):
        """Initialize processor and settings"""
        self.settings = self._load_settings()
        self.enable_logging = self.settings['operation']['enable_logging']
        self.log_path = Path(self.settings['files']['log_file'])
        self.strings = self._load_languages()
        self._setup_logging()
        self.existing_games = self._get_existing_games()
        self.platforms = self.settings['platforms']
        self.last_request_time = 0
        self._display_header()

    def _load_settings(self):
        """Load settings from settings.json"""
        try:
            if not os.path.exists('settings.json'):
                print("Error: settings.json not found!")
                exit(1)
            with open('settings.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            exit(1)

    def _load_languages(self):
        """Load language strings from language.txt"""
        try:
            if not os.path.exists('language.txt'):
                print("Warning: language.txt not found, using English")
                return self._get_default_english()

            languages = {}
            with open('language.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        lang, key, value = line.split('|', 2)
                        if lang not in languages:
                            languages[lang] = {}
                        languages[lang][key] = value

            return languages.get(self.settings['operation']['display_language'], languages['english'])
        except Exception as e:
            print(f"Error loading languages: {e}")
            return self._get_default_english()

    def _get_default_english(self):
        """Return default English strings"""
        return {
            "header_title": "SUPER STEAM PACKER QUEUE CREATOR",
            "platforms_title": "TARGET PLATFORMS",
            "start_processing": "Starting Steam game processing...",
            "fetching_software": "Fetching software list...",
            "fetching_games": "Fetching games list...",
            "found_games": "Found {} games in Steam library",
            "processing_ready": "Ready to process {} games...",
            "estimated_time": "Estimated completion time: {} (HH:MM:SS)",
            "press_enter": "Press Enter to start processing (This will take some time)",
            "test_mode_limit": "Test mode: Reached limit of {} games",
            "progress": "Progress: {:.1f}% | Time remaining: {} | Games: {}/{} | Denuvo: {}",
            "created_queue": "Created queue with {} entries",
            "skipped_denuvo": "Skipped {} games with Denuvo",
            "no_games": "No valid games found for queue",
            "error": "Error: {}"
        }

    def _enforce_rate_limit(self):
        """Enforce strict rate limiting between API calls"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
    
        if elapsed < self.settings['api']['rate_limit']:
            sleep_time = self.settings['api']['rate_limit'] - elapsed
            if self.settings['operation']['verbose_logging']:
                self._log(f"\nRate limit: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
    
        self.last_request_time = time.time()
    def _display_header(self):
        """Display program header with platform settings"""
        print(f"""
+==============================================================+
|            {self.strings['header_title']}                   |
|==============================================================|
|                                                              |
|                    {self.strings['platforms_title']}                          |
|                                                              |
|  +-------------+    +-------------+    +-------------+       |
|  |   WINDOWS   |    |    MAC      |    |   LINUX     |       |
|  |     {('Y' if self.platforms['windows'] else 'N')}       |    |     {('Y' if self.platforms['mac'] else 'N')}       |    |     {('Y' if self.platforms['linux'] else 'N')}       |       |
|  +-------------+    +-------------+    +-------------+       |
|                                                              |
+==============================================================+""")

    def _setup_logging(self):
        """Initialize log file with timestamp"""
        if self.enable_logging:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_path, 'a') as log:
                log.write(f"\n{'='*50}\nScript started at {timestamp}\n{'='*50}\n")

    def _log(self, message):
        """Log message to console and file"""
        if message.startswith('\r'):
            print(message, end='', flush=True)
        else:
            print(message)
        
        if self.enable_logging:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_path, 'a', encoding='utf-8') as log:
                clean_message = message.replace('\r', '')
                log.write(f"[{timestamp}] {clean_message}\n")

    def _get_existing_games(self):
        """Load list of already processed games"""
        games_file = self.settings['files']['games_file']
        if not os.path.exists(games_file):
            return set()
        with open(games_file, 'r', encoding='utf-8') as f:
            return {line.split(' #')[0] for line in f if line.strip()}

    def get_games(self):
        """Get games list from Steam profile"""
        self._enforce_rate_limit()
        url = f"https://steamcommunity.com/id/{self.settings['steam']['steam_id']}/games?tab=all&xml=1"
        if self.settings['operation']['verbose_logging']:
            self._log(f"Requesting games list from: {url}")
        response = requests.get(url)
        games = re.findall(r'<game>.*?<appID>(\d+)</appID>.*?<name>(.*?)</name>', response.text, re.DOTALL)
        return {id: name.replace('<![CDATA[', '').replace(']]>', '') for id, name in games}

    def get_platforms(self, app_id):
        """Check game platforms and return platform info"""
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        
        self._enforce_rate_limit()
        
        try:
            if self.settings['operation']['verbose_logging']:
                self._log(f"Requesting data for AppID: {app_id}")
                request_start = time.time()
            
            response = requests.get(url, timeout=self.settings['api']['timeout'])
            data = response.json().get(str(app_id), {})
            
            if data.get('success'):
                app_data = data['data']
                platforms = app_data.get('platforms', {})
                is_free = app_data.get('is_free', False)
                has_denuvo = 'drm_notice' in app_data and 'Denuvo Anti-tamper' in app_data['drm_notice']
                
                if self.settings['operation']['verbose_logging']:
                    self._log(f"Game: {app_data.get('name')} | Free: {is_free} | Denuvo: {has_denuvo}")
                
                available = []
                queue_platforms = []
                
                # Check each platform
                for platform, enabled in [('windows', 'win64'), ('mac', 'macos'), ('linux', 'lin64')]:
                    if platforms.get(platform) and self.platforms[platform]:
                        available.append(platform.capitalize()[:3])
                        # Only filter Denuvo if the setting is enabled
                        if (not has_denuvo or not self.settings['operation']['filter_denuvo']) and not is_free:
                            queue_platforms.append(enabled)
                
                platforms_str = '/'.join(available) if available else 'Unknown'
                if has_denuvo:
                    platforms_str += " [DENUVO]"
                
                return platforms_str, queue_platforms, app_data.get('name', str(app_id))
                
        except Exception as e:
            if self.settings['operation']['verbose_logging']:
                self._log(f"Error checking platforms for {app_id}: {e}")
        return 'Unknown', [], str(app_id)

    def get_software(self):
        """Get and update software list"""
        software_file = self.settings['files']['software_file']
        existing_ids = set()
        
        if os.path.exists(software_file):
            with open(software_file, 'r', encoding='utf-8') as f:
                existing_ids = {line.split(' #')[0] for line in f if line.strip()}

        self._enforce_rate_limit()
        url = f"https://api.steampowered.com/IStoreService/GetAppList/v1/?key={self.settings['steam']['api_key']}&format=xml&include_games=false&include_dlc=true&include_software=true&include_videos=false&include_hardware=false&max_results=500000"
        response = requests.get(url)
        new_entries = re.findall(r'<appid>(\d+)</appid>.*?<name>(.*?)</name>', response.text, re.DOTALL)

        with open(software_file, 'a', encoding='utf-8') as f:
            for app_id, name in new_entries:
                if app_id not in existing_ids:
                    clean_name = name.encode('ascii', 'ignore').decode('ascii')
                    f.write(f"{app_id} #{clean_name}\n")
                    existing_ids.add(app_id)

        return existing_ids

    def process_queue_from_file(self):
        """Process games from input file"""
        try:
            input_file = self.settings['files']['input_file']
            if not os.path.exists(input_file):
                self._log(self.strings['error'].format(f"{input_file} not found!"))
                return

            self._log(self.strings['fetching_games'])
            with open(input_file, 'r', encoding='utf-8') as f:
                game_ids = [line.split('#')[0].strip() for line in f if line.strip()]

            if not game_ids:
                self._log(self.strings['no_games'])
                return

            self._log(self.strings['found_games'].format(len(game_ids)))
            return self._process_games_list(game_ids)

        except Exception as e:
            self._log(self.strings['error'].format(str(e)))

    def _process_games_list(self, game_ids):
        """Process list of games and create queue"""
        queue_data = []
        processed_count = 0
        denuvo_count = 0
        games_list = []

        total_games = min(len(game_ids), self.settings['operation']['test_limit']) if self.settings['operation']['test_mode'] else len(game_ids)
        
        estimated_seconds = total_games * self.settings['api']['rate_limit']
        estimated_time = time.strftime('%H:%M:%S', time.gmtime(estimated_seconds))
        
        self._log("\n" + self.strings['processing_ready'].format(total_games))
        self._log(self.strings['estimated_time'].format(estimated_time))
        input("\n" + self.strings['press_enter'])
        print()

        start_time = time.time()

        for game_id in game_ids:
            if self.settings['operation']['test_mode'] and processed_count >= self.settings['operation']['test_limit']:
                self._log("\n" + self.strings['test_mode_limit'].format(self.settings['operation']['test_limit']))
                break

            if processed_count > 0:
                elapsed_time = time.time() - start_time
                avg_time_per_game = elapsed_time / processed_count
                remaining_games = total_games - processed_count
                time_remaining = remaining_games * avg_time_per_game
                time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(time_remaining))
                progress = (processed_count / total_games) * 100
                progress_msg = "\r" + self.strings['progress'].format(
                    progress, time_remaining_str, processed_count, total_games, denuvo_count
                )
                self._log(progress_msg)

            platforms_str, queue_platforms, game_name = self.get_platforms(game_id)
            if "[DENUVO]" in platforms_str:
                denuvo_count += 1

            clean_name = game_name.encode('ascii', 'ignore').decode('ascii')
            games_list.append(f"{game_id} #{clean_name} [{platforms_str}]")

            if queue_platforms:
                queue_data.extend(f"{platform}|{game_id}|Public|" for platform in queue_platforms)
            
            processed_count += 1

        print()

        if games_list:
            games_file = self.settings['files']['games_file']
            mode = 'a' if os.path.exists(games_file) and not self.settings['operation']['queue_from_file'] else 'w'
            with open(games_file, mode, encoding='utf-8') as f:
                if mode == 'a' and os.path.getsize(games_file) > 0:
                    f.write('\n')
                f.write('\n'.join(games_list))
            self._log(f"\nAdded {len(games_list)} games to {games_file}")

        if queue_data:
            queue_file = self.settings['files']['queue_file']
            with open(queue_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(queue_data))
            self._log("\n" + self.strings['created_queue'].format(len(queue_data)))
            if denuvo_count > 0:
                self._log(self.strings['skipped_denuvo'].format(denuvo_count))
        else:
            self._log("\n" + self.strings['no_games'])

        return True

    def process_games(self):
        """Main processing function"""
        try:
            if self.settings['operation']['queue_from_file']:
                return self.process_queue_from_file()

            self._log(self.strings['start_processing'])
            software_ids = self.get_software()
            
            self._log(self.strings['fetching_games'])
            games = self.get_games()
            self._log(self.strings['found_games'].format(len(games)))
            
            game_ids = [
                game_id for game_id in games.keys()
                if game_id not in software_ids and game_id not in self.existing_games
            ]
            
            return self._process_games_list(game_ids)

        except Exception as e:
            self._log(self.strings['error'].format(str(e)))
            return False

def main():
    try:
        processor = SteamGameProcessor()
        processor.process_games()
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()