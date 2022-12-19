docker run --name deploy-redis-server --rm \
    -p 30079:6379\
    -p 30079:6379/udp\
    -v $(pwd)/conf:/usr/local/etc/redis\
    redis:7.0.7-alpine\
    redis-server /usr/local/etc/redis/redis.conf