CREATE TABLE IF NOT EXISTS sentiment_emiten_detail (
    id_sentiment_detail INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    judul TEXT,
    link TEXT,
    sentiment ENUM('positif','netral','negatif') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_news (ticker, link)
);

CREATE TABLE IF NOT EXISTS sentiment_emiten_daily (
    id_sentiment_daily INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment ENUM('positif','netral','negatif') NOT NULL,
    total_berita INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_daily (date, ticker)
);
