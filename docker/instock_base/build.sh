#!/bin/sh

cd ../../

DOCKER_NAME=instock_base
TAG=latest

echo " docker build -f docker/instock_base/Dockerfile -t ${DOCKER_NAME} ."
docker build -f docker/instock_base/Dockerfile -t ${DOCKER_NAME}:${TAG} .
