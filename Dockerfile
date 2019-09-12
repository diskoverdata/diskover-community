FROM kayosportsau/docker-diskover-base

ENV DISKOVER_WORKDIR /diskover
ENV DISKOVER_CONFIG ${DISKOVER_WORKDIR}/diskover.cfg
ENV DISKOVER_ROOTDIR ${DISKOVER_WORKDIR}/rootdir
ENV DISKOVER_PLUGINDIR ${DISKOVER_WORKDIR}/plugins

WORKDIR ${DISKOVER_WORKDIR}

COPY ./ ${DISKOVER_WORKDIR}/

RUN mkdir ${DISKOVER_ROOTDIR} && \
    pip install -r requirements.txt

VOLUME ["${DISKOVER_ROOTDIR}"]

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
