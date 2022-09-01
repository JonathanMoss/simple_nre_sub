#!/bin/sh

set -eu

( rabbitmqctl wait --timeout 60 "${RABBITMQ_PID_FILE}"; \
rabbitmqctl  add_user "${RMQ_USER}" "${RMQ_PASS}"
rabbitmqctl  set_user_tags "${RMQ_USER}" administrator
rabbitmqctl  set_permissions -p / "${RMQ_USER}" ".*" ".*" ".*" ) &

rabbitmq-server $@
