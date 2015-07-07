# main-haproxy

`main-haproxy` service contains armadized [HAProxy](http://www.haproxy.org). It can be used to redirect and load balance
your HTTP traffic. Using it alongside `magellan` is a recommended way for service discovery on Armada platform.


Beside HAProxy the service contains REST API endpoint (`/upload_config`) that allows dynamic update of HAProxy configuration.


# Building and running the service.

    armada build main-haproxy
    armada run main-haproxy -p 80:80

The HAProxy service is bound to the port 80 inside the container.
It is a good practice to map it to port 80 on the host also.

Internal service that allows dynamic configuration update runs on port 8080 inside the container.
However `main-haproxy` uses it as default backend so port 80 can be used for uploading configuration as well.
There is no need to expose separate port for it.


## Pairing with `magellan`.

Great results can be achieved by using `main-haproxy` + `magellan` duo.
The first service is responsible for directing net traffic, while the second one is responsible for configuring
the rules for it.

Most common real-life scenario is pointing domain such as `*.initech.com` to the ship/ships that run `main-haproxy` and then
configure `magellan` to map subdomains such as `chat-service.initech.com` to service `chat-service` registered in Armada
catalog. `magellan` by default will configure all `main-haproxy` services in its Armada cluster that have the same
environment set. So the recommended way to run `main-haproxy` is something like this:

    armada run main-haproxy -p 80:80 --env production-aws       (on every ship in the Armada cluster)
    armada run magellan --env production-aws
