# Super-Steam-Packer-Queue-Creator

A Python script for creating Steam Super Packer queues with platform filtering, Denuvo detection, and multi-language support.

## Features

This script provides comprehensive functionality for managing Steam game queues. It offers platform filtering, Denuvo detection, and supports multiple languages. Key features include queue creation from both Steam library and input files, proper API rate limiting, and detailed progress tracking.

## Prerequisites

- Python 3.6 or higher
- requests library (`pip install requests`)
- Steam account with custom URL
- Steam Web API key
- Super Steam Packer (https://cs.rin.ru/forum/viewtopic.php?p=2804531)

## Installation

Installation is straightforward and requires minimal setup:

1. Install Python requirements:
```bash
pip install requests
```

2. Download required files:
   - `steam_queue_creator.py` - Main script
   - `settings.json` - Configuration file
   - `language.txt` - Language strings

3. Place all files in the same directory

## Configuration

### Steam Setup

1. Get your Steam Web API Key:
   - Visit https://steamcommunity.com/dev/apikey
   - Login with your Steam account
   - Create a new key if needed
   - Copy the API key

2. Get your Steam Vanity URL:
   - Go to your Steam profile
   - Copy the name from: `steamcommunity.com/id/YOUR_VANITY_URL`
   - Use this as your Steam ID in the configuration

### Settings Configuration

The settings.json file controls all aspects of the script's operation:

```json
{
    "steam": {
        "steam_id": "YOUR_STEAM_ID_HERE",
        "api_key": "YOUR_API_KEY_HERE"
    },
    "platforms": {
        "windows": true,
        "mac": false,
        "linux": true
    },
    "operation": {
        "queue_from_file": false,
        "test_mode": true,
        "test_limit": 5,
        "verbose_logging": false,
        "enable_logging": true,
        "display_language": "english",
        "filter_denuvo": true
    }
}
```

## Usage

### Processing Steam Library
```bash
python steam_queue_creator.py
```

### Processing From File
1. Create queue.txt with one Steam AppID per line
2. Enable queue_from_file in settings.json
3. Run the script

## Output Files

The script generates several output files:

- games.txt: List of processed games with platform information
- software.txt: List of detected software applications
- gamelistqueue.SSPQ: Generated queue file
- log.txt: Operation log (when enabled)

### File Format Examples

games.txt format:
```
440 #Team Fortress 2 [Win/Lin]
570 #Dota 2 [Win/Lin/Mac]
730 #Counter-Strike 2 [Win/Lin] [DENUVO]
```

gamelistqueue.SSPQ format:
```
win64|440|Public|
lin64|440|Public|
win64|570|Public|
lin64|570|Public|
```

## Language Support

The script includes support for:
- English
- French
- German
- Pirate
- Spanish

Change the language by setting display_language in settings.json

## Troubleshooting

Common issues and solutions:

1. "Module not found 'requests'":
```bash
pip install requests
```

2. API Key validation errors:
   - Verify your key at https://steamcommunity.com/dev/apikey
   - Check settings.json configuration

3. Profile not found:
   - Verify your Steam Vanity URL
   - Ensure your profile is public

4. Rate limiting issues:
   - Adjust rate_limit in settings.json
   - Default is 2.0 seconds between requests

## License

This script is provided as-is for the CS.rin.ru community. Use at your own discretion.

## Acknowledgments

Special thanks to Masquerade for creating Super Steam Packer, making this queue creation tool possible.
