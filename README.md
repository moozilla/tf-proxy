## TF Proxy

This script establishes a simple TCP network proxy between the Tetris Friends server and
client, that can be used to sniff traffic, as well as inject traffic. Possible uses:

- Record games as they are being played, to create a large corpus of game play data
  (eg. for training a ML model)
- Generate live stats on player performance, and inject chat message summaries
- Experiment with undocumented parts of the game

### Usage

- Run the proxy with `py ./proxy.py`
- You can live edit `parser.py` while the proxy is running
- See https://www.youtube.com/watch?v=iApNzWZG-10 for inspiration
