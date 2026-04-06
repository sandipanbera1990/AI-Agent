CREATE DATABASE IF NOT EXISTS support_db;
USE support_db;

CREATE TABLE app_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    last_login DATETIME
);

INSERT INTO app_users (username, email, status, last_login) VALUES
('alice_admin', 'alice@example.com', 'active', '2024-05-10 10:00:00'),
('bob_ops', 'bob@example.com', 'active', '2024-05-09 14:30:00'),
('charlie_dev', 'charlie@example.com', 'locked', '2024-05-01 08:15:00');

CREATE TABLE app_settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(100) NOT NULL
);

INSERT INTO app_settings (setting_key, setting_value) VALUES
('MAX_DB_CONNECTIONS', '100'),
('MAINTENANCE_MODE', 'false'),
('CACHE_STRATEGY', 'redis');
