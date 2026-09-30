from flask import Flask, jsonify, request

from stock_fetcher import fetch_and_save_stock_data
from fuzzy_runner import run_fuzzy
from insight_runner import run_insight
from realtime_recommendation import run_realtime_recommendation
from realtime import get_latest_realtime

from db import (
    get_latest_stock_date,
    stock_data_exists,
    count_stock_data,
    fuzzy_data_exists,
    count_fuzzy_data
)

from datetime import datetime, date
from functools import wraps

import os
from dotenv import load_dotenv

load_dotenv()



app = Flask(__name__)


API_KEY = os.getenv("FUZZY_API_KEY")


def require_api_key(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        client_key = request.headers.get("X-API-Key")

        if not client_key:

            return jsonify({
                "status": "error",
                "message": "Header X-API-Key wajib diberikan."
            }), 401


        # ----------------------------------------------------
        # API KEY SERVER TIDAK TERSEDIA
        # ----------------------------------------------------

        if not API_KEY:

            return jsonify({
                "status": "error",
                "message": "API Key server belum dikonfigurasi."
            }), 500


        # ----------------------------------------------------
        # API KEY SALAH
        # ----------------------------------------------------

        if client_key != API_KEY:

            return jsonify({
                "status": "error",
                "message": "X-API-Key tidak valid."
            }), 403


        return f(*args, **kwargs)


    return decorated


# ============================================================
# VALIDASI TANGGAL
# ============================================================

def parse_date(date_string):

    try:

        return datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return None


# ============================================================
# AMBIL TANGGAL REQUEST
# ============================================================

def get_date_range():

    """
    Jika tidak diberikan tanggal:
        otomatis menggunakan hari ini.

    Jika hanya start_date:
        end_date = start_date.

    Jika menggunakan custom:
        start_date dan end_date digunakan.
    """

    start_date = request.args.get(
        "start_date"
    )

    end_date = request.args.get(
        "end_date"
    )


    # --------------------------------------------------------
    # TIDAK ADA TANGGAL
    # --------------------------------------------------------

    if not start_date and not end_date:

        today = date.today()

        return (
            today,
            today,
            False,
            None
        )


    # --------------------------------------------------------
    # HANYA START DATE
    # --------------------------------------------------------

    if start_date and not end_date:

        end_date = start_date


    # --------------------------------------------------------
    # HANYA END DATE
    # --------------------------------------------------------

    if end_date and not start_date:

        return (
            None,
            None,
            False,
            "Jika menggunakan end_date, start_date juga wajib diisi."
        )


    start = parse_date(
        start_date
    )

    end = parse_date(
        end_date
    )


    if not start:

        return (
            None,
            None,
            False,
            "Format start_date harus YYYY-MM-DD."
        )


    if not end:

        return (
            None,
            None,
            False,
            "Format end_date harus YYYY-MM-DD."
        )

    if start > end:

        return (
            None,
            None,
            False,
            "start_date tidak boleh lebih besar dari end_date."
        )


    is_custom = True

    return (
        start,
        end,
        is_custom,
        None
    )


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "fuzzy-saham"
    })


