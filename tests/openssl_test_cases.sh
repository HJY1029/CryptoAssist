#!/bin/bash
openssl enc -aes-128-cbc -k secret -in /dev/null -out /dev/null 2>&1
