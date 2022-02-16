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

// diskover-web community edition (ce) json user database

namespace diskover;

class UserDatabase
{
    private $data;

    // Consider moving to Constants.php
    // Ensure file is not in /public/ folder.
    private $databaseFilename = '../diskover.json';

    public function connect()
    {
        // Initial setup if necessary.
        $this->setupDatabase();

        // Load data into memory.
        $rawData = file_get_contents($this->databaseFilename);
        $this->data = json_decode($rawData, JSON_OBJECT_AS_ARRAY);
    }

    protected function setupDatabase()
    {
        // If the database file already exists, we have nothing to do here.
        if (file_exists($this->databaseFilename)) {
            return;
        }

        // Since the database file does not exist,
        // create the file, and adjust the permissions.
        // Note: Not using umask since it is not thread safe.
        touch($this->databaseFilename);
        // Fix permissions so only current user can read/write.
        chmod($this->databaseFilename, 0600);

        // Grab config data and create initial user.
        $user = new User();
        $user->username = Constants::USER;
        $user->setPassword(Constants::PASS);

        // Add the user, and save the newly created entry.
        $this->addUser($user);
        $this->writeDatabase();
    }

    protected function addUser(User $user)
    {
        $this->data['users'][] = [
            'username' => $user->username,
            'password' => $user->passHash,
        ];
    }

    protected function writeDatabase()
    {
        file_put_contents(
            $this->databaseFilename,
            json_encode($this->data)
        );
    }

    public function findUser($username): User
    {
        $user = new User();

        foreach($this->data['users'] as $userData) {
            if ($userData['username'] !== $username) {
                continue;
            }

            // Found a username match.
            $user->isValid = true;
            $user->username = $userData['username'];
            $user->passHash = $userData['password'];
        }

        return $user;
    }

    public function changePassword(bool $initialChange): string
    {
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
            if (!$user->validatePassword(Constants::PASS)) {
                // They were attempting to change their password from the
                // initial password change page, but the database password
                // does not match the expected default password.
                return 'Initial password has already been set.<br><a href="/login.php">Go to login page</a>';
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
            $this->writeDatabase();
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

        foreach($this->data['users'] as $k => $userData) {
            if ($userData['username'] !== $user->username) {
                continue;
            }

            // Found a username match.
            $foundUser = true;
            $this->data['users'][$k]['password'] = $user->passHash;
        }

        if (!$foundUser) {
            throw new \Exception('Tried to update a non-existent user.');
        }
    }
}