# ============================================================
# FETCH STOCK DATA
@app.route("/stock/fetch", methods=["POST"])
@require_api_key
def fetch_stock():

    try:

        # ====================================================
        # TENTUKAN MODE
        # ====================================================

        requested_mode = request.args.get(
            "mode"
        )

        # Jika TIDAK ADA mode
        # otomatis mengambil data hari ini
        if not requested_mode:
            requested_mode = "daily"

        requested_mode = requested_mode.lower()


        # ====================================================
        # VALIDASI MODE
        # ====================================================

        if requested_mode not in [
            "daily",
            "custom",
            "full"
        ]:

            return jsonify({
                "status": "error",
                "message": (
                    "Mode tidak valid. "
                    "Gunakan daily, custom, atau full."
                )
            }), 400


        # ====================================================
        # MODE DAILY / CURRENT
        # ====================================================

        if requested_mode == "daily":

            # ------------------------------------------------
            # TANGGAL HARI INI
            # ------------------------------------------------

            today = date.today()


            # ------------------------------------------------
            # BACA DATA YANG SUDAH ADA
            # UNTUK PROSES PERHITUNGAN
            # ------------------------------------------------

            latest_date = get_latest_stock_date()


            # ------------------------------------------------
            # CEK KHUSUS DATA HARI INI
            # ------------------------------------------------

            exists_today = stock_data_exists(
                today,
                today
            )


            # ------------------------------------------------
            # JIKA DATA HARI INI SUDAH ADA
            # ------------------------------------------------

            if exists_today:

                total = count_stock_data(
                    today,
                    today
                )

                return jsonify({

                    "status": "blocked",

                    "message": (
                        "Data saham untuk hari ini "
                        "sudah tersedia dan "
                        "tidak dapat diambil kembali."
                    ),

                    "mode": "daily",

                    "date": str(today),

                    "latest_date": (
                        str(latest_date)
                        if latest_date
                        else None
                    ),

                    "existing_data": total

                }), 409


            # ------------------------------------------------
            # DATA HARI INI BELUM ADA
            # ------------------------------------------------

            # fetch_and_save_stock_data()
            # menggunakan data historis yang sudah ada
            # untuk proses perhitungan rata-rata
            result = fetch_and_save_stock_data(
                mode="daily"
            )


            return jsonify({

                "status": "success",

                "mode": "daily",

                "date": str(today),

                "message": (
                    "Data saham hari ini "
                    "berhasil diambil."
                ),

                "result": result

            }), 200


        # ====================================================
        # MODE FULL
        # ====================================================

        if requested_mode == "full":

            today = date.today()

            try:

                start_date = today.replace(
                    year=today.year - 5
                )

            except ValueError:

                start_date = today.replace(
                    year=today.year - 5,
                    day=28
                )

            end_date = today


            # ------------------------------------------------
            # CEK DATA
            # ------------------------------------------------

            exists = stock_data_exists(
                start_date,
                end_date
            )

            if exists:

                total = count_stock_data(
                    start_date,
                    end_date
                )

                return jsonify({

                    "status": "blocked",

                    "message": (
                        "Data saham 5 tahun "
                        "pada rentang tersebut "
                        "sudah tersedia dan "
                        "tidak dapat diambil kembali."
                    ),

                    "mode": "full",

                    "years": 5,

                    "start_date": str(
                        start_date
                    ),

                    "end_date": str(
                        end_date
                    ),

                    "existing_data": total

                }), 409


            # ------------------------------------------------
            # FETCH 5 TAHUN
            # ------------------------------------------------

            result = fetch_and_save_stock_data(
                mode="full",
                years=5
            )


            return jsonify({

                "status": "success",

                "mode": "full",

                "years": 5,

                "start_date": str(
                    start_date
                ),

                "end_date": str(
                    end_date
                ),

                "message": (
                    "Data saham 5 tahun "
                    "berhasil diambil."
                ),

                "result": result

            }), 200


        # ====================================================
        # MODE CUSTOM
        # ====================================================

        if requested_mode == "custom":

            start_date = request.args.get(
                "start_date"
            )

            end_date = request.args.get(
                "end_date"
            )


            # ------------------------------------------------
            # VALIDASI
            # ------------------------------------------------

            if not start_date:

                return jsonify({

                    "status": "error",

                    "message": (
                        "start_date wajib diisi "
                        "untuk mode custom."
                    )

                }), 400


            if not end_date:

                return jsonify({

                    "status": "error",

                    "message": (
                        "end_date wajib diisi "
                        "untuk mode custom."
                    )

                }), 400


            # ------------------------------------------------
            # PARSE TANGGAL
            # ------------------------------------------------

            start = parse_date(
                start_date
            )

            end = parse_date(
                end_date
            )

            if not start or not end:
                return jsonify({
                    "status": "error",
                    "message": (
                        "Format tanggal harus "
                        "YYYY-MM-DD."
                    )

                }), 400

            if start > end:
                return jsonify({
                    "status": "error",
                    "message": (
                        "start_date tidak boleh "
                        "lebih besar dari end_date."
                    )

                }), 400

            exists = stock_data_exists(
                start,
                end
            )

            if exists:
                total = count_stock_data(
                    start,
                    end
                )
                return jsonify({
                    "status": "blocked",
                    "message": (
                        "Data saham pada "
                        "rentang tanggal tersebut "
                        "sudah tersedia dan "
                        "tidak dapat diambil kembali."
                    ),
                    "mode": "custom",
                    "start_date": str(
                        start
                    ),
                    "end_date": str(
                        end
                    ),
                    "existing_data": total

                }), 409

            result = fetch_and_save_stock_data(
                mode="custom",
                start_date=str(
                    start
                ),
                end_date=str(
                    end
                )
            )

            return jsonify({
                "status": "success",
                "mode": "custom",
                "start_date": str(
                    start
                ),
                "end_date": str(
                    end
                ),
                "message": (
                    "Data saham berhasil diambil."
                ),
                "result": result

            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)

        }), 500

    
