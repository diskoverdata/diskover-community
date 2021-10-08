FROM composer:1.9.3 as vendor
LABEL maintainer "Diskover Data <info@diskoverdata.com>"

WORKDIR /tmp/

COPY composer.json composer.json
COPY composer.lock composer.lock

RUN composer install \
    --ignore-platform-reqs \
    --no-interaction \
    --no-plugins \
    --no-scripts \
    --prefer-dist


FROM php:7.4-fpm

# Install php ldap extension
RUN apt-get update && \
        apt-get install -y libldap2-dev
RUN docker-php-ext-configure ldap
RUN docker-php-ext-install ldap

# Copy existing application directory contents
COPY . /var/www
COPY --from=vendor /tmp/vendor/ /var/www/vendor/