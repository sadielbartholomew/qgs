#!/usr/bin/env bash

cd source/files/examples

for file in ./*.ipynb; do
    jupyter nbconvert --to rst "$file"
done
