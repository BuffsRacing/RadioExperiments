# RadioExperiments

![RadioExperiments Web Server](docs/assets/messages.png)

## Installation

Make sure you have [Poetry](https://python-poetry.org/) installed.

```bash
git clone https://github.com/buffsracing/radioexperiments
poetry install
poetry shell
cp .env.example .env
py -m flask --app main run
```

The web server will be available at [http://localhost:5000](http://localhost:5000).

## Current Features

* Record and playback radio messages
  * Recorded messages are stored as WAV files
  * If there is an internet connection, the WAV files are transcribed using Microsoft Azure Speech-to-Text
* Choose audio output device
  
## Planned Features

* Soundboard with pre-recorded messages to transmit
* Backup WAV files to a cloud storage service
* Public view with limited functionality

## Bundling the Web Server

Windows:

```bash
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" main.py
```

*nix:

```bash
pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" main.py
```