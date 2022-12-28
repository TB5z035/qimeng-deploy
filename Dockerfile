FROM python:3.9
RUN apt-get update && \
    apt-get install redis libgl1-mesa-glx libglib2.0-0 lsb-release -y && \
    apt-get clean
ADD mysql/mysql-apt-config_0.8.24-1_all.deb /opt/mysql-apt.deb
RUN DEBIAN_FRONTEND=noninteractive dpkg -i /opt/mysql-apt.deb
RUN apt-get update && \
    apt-get install mysql-client -y && \
    apt-get clean

ADD requirements.txt /workspace/qimeng/requirements.txt
WORKDIR /workspace/qimeng
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
ADD qimeng /workspace/qimeng
# RUN python manage.py migrate
ADD lib/libMVSDK.so /lib/libMVSDK.so
ADD lib/*.rules /etc/udev/rules.d/
ADD redis/redis.conf /etc/redis.conf
