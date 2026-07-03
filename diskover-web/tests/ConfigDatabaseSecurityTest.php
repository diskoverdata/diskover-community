<?php

require_once __DIR__ . '/../src/diskover/ConfigDatabase.php';

use diskover\ConfigDatabase;

function assertSameValue($expected, $actual, $message)
{
    if ($expected !== $actual) {
        fwrite(STDERR, $message . PHP_EOL);
        fwrite(STDERR, 'Expected: ' . var_export($expected, true) . PHP_EOL);
        fwrite(STDERR, 'Actual: ' . var_export($actual, true) . PHP_EOL);
        exit(1);
    }
}

function assertThrows($callback, $message)
{
    try {
        $callback();
    } catch (Exception $e) {
        return;
    }

    fwrite(STDERR, $message . PHP_EOL);
    exit(1);
}

$databaseFile = tempnam(sys_get_temp_dir(), 'diskover-config-test-');
$sqlite = new SQLite3($databaseFile);
$sqlite->exec("CREATE TABLE configweb (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, value TEXT, UNIQUE(name))");
$sqlite->exec("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL)");
$sqlite->exec("INSERT INTO configweb (name, value) VALUES ('SAFE_SETTING', '\"old\"')");
$sqlite->exec("INSERT INTO users (username, password) VALUES ('admin', 'original')");

$configDatabase = new ConfigDatabase();
$reflection = new ReflectionClass($configDatabase);
$dbProperty = $reflection->getProperty('db');
$dbProperty->setAccessible(true);
$dbProperty->setValue($configDatabase, $sqlite);

$configDatabase->updateConfigSetting('configweb', 'SAFE_SETTING', 'new value');
$storedValue = $sqlite->querySingle("SELECT value FROM configweb WHERE name = 'SAFE_SETTING'");
assertSameValue('new value', json_decode($storedValue), 'Normal config update did not preserve expected behavior.');

$configDatabase->updateConfigSetting('configweb', 'SAFE_SETTING', "safe'; UPDATE users SET password='pwned");
$password = $sqlite->querySingle("SELECT password FROM users WHERE username = 'admin'");
assertSameValue('original', $password, 'Stacked SQL in a config value modified the users table.');

$configDatabase->updateConfigSetting('configweb', "SAFE_SETTING'; UPDATE users SET password='pwned", 'ignored');
$password = $sqlite->querySingle("SELECT password FROM users WHERE username = 'admin'");
assertSameValue('original', $password, 'Stacked SQL in a config name modified the users table.');

assertThrows(function () use ($configDatabase) {
    $configDatabase->updateConfigSetting("configweb; UPDATE users SET password='pwned'", 'SAFE_SETTING', 'ignored');
}, 'Invalid config table name was accepted.');

$sqlite->close();
unlink($databaseFile);

echo "ConfigDatabaseSecurityTest passed\n";
