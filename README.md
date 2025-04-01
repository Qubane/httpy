# HTTPy Server
- Small HTTP server written using (mostly) standard python libraries
- Server supports HTTPS if you have the keys, which you could get from `Let's Encrypt`

# Running HTTPy Server
- `git clone https://github.com/UltraQbik/httpy`
- `cd httpy`
- `python3.12 main.py -a 127.0.0.1:80` to run basic HTTP server on port `80`
- enter `127.0.0.1` in browser path, and you should see the page
### Command line arguments
- `-a / --address` - address:port pair
- `-c / --certificate` - SSL certificate
- `-k / --private-key` - SSL private key

# System requirements
## Without docker
- At least python 3.12 and higher
- 128 MiB of RAM
- 1 GiB of disk space
## With docker
- idk lol

# Running using docker
- build image `docker build -t httpy .`
- start a new service `docker run -d -p 13700:13700 httpy -p 13700`
- `-p A:B` is a port mapping from port host's port `13700 (A)` to container's port `13700 (B)`, change to the port you use
