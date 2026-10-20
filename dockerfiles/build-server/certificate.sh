mkdir -p /srv/registry/certs
sudo openssl req \
    -newkey rsa:3072 \
    -nodes \
    -sha256 \
    -x509 \
    -days 365 \
    -keyout /srv/registry/certs/registry.key \
    -out /srv/registry/certs/registry.crt \
    -subj "/CN=registry.example.lan" \
    -addext "subjectAltName=DNS:registry.example.lan, 185.221.22.224"



sudo openssl req \
    -newkey rsa:3072 \
    -nodes \
    -sha256 \
    -x509 \
    -days 365 \
    -keyout /srv/registry/certs/registry.key \
    -out /srv/registry/certs/registry.crt \
    -subj "/CN=registry.example.lan" \
    -addext "subjectAltName=DNS:registry.example.lan, 185.221.22.224"



  chmod 600 /srv/registry/certs/registry.key

docker stop registry
docker rm registry


docker run -d \
    --name registry \
    --restart unless-stopped \
    -p 5000:5000 \
    -v /srv/docker-registry:/var/lib/registry \
    -v /srv/registry/certs:/certs:ro \
    -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registry.crt \
    -e REGISTRY_HTTP_TLS_KEY=/certs/registry.key \
    registry:3


curl --cacert /srv/registry/certs/registry.crt \
    https://185.221.22.224:5000/v2/

#build
mkdir -p /etc/docker/certs.d/registry.example.lan:5000
cp /srv/registry/certs/registry.crt /etc/docker/certs.d/registry.example.lan:5000/ca.crt
docker push 185.221.22.224:5000/simple-tickets-backend:test

#application разместить
#/etc/docker/certs.d/registry.example.lan:5000/ca.crt
#docker pull 185.221.22.224:5000/simple-tickets-backend:test