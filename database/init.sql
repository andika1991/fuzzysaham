CREATE DATABASE IF NOT EXISTS fuzzy_saham;
USE fuzzy_saham;

-- =====================
-- USER & CHAT
-- =====================
CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(255),
    role VARCHAR(20)
);

CREATE TABLE conversation (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME,
    last_update DATETIME,
    user_id INT,
    CONSTRAINT fk_conversation_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE CASCADE
);

CREATE TABLE chat_messages (
    id_chatmessages INT AUTO_INCREMENT PRIMARY KEY,
    sender VARCHAR(20),
    message_text VARCHAR(500),
    created_at DATETIME,
    conversation_id INT,
    CONSTRAINT fk_chat_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversation(conversation_id)
        ON DELETE CASCADE
);



CREATE TABLE stock_lq45 (
    id_stock INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE,
    nama_perusahaan VARCHAR(100),
    sektor VARCHAR(50),
    industri VARCHAR(50)
);

CREATE TABLE stock_data (
    stockdata_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    close_price DECIMAL(12,2),
    eps FLOAT,
    per FLOAT,
    roe FLOAT,
    der FLOAT,
    fcf FLOAT,
    ma50 FLOAT,
    ma200 FLOAT,
    volume BIGINT,
    volma200 BIGINT,
    rsi INT,
    sentimen VARCHAR(20),
    id_stock INT,
    CONSTRAINT fk_stockdata_stock
        FOREIGN KEY (id_stock)
        REFERENCES stock_lq45(id_stock)
        ON DELETE CASCADE
);



CREATE TABLE rule (
    id_rule INT AUTO_INCREMENT PRIMARY KEY,
    eps VARCHAR(10),
    per VARCHAR(10),
    roe VARCHAR(10),
    der VARCHAR(10),
    fcf VARCHAR(10),
    ma50 VARCHAR(10),
    ma200 VARCHAR(10),
    volume VARCHAR(10),
    rsi VARCHAR(15),
    sentimen VARCHAR(10),
    output VARCHAR(20),
    horizon VARCHAR(50)
);

CREATE TABLE fuzzy_membership (
    id_fuzzymembership INT AUTO_INCREMENT PRIMARY KEY,
    eps_level VARCHAR(10),
    per_level VARCHAR(10),
    roe_level VARCHAR(10),
    der_level VARCHAR(10),
    fcf_level VARCHAR(10),
    trend_ma50 VARCHAR(10),
    trend_ma200 VARCHAR(10),
    rsi_level VARCHAR(15),
    volume_level VARCHAR(10),
    sentimen_level VARCHAR(10),
    stockdata_id INT,
    CONSTRAINT fk_membership_stockdata
        FOREIGN KEY (stockdata_id)
        REFERENCES stock_data(stockdata_id)
        ON DELETE CASCADE
);

CREATE TABLE fuzzy_output (
    output_id INT AUTO_INCREMENT PRIMARY KEY,
    fuzzy_score FLOAT,
    kategori VARCHAR(20),
    insight VARCHAR(100),
    horizon VARCHAR(50),
    stockdata_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_output_stockdata
        FOREIGN KEY (stockdata_id)
        REFERENCES stock_data(stockdata_id)
        ON DELETE CASCADE
);


CREATE TABLE sentiment_emiten_detail (
    id_sentiment_detail INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    judul TEXT,
    link TEXT,
    sentiment ENUM('positif','netral','negatif') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_news (ticker, link)
);


CREATE TABLE sentiment_emiten_daily (
    id_sentiment_daily INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment ENUM('positif','netral','negatif') NOT NULL,
    total_berita INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_daily (date, ticker)
);
