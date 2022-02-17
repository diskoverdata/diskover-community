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

// diskover-web community edition (ce) login post handling

namespace diskover;

class Login
{
    private $user;

    public function checkLoginPost(): bool
    {
        // Check posted login data.
        if (!$this->validateLogin()) {
            // Unsuccessful login.
            return false;
        }

        // Handle successful login.
        $this->handleSuccess();

        return true;
    }

    public function validateLogin(): bool
    {
        $username = $_SESSION['username'] = $_POST['username'];
        $password = $_POST['password'];

        // Load database and find user.
        $db = new UserDatabase();
        $db->connect();
        $user = $db->findUser($username);

        if ($user->validatePassword(Constants::PASS)) {
            // Default password is valid, redirect to change.
            header('location: password.php?initial');
            exit;
        }

        if (!$user->isValid) {
            return false;
        }

        if (!$user->validatePassword($password)) {
            return false;
        }

        // Valid user!
        $this->user = $user;
        return true;
    }

    public function handleSuccess()
    {
        if (isset($_POST['stayloggedin'])) {
            $_SESSION['stayloggedin'] = true;
        } else {
            $_SESSION['stayloggedin'] = false;
        }

        $_SESSION['loggedin'] = true;
        $_SESSION['last_activity'] = time();
        $_SESSION['username'] = $this->user->username;
    }
}
