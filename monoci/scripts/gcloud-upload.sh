#!/bin/bash

gcloud docker -- push $IMAGE_NAME:latest
gcloud docker -- push $IMAGE_NAME:$VERSION