# HTTPy Server
- Small HTTP server written using (mostly) standard python libraries
- Server supports HTTPS if you have the keys, which you could get from `Let's Encrypt`

# Running HTTPy Server
- Server requires `python3.12` and up
- `git clone https://github.com/UltraQbik/httpy`
- `cd httpy`
- `python3.12 main.py -p 80` to run basic HTTP server on port `80`
- enter `127.0.0.1` in browser path, and you should see the page
### Command line arguments
- `-p / --port` - port to which the server will be binded
- `-c / --certificate` - SSL certificate (full chain if using certbot)
- `-k / --private-key` - SSL private key
- `--compress-path` - compresses all files in `www` directory (if not explicitly said not to in `src/config.py`)
- `--enable-ssl` - enables SSL, which allows to connect using https, requires certificate and private key to be present
- `-v / --verbose` - prints a lot of information
- `-lu / --live-update` - live updates files, even when using compression

# Run using docker
- build image `docker build -t httpy .`
- start a new service `docker service create --name httpy_server -p 13700:13700 httpy`
- `-p A:B` is a port mapping from port host's port `13700 (A)` to container's port `13700 (B)`, change to the port you use
