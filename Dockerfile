FROM microservice_python
MAINTAINER Cerebro <cerebro@ganymede.eu>

RUN apt-get install -y haproxy
RUN pip install -U web.py
RUN sed -i 's/ENABLED=0/ENABLED=1/' /etc/default/haproxy

ADD . /opt/main-haproxy
ADD ./supervisor/main-haproxy.conf /etc/supervisor/conf.d/main-haproxy.conf

RUN cp /opt/main-haproxy/src/initial_haproxy.cfg /etc/haproxy/haproxy.cfg

# Port exposed by HAProxy system service. It should be published to the host at port 80.
# Internal web service main_haproxy.py, used for hosting index page, uploading new haproxy.cfg and health-checks
# via REST API is running on port 8080 inside the container, however main-haproxy uses it as default backend so port 80
# can be used for uploading as well.
EXPOSE 80
