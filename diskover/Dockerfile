FROM python:3.7-alpine
LABEL maintainer "Diskover Data <info@diskoverdata.com>"

# Install additional packages
RUN apk update \
  && apk add --no-cache --virtual build-dependencies \
  build-base \
  gcc \
  python3-dev \
  && apk add --no-cache bash \
  ncurses

# Copy existing application directory contents
COPY . /app/diskover

WORKDIR /app/diskover

# Install required python3 pip modules
RUN pip install --no-cache-dir -r requirements.txt

# Keep container running
ENTRYPOINT [ "./docker-entrypoint.sh" ]
