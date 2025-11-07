#!/bin/bash

# MySQL setup for KV Store

echo "Setting up MySQL database for KV Store..."
echo ""

sudo mysql <<EOF
-- Create database
CREATE DATABASE IF NOT EXISTS kvstore_db;

-- Allow root with empty password (auth_socket to mysql_native_password)
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';

-- Create table
USE kvstore_db;
CREATE TABLE IF NOT EXISTS kv_pairs (
    kv_key VARCHAR(255) PRIMARY KEY,
    kv_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create hash table (using text prefix + hash to avoid both size limits AND collisions)
CREATE TABLE IF NOT EXISTS hash_store (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    text_prefix VARCHAR(255) NOT NULL,  -- First 255 chars of text
    text_hash CHAR(32) NOT NULL,        -- Hash for quick filtering
    text TEXT NOT NULL,                 -- Full text content
    hash_value BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_text_combo (text_prefix, text_hash),  -- Composite unique key
    INDEX idx_hash (text_hash)          -- Fast hash-based lookups
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

FLUSH PRIVILEGES;

-- Show result
SELECT 'Setup complete!' as Status;
SHOW TABLES;
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ MySQL setup complete!"
    echo ""
    echo "Database: kvstore_db"
    echo "User: root"
    echo "Password: (empty)"
else
    echo ""
    echo "✗ Setup failed"
fi
