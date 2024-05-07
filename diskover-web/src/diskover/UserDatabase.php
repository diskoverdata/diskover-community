<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2023 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover-web community edition (ce) sqlite3 user database

namespace diskover;
use SQLite3;

class UserDatabase
{
    private $db;
    private $databaseFilename;

    public function connect()
    {
        require 'config_defaults_web.php';
        
        // Get database file path from config defaults
        // Check for env var
        $this->databaseFilename = getenv('DATABASE') ?: $config_defaults_web['DATABASE'];

        try {
            // Open sqlite database
            $this->db = new SQLite3($this->databaseFilename);
        }
        catch (\Exception $e) {
            throw new \Exception('There was an error connecting to the database! ' . $e->getMessage());
        }

        // Check database file is writable
        if (!is_writable($this->databaseFilename)) {
            throw new \Exception($this->databaseFilename . ' is not writable!');
        }

        // Initial setup if necessary.
        $this->setupDatabase();
    }

    protected function setupDatabase()
    {
        require 'config_defaults_web.php';
        // If the database users table is not empty, we have nothing to do here.
        $res = $this->db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='users'");
        if ($row = $res->fetchArray()) {
            return;
        }

        // Set up sqlite user table if does not yet exist.
        $res = $this->db->exec("CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT NOT NULL, 
            password TEXT NOT NULL
        )");

        if (!$res) {
            throw new \Exception('There was an error creating users table!');
        }

        // Grab config data and create initial user.
        $user = new User();
        $user->username = $config_defaults_web['USER'];
        $user->setPassword($config_defaults_web['PASS']);

        // Add the user, and save the newly created entry.
        $this->addUser($user);
    }

    protected function addUser(User $user)
    {
        $this->db->exec("INSERT INTO users ('username', 'password') 
            VALUES ('$user->username', '$user->passHash')");
    }

    protected function closeDatabase()
    {
        $this->db->close();
    }

    public function findUser($username): User
    {
        $user = new User();

        $res = $this->db->query('SELECT * FROM users');

        while ($row = $res->fetchArray()) {
            if ($row['username'] != $username) {
                continue;
            }

            // Found a username match.
            $user->isValid = true;
            $user->username = $row['username'];
            $user->passHash = $row['password'];
        }

        return $user;
    }

    public function changePassword(bool $initialChange): string
    {
        require 'config_defaults_web.php';
        $username = $_SESSION['username'];
        $password1 = $_POST['password'];
        $password2 = $_POST['password2'];
        $currentPassword = $_POST['passwordCurrent'];

        $user = $this->findUser($username);
        if (!$user->isValid) {
            // This should not happen unless something strange
            // causes the user database to be missing the currently
            // logged in $_SESSION['username']
            return 'Error, could not find current user.';
        }

        // On their initial password set, we will not prompt them
        // for a password, but for sanity, make sure the current
        // password matches the expected default password.
        if ($initialChange) {
            if (!$user->validatePassword($config_defaults_web['PASS'])) {
                // They were attempting to change their password from the
                // initial password change page, but the database password
                // does not match the expected default password.
                return 'Initial password has already been set.<br><a href="login.php">Go to login page</a>';
            }
        } else {
            // This is not the initial password change, so validate
            // against the password in the database.
            if (!$user->validatePassword($currentPassword)) {
                return 'Current password is not correct.';
            }
        }

        // Ensure passwords match, then we can work on one variable.
        if ($password1 !== $password2) {
            return 'Passwords do not match.';
        }

        // Ensure password not same as default.
        if ($password1 === $config_defaults_web['PASS']) {
            return 'Password same as default, use a different password.';
        }

        // Consider additional complexity requirements.
        // For now, at least 8 characters.
        if (strlen($password1) < 8) {
            return 'Password should be 8 characters or longer.';
        }

        // Update the password.
        $user->setPassword($password1);
        try {
            // Persist and save.
            $this->updateUser($user);
            //$this->closeDatabase();
        } catch(\Exception $e) {
            // This should not happen since the user was checked above.
            return 'Error, failed to find and update user.';
        }

        // Successful, no error.
        return '';
    }

    /**
     * Does not support changing username.
     * Only update is password hash.
     *
     * @throws \Exception
     */
    public function updateUser(User $user)
    {
        $foundUser = false;

        $res = $this->db->exec("UPDATE users SET password='$user->passHash' WHERE username = '$user->username'");

        if ($res) {
            $foundUser = true;
        }

        if (!$foundUser) {
            throw new \Exception('Tried to update a non-existent user.');
        }
    }
}