@app.route("/fuzzy/run", methods=["POST"])
@require_api_key
def run_fuzzy_api():

    try:


        start_date, end_date, is_custom, error = (
            get_date_range()
        )


        if error:
            return jsonify({
                "status": "error",
                "message": error
            }), 400

        stock_exists = stock_data_exists(
            start_date,
            end_date
        )

        if not stock_exists:

            return jsonify({
                "status": "blocked",
                "message": (
                    "Data saham pada tanggal "
                    "yang diminta belum tersedia. "
                    "Jalankan /stock/fetch terlebih dahulu."
                ),
                "start_date": str(
                    start_date
                ),
                "end_date": str(
                    end_date
                )
            }), 409


        fuzzy_exists = fuzzy_data_exists(
            start_date,
            end_date
        )

        if fuzzy_exists:
            total = count_fuzzy_data(
                start_date,
                end_date
            )
            return jsonify({
                "status": "blocked",
                "message": (
                    "Data fuzzy pada tanggal "
                    "yang diminta sudah diproses "
                    "dan tidak dapat diproses kembali."
                ),
                "mode": (
                    "custom"
                    if is_custom
                    else "daily"
                ),
                "start_date": str(
                    start_date
                ),
                "end_date": str(
                    end_date
                ),
                "existing_fuzzy": total
            }), 409

        mode = (
            "custom"
            if is_custom
            else "daily"
        )

        if mode == "custom":
            result = run_fuzzy(
                mode="custom",
                start_date=str(
                    start_date
                ),
                end_date=str(
                    end_date
                )
            )
        else:
            result = run_fuzzy(
                mode="daily"
            )


        return jsonify({
            "status": "success",
            "mode": mode,
            "start_date": str(
                start_date
            ),
            "end_date": str(
                end_date
            ),
            "message": (
                "Fuzzy berhasil dijalankan."
            ),
            "result": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)

        }), 500



@app.route("/insight/run", methods=["POST"])
@require_api_key
def run_insight_api():

    ticker = request.args.get("ticker")
    tanggal = request.args.get("tanggal")

    try:

        if not ticker:
            return jsonify({
                "status": "error",
                "message": "Parameter ticker wajib diisi."
            }), 400

        ticker = ticker.upper().strip()

        if tanggal:

            try:
                tanggal_obj = datetime.strptime(
                    tanggal,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                return jsonify({
                    "status": "error",
                    "message": (
                        "Format tanggal harus YYYY-MM-DD."
                    )
                }), 400

        else:

            tanggal_obj = None

        result = run_insight(
            ticker=ticker,
            tanggal=tanggal_obj
        )


        if not result:
            return jsonify({
                "status": "error",
                "message": (
                    f"Data fuzzy untuk {ticker} "
                    + (
                        f"tanggal {tanggal}"
                        if tanggal
                        else "tanggal terbaru"
                    )
                    + " tidak ditemukan."
                ),

                "ticker": ticker,

                "tanggal": (
                    str(tanggal_obj)
                    if tanggal_obj
                    else None
                )

            }), 404


        # ====================================================
        # SUCCESS
        # ====================================================

        return jsonify({
            "status": "success",
            "ticker": ticker,
            "tanggal": (
                str(tanggal_obj)
                if tanggal_obj
                else None
            ),
            "data": result
        }), 200


    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/realtime/run", methods=["POST"])
@require_api_key
def run_realtime_api():
    try:
        result = run_realtime_recommendation()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/realtime/latest", methods=["GET"])
@require_api_key
def realtime_latest_api():

    try:

        data = get_latest_realtime()

        return jsonify({
            "status": "success",
            "total": len(data),
            "data": data
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False

    )