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
        $this->setupDatabaseConfig('configweb');
        $this->setupDatabaseConfig('configdiskover');
    }

    protected function setupDatabaseConfig($table)
    {
        // If the database table exists and already has config settings, we have nothing to do here.
        $res = $this->db->query("SELECT * FROM sqlite_master WHERE type='table' AND name='" . $table . "'");
        if ($row = $res->fetchArray()) {
            $res = $this->db->query("SELECT COUNT(*) as count FROM $table");
            $row = $res->fetchArray();
            if ($row['count'] > 0) {
                return;
            }
        }

        // Set up sqlite config table if does not yet exist.
        $res = $this->db->exec("CREATE TABLE IF NOT EXISTS $table (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            value TEXT,
            UNIQUE(name)
        )");

        if (!$res) {
            throw new \Exception('There was an error creating ' . $table . ' table!');
        }

        // Add the settings, and save the newly created entries.
        $this->addDefaultSettings($table);
    }

    protected function addDefaultSettings($table)
    {
        if ($table === 'configweb') {
            // Copy existing web config Constants.php into sqlite.
            if (file_exists('../src/diskover/Constants.php')) {
                $this->copyConfigPhpSqlite();
            } else {
                // Copy config defaults into sqlite.
                require 'config_defaults_web.php';

                foreach ($config_defaults_web as $configkey => $configval) {
                    $this->addConfigSetting('configweb', $configkey, $configval);
                }
            }
        } elseif ($table === 'configdiskover') {
            // Copy diskover config defaults into sqlite.
            require 'config_defaults_diskover.php';

            foreach ($config_defaults_diskover as $configkey => $configval) {
                $this->addConfigSetting('configdiskover', $configkey, $configval);
            }
        }
    }

    protected function copyConfigPhpSqlite()
    {
        require 'config_defaults_web.php';

        $oldconfig = new Constants;
        $refl = new ReflectionClass('diskover\Constants');
        $consts = $refl->getConstants();
        foreach ($config_defaults_web as $configkey => $configval) {
            if (!array_key_exists($configkey, $consts)) {
                $oldconfig->{$configkey} = $configval;
            } else {
                $oldconfig->{$configkey} = $consts[$configkey];
            }
            $this->addConfigSetting('configweb', $configkey, $oldconfig->{$configkey});
        }
        // Rename the Constants.php files to .old.
        rename('../src/diskover/Constants.php', '../src/diskover/Constants.php.old');
        rename('../src/diskover/Constants.php.sample', '../src/diskover/Constants.php.sample.old');
    }

    public function getConfigSettings($table)
    {   
        // Get diskover-web config settings
        $config = array();
        $res = $this->db->query("SELECT * FROM $table");
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            // decode json string and handle non encoded
            $val = json_decode($row['value'], JSON_OBJECT_AS_ARRAY);
            // change true and false string to boolean
            if ($val == 'true' || $val == 'false') {
                $val = filter_var($val, FILTER_VALIDATE_BOOLEAN);
            }
            $config[$row['name']] = $val;
        }
        return $config;
    }

    public function getESConfigSettings()
    {
        $diskover_config = $this->getConfigSettings('configdiskover');
        $web_config = $this->getConfigSettings('configweb');
        $all_config = array_merge($diskover_config, $web_config);
        $es_config = array();
        foreach ($all_config as $key => $value) {
            if (preg_match("/^ES_/", $key)) {
                $es_config[$key] = $value;
            }
        }
        return $es_config;
    }

    public function addConfigSetting($table, $name, $value)
    {
        $value = json_encode($value);
        $this->db->exec("INSERT OR IGNORE INTO $table ('name', 'value') 
            VALUES ('$name', '$value')");
    }

    public function updateConfigSetting($table, $name, $value)
    {
        $foundSetting = false;
        $value = json_encode($value);

        $res = $this->db->exec("UPDATE $table SET value='$value' WHERE name = '$name'");

        if ($res) {
            $foundSetting = true;
        }

        if (!$foundSetting) {
            throw new \Exception('Tried to update a non-existent config setting.');
        }
    }

    protected function closeDatabase()
    {
        $this->db->close();
    }
}
