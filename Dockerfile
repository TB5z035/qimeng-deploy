FROM python:3.9
RUN apt-get update && apt-get install redis libgl1-mesa-glx libglib2.0-0 -y && apt-get clean
ADD requirements.txt /workspace/qimeng/requirements.txt
WORKDIR /workspace/qimeng
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
ADD qimeng /workspace/qimeng
RUN python manage.py migrate
ADD lib/libMVSDK.so /lib/libMVSDK.so
ADD lib/*.rules /etc/udev/rules.d/
ADD redis/redis.conf /etc/redis.conf
