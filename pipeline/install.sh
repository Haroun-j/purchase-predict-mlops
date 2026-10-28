#!/bin/bash
set -e

apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 git \
  && rm -rf /var/lib/apt/lists/*

mkdir -p \
  conf/local \
  data/01_raw \
  data/02_intermediate \
  data/03_primary \
  data/04_feature \
  data/05_model_input \
  data/06_models \
  data/07_model_output \
  data/08_reporting \
  mlruns
