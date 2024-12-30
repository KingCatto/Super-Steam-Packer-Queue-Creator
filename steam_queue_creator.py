"""
Steam Queue Creator - Creates Steam Super Packer queues with configurable Denuvo filtering.
Requires settings.json and language.txt in the same directory.
"""

import requests, re, time, os, json
from datetime import datetime
from pathlib import Path

class SteamGameProcessor:
    def __init__(self):
        self.settings = self._load_settings()
        self.strings = self._load_languages()
        self.log_path = Path(self.settings['files']['log_file'])
        self.existing_games = self._load_existing_games()
        self.last_request_time = 0
        self._setup_logging(self.settings['operation']['enable_logging'])
        self._display_header()

    def _load_settings(self):
        """Load and validate settings from JSON"""
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            exit(1)

    def _load_languages(self):
        """Load language strings with fallback to English"""
        try:
            languages = {}
            if os.path.exists('language.txt'):
                with open('language.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            lang, key, value = line.strip().split('|', 2)
                            languages.setdefault(lang, {})[key] = value
                return languages.get(self.settings['operation']['display_language'], 
                                  languages.get('english', self._get_default_english()))
            return self._get_default_english()
        except Exception as e:
            print(f"Error loading languages: {e}")
            return self._get_default_english()

    def _get_default_english(self):
        """Default English strings as fallback"""
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
        """Enforce API rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.settings['api']['rate_limit']:
            sleep_time = self.settings['api']['rate_limit'] - elapsed
            self.settings['operation']['verbose_logging'] and self._log(f"\nRate limit: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _setup_logging(self, enable_logging):
        """Initialize logging if enabled"""
        if enable_logging and (log_dir := os.path.dirname(self.log_path)):
            os.makedirs(log_dir, exist_ok=True)
            with open(self.log_path, 'a') as log:
                log.write(f"\n{'='*50}\nScript started at {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*50}\n")

    def _log(self, message):
        """Unified logging to console and file"""
        message.startswith('\r') and print(message, end='', flush=True) or print(message)
        if self.settings['operation']['enable_logging']:
            with open(self.log_path, 'a', encoding='utf-8') as log:
                log.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message.replace('\r', '')}\n")

    def _load_existing_games(self):
        """Load previously processed games"""
        try:
            games_file = self.settings['files']['games_file']
            return set(line.split(' #')[0] for line in open(games_file) if line.strip()) if os.path.exists(games_file) else set()
        except Exception:
            return set()

    def _check_denuvo(self, app_data):
        """Check for Denuvo DRM patterns"""
        if 'drm_notice' not in app_data:
            return False
        return any(pattern.lower() in app_data['drm_notice'].lower() 
                  for pattern in self.settings.get('drm', {}).get('denuvo_strings', 
                  ["Denuvo Anti-tamper", "Denuvo Antitamper"]))

    def _display_header(self):
        """Display configuration status"""
        denuvo_status = "ENABLED" if self.settings['operation'].get('filter_denuvo', True) else "DISABLED"
        platforms = self.settings['platforms']
        print(f"""
+==============================================================+
|            {self.strings['header_title']}                   |
|==============================================================|
|                                                              |
|                    {self.strings['platforms_title']}                          |
|                                                              |
|  +-------------+    +-------------+    +-------------+       |
|  |   WINDOWS   |    |    MAC      |    |   LINUX     |       |
|  |     {('Y' if platforms['windows'] else 'N')}       |    |     {('Y' if platforms['mac'] else 'N')}       |    |     {('Y' if platforms['linux'] else 'N')}       |       |
|  +-------------+    +-------------+    +-------------+       |
|                                                              |
|                 DENUVO FILTERING: {denuvo_status}                       |
+==============================================================+""")
    def get_games(self):
        """Fetch and parse Steam library games"""
        self._enforce_rate_limit()
        response = requests.get(f"https://steamcommunity.com/id/{self.settings['steam']['steam_id']}/games?tab=all&xml=1")
        return {id: name.replace('<![CDATA[', '').replace(']]>', '')
                for id, name in re.findall(r'<game>.*?<appID>(\d+)</appID>.*?<name>(.*?)</name>', 
                response.text, re.DOTALL)}

    def get_platforms(self, app_id):
        """Check platforms and DRM status for a game"""
        self._enforce_rate_limit()
        try:
            response = requests.get(
                f"https://store.steampowered.com/api/appdetails?appids={app_id}",
                timeout=self.settings['api']['timeout']
            ).json().get(str(app_id), {})
            
            if response.get('success'):
                app_data = response['data']
                platforms = app_data.get('platforms', {})
                is_free = app_data.get('is_free', False)
                has_denuvo = self._check_denuvo(app_data)
                
                if self.settings['operation']['verbose_logging']:
                    self._log(f"Game: {app_data.get('name')} | Free: {is_free} | Denuvo: {has_denuvo}")
                
                available = []
                queue_platforms = []
                
                for plat, enabled in [('windows', 'win64'), ('mac', 'macos'), ('linux', 'lin64')]:
                    if platforms.get(plat) and self.settings['platforms'][plat]:
                        available.append(plat.capitalize()[:3])
                        if not is_free and (not has_denuvo or not self.settings['operation'].get('filter_denuvo', True)):
                            queue_platforms.append(enabled)
                
                return f"{'/'.join(available) if available else 'Unknown'}{' [DENUVO]' if has_denuvo else ''}", queue_platforms, app_data.get('name', str(app_id))
        except Exception as e:
            self.settings['operation']['verbose_logging'] and self._log(f"Error checking platforms for {app_id}: {e}")
        return 'Unknown', [], str(app_id)

    def get_software(self):
        """Update and return software list"""
        existing_ids = set()
        software_file = self.settings['files']['software_file']
        
        if os.path.exists(software_file):
            with open(software_file, 'r', encoding='utf-8') as f:
                existing_ids = {line.split(' #')[0] for line in f if line.strip()}

        self._enforce_rate_limit()
        response = requests.get(
            f"https://api.steampowered.com/IStoreService/GetAppList/v1/",
            params={
                'key': self.settings['steam']['api_key'],
                'format': 'xml',
                'include_games': 'false',
                'include_dlc': 'true',
                'include_software': 'true',
                'include_videos': 'false',
                'include_hardware': 'false',
                'max_results': '500000'
            }
        )

        new_entries = re.findall(r'<appid>(\d+)</appid>.*?<name>(.*?)</name>', response.text, re.DOTALL)
        
        with open(software_file, 'a', encoding='utf-8') as f:
            for app_id, name in new_entries:
                if app_id not in existing_ids:
                    f.write(f"{app_id} #{name.encode('ascii', 'ignore').decode('ascii')}\n")
                    existing_ids.add(app_id)

        return existing_ids

    def _process_games_list(self, game_ids):
        """Process games and generate queue"""
        queue_data, games_list, denuvo_count = [], [], 0
        total_games = min(len(game_ids), self.settings['operation']['test_limit']) if self.settings['operation']['test_mode'] else len(game_ids)
        processed_count = 0
        
        self._log("\n" + self.strings['processing_ready'].format(total_games))
        self._log(self.strings['estimated_time'].format(time.strftime('%H:%M:%S', time.gmtime(total_games * self.settings['api']['rate_limit']))))
        input("\n" + self.strings['press_enter'] + "\n")

        start_time = time.time()
        
        for game_id in game_ids:
            if self.settings['operation']['test_mode'] and processed_count >= self.settings['operation']['test_limit']:
                self._log("\n" + self.strings['test_mode_limit'].format(self.settings['operation']['test_limit']))
                break

            # Show progress
            if processed_count > 0:
                elapsed = time.time() - start_time
                remaining = (total_games - processed_count) * (elapsed / processed_count)
                self._log("\r" + self.strings['progress'].format(
                    (processed_count / total_games) * 100,
                    time.strftime('%H:%M:%S', time.gmtime(remaining)),
                    processed_count, total_games, denuvo_count
                ))

            platforms_str, queue_platforms, game_name = self.get_platforms(game_id)
            denuvo_count += '[DENUVO]' in platforms_str
            games_list.append(f"{game_id} #{game_name.encode('ascii', 'ignore').decode('ascii')} [{platforms_str}]")
            queue_data.extend(f"{platform}|{game_id}|Public|" for platform in queue_platforms)
            processed_count += 1

        # Save results
        if games_list:
            games_file = self.settings['files']['games_file']
            mode = 'a' if os.path.exists(games_file) and not self.settings['operation']['queue_from_file'] else 'w'
            with open(games_file, mode, encoding='utf-8') as f:
                if mode == 'a' and os.path.getsize(games_file) > 0:
                    f.write('\n')
                f.write('\n'.join(games_list))
            self._log(f"\nAdded {len(games_list)} games to {games_file}")

        if queue_data:
            with open(self.settings['files']['queue_file'], 'w', encoding='utf-8') as f:
                f.write('\n'.join(queue_data))
            self._log("\n" + self.strings['created_queue'].format(len(queue_data)))
            denuvo_count and self._log(self.strings['skipped_denuvo'].format(denuvo_count))
        else:
            self._log("\n" + self.strings['no_games'])

        return True

    def process_queue_from_file(self):
        """Process games from input file"""
        try:
            input_file = self.settings['files']['input_file']
            if not os.path.exists(input_file):
                return self._log(self.strings['error'].format(f"{input_file} not found!"))

            self._log(self.strings['fetching_games'])
            with open(input_file, 'r', encoding='utf-8') as f:
                game_ids = [line.split('#')[0].strip() for line in f if line.strip()]

            return self._process_games_list(game_ids) if game_ids else self._log(self.strings['no_games'])
        except Exception as e:
            self._log(self.strings['error'].format(str(e)))

    def process_games(self):
        """Main entry point for processing"""
        try:
            if self.settings['operation']['queue_from_file']:
                return self.process_queue_from_file()

            self._log(self.strings['start_processing'])
            software_ids = self.get_software()
            
            self._log(self.strings['fetching_games'])
            games = self.get_games()
            self._log(self.strings['found_games'].format(len(games)))
            
            return self._process_games_list([
                game_id for game_id in games.keys()
                if game_id not in software_ids and game_id not in self.existing_games
            ])
        except Exception as e:
            self._log(self.strings['error'].format(str(e)))
            return False

def main():
    try:
        SteamGameProcessor().process_games()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
