FROM microservice_python
MAINTAINER Cerebro <cerebro@ganymede.eu>

RUN add-apt-repository -y ppa:vbernat/haproxy-1.9
RUN apt-get update -y
RUN apt-get install -y haproxy socat
RUN pip install -U bottle armada
RUN sed -i 's/ENABLED=0/ENABLED=1/' /etc/default/haproxy

ADD . /opt/main-haproxy
ADD ./supervisor/* /etc/supervisor/conf.d/

RUN cp /opt/main-haproxy/src/initial_haproxy.cfg /etc/haproxy/haproxy.cfg
RUN cp /opt/main-haproxy/errors/* /etc/haproxy/errors/

# Port exposed by HAProxy system service. It should be published to the host at port 80.
# Internal web service main_haproxy.py, used for hosting index page, uploading new haproxy.cfg and health-checks
# via REST API is running on port 8080 inside the container, however main-haproxy uses it as default backend so port 80
# can be used for uploading as well.
EXPOSE 80
EXPOSE 8001
