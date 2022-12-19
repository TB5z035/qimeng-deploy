docker run -v $(pwd):/etc/redis --name redis -p 6379:6379 -it redis:7.0.7 redis-server /etc/redis/redis.conf
