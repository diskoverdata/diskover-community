FROM python:3.7.3-slim-stretch

ENV DISKOVER_WORKDIR /diskover
ENV DISKOVER_CONFIG ${DISKOVER_WORKDIR}/diskover.cfg
ENV DISKOVER_ROOTDIR ${DISKOVER_WORKDIR}/rootdir
ENV DISKOVER_PLUGINDIR ${DISKOVER_WORKDIR}/plugins

WORKDIR ${DISKOVER_WORKDIR}

COPY ./ ${DISKOVER_WORKDIR}/

RUN apt-get update && \
    apt-get install curlftpfs --yes && \
    apt-get clean && \
    mkdir ${DISKOVER_ROOTDIR} && \
    pip install -r requirements.txt

VOLUME ["${DISKOVER_ROOTDIR}"]

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
