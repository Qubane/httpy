# HTTPy
- Small HTTP server written using standard python libraries
- Server supports HTTPS if you have the keys, which you could get from `Let's Encrypt`

# Run using docker
- build image `docker build -t httpy .`
- start a new service `docker service create --name httpy_server -p 13700:13700 httpy`
- `-p A:B` is a port mapping from port host's port `13700 (A)` to container's port `13700 (B)`, change to the port you use
