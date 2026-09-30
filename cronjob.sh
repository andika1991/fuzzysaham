#!/bin/sh

FUZZY_URL="http://localhost:5002"
SENTIMENT_URL="http://localhost:5001"

echo "========================================"
echo "CRON START : $(date)"
echo "========================================"



echo "[1] Fetch data saham..."

curl -s -X POST \
    -H "X-API-Key: ${FUZZY_API_KEY}" \
    "${FUZZY_URL}/stock/fetch?mode=daily"

echo ""


echo "[2] Analisis sentimen..."

curl -s -X POST \
    -H "X-API-Key: ${FUZZY_API_KEY}" \
    "${SENTIMENT_URL}/sentiment/run"

echo ""



echo "[3] Menjalankan Fuzzy Mamdani..."

curl -s -X POST \
    -H "X-API-Key: ${FUZZY_API_KEY}" \
    "${FUZZY_URL}/fuzzy/run"

echo ""


echo "[4] Menjalankan insight OpenAI..."

TICKERS="
BBCA
BBNI
BBRI
BMRI
TLKM
ASII
ICBP
INDF
KLBF
UNTR
"

for TICKER in $TICKERS
do

    echo "Insight ${TICKER}..."

    curl -s -X POST \
        -H "X-API-Key: ${FUZZY_API_KEY}" \
        "${FUZZY_URL}/insight/run?ticker=${TICKER}"

    echo ""

done


echo "========================================"
echo "CRON SELESAI : $(date)"
echo "========================================"