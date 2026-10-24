#!/bin/sh
case "$1" in
    post)
        /usr/local/bin/omen-rgb on || true
        ;;
esac
