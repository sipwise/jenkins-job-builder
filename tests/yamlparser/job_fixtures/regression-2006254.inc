#!/bin/bash
IMG_NAME="gluster/glusterd2-nightly"
IMG_VERSION=$(date +%Y%m%d)


mkdir -p go/{pkg,src,bin}
export GOPATH=$PWD/go
export PATH=$PATH:$GOPATH/bin
export PATH=/usr/sbin:$PATH

export CSISRC=$GOPATH/src/github.com/gluster/gluster-csi-driver
cd $CSISRC
go get github.com/xxx/yyy
go get -u github.com/golang/dep/cmd/dep
make

cp pkg/glusterfs/Dockerfile .
buildah bud .
#if [ "$PUSH_TO_HUB" = true ]; then
    #buildah push --authfile $AUTH_JSON "localhost/$IMG_NAME:$IMG_VERSION" "docker://docker.io/gluster/glusterd2-nightly:$IMG_VERSION"
    #buildah push --authfile $AUTH_JSON "localhost/$IMG_NAME:$IMG_VERSION" "docker://docker.io/gluster/glusterd2-nightly:latest"
#fi
