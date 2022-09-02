FROM python:3.8-alpine
ADD ./docker/base-python/requirements.txt .
ADD ./nre_sldb_soap.py .
ADD ./persistent_outbound_mq.py .
ADD ./docker/nre-sldb-soap/entrypoint.sh .
RUN pip3 install -r ./requirements.txt
