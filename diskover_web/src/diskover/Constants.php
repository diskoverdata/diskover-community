<?php

namespace diskover;

class Constants {
    // set to your Elasticearch host or ip
    const ES_HOST = 'localhost';
    // don't change following two lines
    const ES_INDEX = 'diskover-*';
    const ES_TYPE = 'file';
    // set following two lines if using X-Pack http-auth
    const ES_USER = '';
    const ES_PASS = '';
}
