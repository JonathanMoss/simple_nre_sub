FROM rabbitmq:3.8.2-alpine
ENV RABBITMQ_PID_FILE=/var/lib/rabbitmq/mnesia/rabbitmq
RUN rabbitmq-plugins enable rabbitmq_management
ADD ./docker/rabbitmq/entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
