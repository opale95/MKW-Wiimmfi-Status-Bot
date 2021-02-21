# MKW Wiimmfi Status Bot
**A Discord Bot (using the discord.py python library) that shows the current amount of people playing Mario Kart Wii on the custom Wiimmfi servers.**

Wiimmfi server website (from which the data is taken from): https://wiimmfi.de/stat?m=88

Installing
------------
**Python 3.9.1 required**

Install required libraries:

```sh
# Linux/macOS
python3 -m pip install -r requirements.txt

# Windows
py -3 -m pip install -r requirements.txt
```

Required library on Raspbian (for Raspberry Pi hardware):

```sh
sudo apt-get install libatlas-base-dev
```

Configuration
--------------
  - Go to the Discord Applications website and select/create your App: 
		https://discord.com/developers/applications/
  - Client ID:
    - Click the Copy button under Client ID
        - Open the client_id.txt file, remove any content then paste.
  - Token:
    - Click the Bot section under Settings on the left of the webpage.
    - Click the Copy button under Token.
    - Open the token.txt file, remove any content then paste.

Usage
------
```sh
#Linux/macOS
python3 main.py
```
