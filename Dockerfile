FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime
RUN apt-get update && apt-get install redis libgl1-mesa-glx libglib2.0-0 -y && apt-get clean
ADD requirements.txt /workspace/qimeng/requirements.txt
WORKDIR /workspace/qimeng
RUN pip install -r requirements.txt
ADD qimeng /workspace/qimeng
RUN python manage.py migrate
ADD lib/libMVSDK.so /lib/libMVSDK.so
ADD lib/*.rules /etc/udev/rules.d
ADD lib/1223.Config /opt/qm.Config
ADD redis/redis.conf /etc/redis.conf

# CMD redis-server /etc/redis.conf; gunicorn --daemon --bind=0.0.0.0 qimeng.wsgi; python manage.py rqworker