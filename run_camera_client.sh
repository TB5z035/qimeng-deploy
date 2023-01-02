SHARE_PATH=/home/gongjt4/camera_share
ADDR=192.168.2.66
PORT=4444
docker run -v $SHARE_PATH:/share -p $PORT:$PORT --rm -it --privileged --name camera tb5zhh/qimeng-deploy python -m camera.client --station_id $ADDR --port $PORT

