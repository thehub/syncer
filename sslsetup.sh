#!/bin/bash
setupSSLCerts () {
    openssl genrsa 1024 > certs/host.key
    echo "=============================="
    echo "Generating Server certificate"
    echo "=============================="
    openssl req -new -x509 -nodes -sha1  -key certs/host.key > certs/server.cert
    echo "=============================="
    echo "Generating Client certificate"
    echo "=============================="
    openssl req -new -x509 -nodes -sha1  -key certs/host.key > certs/client.cert
    cat certs/host.key certs/server.cert > certs/server.pem || exit 1
    cat certs/host.key certs/client.cert > certs/client.pem || exit 1
}
test -d certs || mkdir certs
test -e certs/server.pem && test -e certs/client.pem
if [ $? -ne 0 ]
    then
        echo
        echo "OpenSSL certificates are not found!\n"
        echo "Hit enter to invoke certificate generation wizard"
        echo "^c to exit"
        echo
        read ans
        setupSSLCerts
fi
