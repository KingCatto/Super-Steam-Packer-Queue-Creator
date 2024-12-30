# Super-Steam-Packer-Queue-Creator

A Python script to create Steam Super Packer queues with platform filtering, Denuvo detection, and multilingual support. 

## Features

- Creates queue files for Steam Super Packer
- Filters out software and free games
- Detects and marks games with Denuvo DRM
- Supports multiple languages (English, French, German, Pirate, Spanish)
- Enforces proper API rate limiting
- Tracks progress and estimates completion time
- Can process games from Steam library or input file

## Prerequisites

- Python 3.6 or higher
- requests library (`pip install requests`)
- Steam account with custom URL
- Steam Web API key

## Setup

1. Install required Python package:
   ```bash
   pip install requests
   ```

2. Get your Steam Web API Key:
   - Visit https://steamcommunity.com/dev/apikey
   - Create new key if you don't have one
   - Save the key for configuration

3. Get your Steam Vanity URL:
   - Go to your Steam profile
   - Your URL will look like: `steamcommunity.com/id/YOUR_VANITY_URL`
   - Copy the part after `/id/`

4. Configure the script:
   - Open `steam_queue_creator.py`
   - Set your STEAM_ID (Vanity URL)
   - Set your API_KEY
   - Adjust other settings as needed

## Configuration Options

### Steam API Settings
```python
STEAM_ID = "YOUR_STEAM_ID_HERE"     # Your Steam Vanity URL
API_KEY = "YOUR_API_KEY_HERE"       # Your Steam Web API Key
DISPLAY_LANGUAGE = "english"         # Interface language
```

### Platform Settings
```python
PLATFORM_WINDOWS = True             # Include Windows games
PLATFORM_MAC = False                # Include Mac games
PLATFORM_LINUX = True              # Include Linux games
```

### Processing Settings
```python
QUEUE_FROM_FILE = False            # Use queue.txt instead of Steam library
TEST_MODE = True                   # Enable test mode
TEST_LIMIT = 5                     # Number of games to process in test mode
VERBOSE_LOGGING = False            # Show detailed API logs
ENABLE_LOGGING = True              # Save logs to file
```

## Usage

### Process Steam Library
1. Configure settings in the script
2. Run the script:
   ```bash
   python steam_queue_creator.py
   ```
3. Wait for processing to complete

### Process From File
1. Create a file named `queue.txt`
2. Add one Steam AppID per line
3. Set `QUEUE_FROM_FILE = True` in settings
4. Run the script

## Output Files

- `games.txt`: List of processed games with platform info
- `software.txt`: List of detected software applications
- `gamelistqueue.SSPQ`: Generated queue file for Steam Super Packer
- `log.txt`: Operation log (if logging enabled)

### Output Format Examples

games.txt:
```
440 #Team Fortress 2 [Win/Lin]
570 #Dota 2 [Win/Lin/Mac]
730 #Counter-Strike 2 [Win/Lin] [DENUVO]
```

gamelistqueue.SSPQ:
```
win64|440|Public|
lin64|440|Public|
win64|570|Public|
lin64|570|Public|
macos|570|Public|
```

## Language Support

Available languages:
- English
- French
- German
- Pirate
- Spanish

Change language by setting `DISPLAY_LANGUAGE` in configuration.

## Rate Limiting

The script enforces a 2-second delay between Steam API calls to comply with rate limits. This affects processing time but ensures reliable operation.

Estimated processing time:
- 2 seconds per game
- Example: 100 games ≈ 3.5 minutes

## Troubleshooting

### Common Issues

1. "No module named 'requests'":
   ```bash
   pip install requests
   ```

2. "API Key not valid":
   - Check your API key at https://steamcommunity.com/dev/apikey
   - Ensure it's correctly copied to configuration

3. "Profile not found":
   - Verify your Steam Vanity URL
   - Make sure your profile is public

4. Rate limit errors:
   - The script automatically handles rate limiting
   - If you still get errors, increase PLATFORM_RATE_LIMIT

### Debug Mode

For detailed logging:
1. Set `VERBOSE_LOGGING = True`
2. Check log.txt for API responses

## Contributing

Feel free to:
- Submit bug reports
- Suggest features
- Add new language translations
- Improve documentation

## License

This script is provided as-is for the CS.rin.ru community. Use at your own discretion.

## Acknowledgments

- Thanks to Steam for providing the API
- Thamks to Masquerade for making Super Steam Packer
