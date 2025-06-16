# greenCDN
## File Structure
green-cdn/  
├── docker-compose.yml  
├── haproxy/  
│   └── haproxy.cfg  
├── web1/  
│   ├── app.py  
│   └── Dockerfile  
├── web2/  
│   ├── app.py  
│   └── Dockerfile  
├── web3/  
│   ├── app.py  
│   └── Dockerfile  
## Commands
First create the network:  
  `docker network create --driver=bridge mynetwork`  
  
Then set up the servers:  
  `docker run -d --name web1 --net mynetwork -e ECHO_SERVER_TEXT="Hello from server 1" ealen/echo-server`  
  `docker run -d --name web2 --net mynetwork -e ECHO_SERVER_TEXT="Hello from server 2" ealen/echo-server`  
  `docker run -d --name web3 --net mynetwork -e ECHO_SERVER_TEXT="Hello from server 3" ealen/echo-server`  
  
Make sure you have the config file in your current directory. Then run HAProxy:  
  `docker run -d --name haproxy --net mynetwork -v "${PWD}\haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro" -p 80:80 -p 8404:8404 haproxytech/haproxy-alpine:2.4`  

You can simulate a request by visiting http://localhost and you can view the dashboard by visiting http://localhost:8404  

To stop and remove the containers, run these lines:  
`docker stop web1; docker rm web1`  
`docker stop web2; docker rm web2`  
`docker stop web3; docker rm web3`  
`docker stop haproxy; docker rm haproxy`  
`docker network rm mynetwork`  

Source: https://www.haproxy.com/blog/how-to-run-haproxy-with-docker
