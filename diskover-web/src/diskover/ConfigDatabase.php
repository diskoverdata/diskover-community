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

// diskover-web sqlite3 config database

namespace diskover;
error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE & ~E_DEPRECATED);
use diskover\Constants;
use ReflectionClass;
use SQLite3;

class ConfigDatabase
{
    private $db;
    private $databaseFilename;

    public function connect()
    {
        require 'config_defaults.php';
        // Get datbase file path from config defaults
        $this->databaseFilename = $config_defaults['DATABASE'];

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
        // If the database config table exists and already has config settings, we have nothing to do here.
        $res = $this->db->query("SELECT * FROM sqlite_master WHERE type='table' AND name='config'");
        if ($row = $res->fetchArray()) {
            $res = $this->db->query("SELECT COUNT(*) as count FROM config");
            $row = $res->fetchArray();
            if ($row['count'] > 0) {
                return;
            }
        }

        // Set up sqlite config table if does not yet exist.
        $res = $this->db->exec("CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            value TEXT NOT NULL
        )");

        if (!$res) {
            throw new \Exception('There was an error creating config table!');
        }

        // Add the settings, and save the newly created entries.
        $this->addDefaultSettings();
    }

    protected function addDefaultSettings()
    {
        // Copy existing web config Constants.php into sqlite.
        if (file_exists('../src/diskover/Constants.php')) {
            $this->copyConfigPhpSqlite();
        } else {
            // Copy config defaults into sqlite.
            require 'config_defaults.php';

            foreach ($config_defaults as $configkey => $configval) {
                $this->addConfigSetting($configkey, $configval);
            }
        }
    }

    protected function copyConfigPhpSqlite()
    {
        require 'config_defaults.php';

        $oldconfig = new Constants;
        $refl = new ReflectionClass('diskover\Constants');
        $consts = $refl->getConstants();
        foreach ($config_defaults as $configkey => $configval) {
            if (!array_key_exists($configkey, $consts)) {
                $oldconfig->{$configkey} = $configval;
            } else {
                $oldconfig->{$configkey} = $consts[$configkey];
            }
            $this->addConfigSetting($configkey, $oldconfig->{$configkey});
        }
        // Rename the Constants.php files to .old.
        rename('../src/diskover/Constants.php', '../src/diskover/Constants.php.old');
        rename('../src/diskover/Constants.php.sample', '../src/diskover/Constants.php.sample.old');
    }

    protected function closeDatabase()
    {
        $this->db->close();
    }

    public function getConfigSettings()
    {   
        $res = $this->db->query('SELECT * FROM config');
        $config = array();
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            $val = json_decode($row['value'], JSON_OBJECT_AS_ARRAY);
            // change true and false string to boolean
            if ($val == 'true' || $val == 'false') {
                $val = filter_var($val, FILTER_VALIDATE_BOOLEAN);
            }
            $config[$row['name']] = $val;
        }
        return $config;
    }

    public function addConfigSetting($name, $value)
    {   
        $value_json = json_encode($value);
        $this->db->exec("INSERT INTO config ('name', 'value') 
            VALUES ('$name', '$value_json')");
    }

    public function updateConfigSetting($name, $value)
    {
        $foundSetting = false;
        $value_json = json_encode($value);

        $res = $this->db->exec("UPDATE config SET value='$value_json' WHERE name = '$name'");

        if ($res) {
            $foundSetting = true;
        }

        if (!$foundSetting) {
            throw new \Exception('Tried to update a non-existent config setting.');
        }
    }
}
