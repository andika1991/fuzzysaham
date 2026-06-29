from flask import Flask, jsonify, request
from stock_fetcher import fetch_and_save_stock_data
from fuzzy_runner import run_fuzzy   # ← fungsi fuzzy inference
from insight_runner import run_insight

app = Flask(__name__)

# =====================================================
# HEALTH CHECK
# =====================================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "fuzzy-saham",
    })


# =====================================================
# FETCH STOCK DATA
# =====================================================
@app.route("/stock/fetch", methods=["POST"])
def fetch_stock():

    mode = request.args.get("mode", "daily")

    try:
        result = fetch_and_save_stock_data(mode=mode)
        return jsonify({
            "status": "success",
            "mode": mode,
            "result": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =====================================================
# RUN FUZZY ENGINE
# =====================================================
@app.route("/fuzzy/run", methods=["POST"])
def run_fuzzy_api():

    try:
        result = run_fuzzy()
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/insight/run", methods=["POST"])
def run_insight_api():
    ticker = request.args.get("ticker")  # optional
    result = run_insight(ticker)
    return jsonify({
        "status": "success",
        "data": result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
