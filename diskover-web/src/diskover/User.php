<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover-web community edition (ce) user data

namespace diskover;

class User
{
    public $isValid = false;

    public $username;

    public $passHash;

    public function setPassword($password)
    {
        $this->passHash = $this->hashPassword($password);
    }

    public function hashPassword($password): string
    {
        // Pepper the password before hashing.
        $peppered = hash_hmac('sha256', $password, Constants::PASSWORD_PEPPER);
        return password_hash($peppered, PASSWORD_DEFAULT);
    }

    public function validatePassword($password): bool
    {
        // Pepper the password before verifying.
        $peppered = hash_hmac('sha256', $password, Constants::PASSWORD_PEPPER);
        return password_verify($peppered, $this->passHash);
    }
}
