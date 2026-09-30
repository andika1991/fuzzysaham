import os
import requests
from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required,current_user
from models import detail
from models.stock import StockModel
from models.detail import StockDetail
from openai import OpenAI
from flask import request, jsonify, current_app, redirect
from models.chat import Conversation, ChatMessage
from flask import abort
from models.fuzzy import FuzzyOutput
from utils.pdf_export import generate_ranking_pdf
from flask import request, render_template, make_response
from models.news import News
from models.dashboard import DashboardModel
from models.dashboard_admin import DashboardAdm

from dotenv import load_dotenv


load_dotenv()

main_bp = Blueprint("main", __name__)
user_bp = Blueprint(
    "user",                # nama blueprint
    __name__,
    url_prefix="/user"     # semua route diawali /user
)
@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    total_saham = DashboardModel.get_total_saham()

    return render_template(
        "user/dashboard.html",
        total_saham=total_saham
    )
@main_bp.route("/user")
@login_required
def user_page():
    if current_user.role != "user":
        return abort(403)

    total_saham = DashboardModel.get_total_saham()
    last_update = DashboardModel.get_last_update()
    total_rekomendasi = DashboardModel.get_total_rekomendasi()
    toprank = DashboardModel.toprank()
    top5_ranking = DashboardModel.get_top5_ranking()
    top_gainer = DashboardModel.get_top_gainer()
    top_loser = DashboardModel.get_top_loser()

    return render_template(
        "user/dashboard.html",
        total_saham=total_saham,
        last_update=last_update,
        total_rekomendasi=total_rekomendasi,
        toprank=toprank,
        top5_ranking=top5_ranking,
        top_gainer=top_gainer,
        top_loser=top_loser

    )

@main_bp.route("/admin")
@login_required
def admin_page():
    if current_user.role != "admin":
        return abort(403)
    total_saham = DashboardModel.get_total_saham()

    rule_count = DashboardAdm.get_rule_count()
    return render_template("admin/dashboard.html", rule_count=rule_count, total_saham=total_saham)

@user_bp.route("/ranking")
@login_required
def ranking():
    tanggal = request.args.get("tanggal")

    available_dates = FuzzyOutput.get_available_dates()

    if not tanggal:
        latest_date = FuzzyOutput.get_latest_date()
        tanggal = latest_date

    ranking_data = []

    if tanggal:
        ranking_data = FuzzyOutput.get_ranking_by_date(tanggal)

    return render_template(
        "user/ranking.html",
        ranking=ranking_data,
        available_dates=available_dates,
        selected_date=tanggal
    )

@user_bp.route("/ranking/pdf")
@login_required
def ranking_pdf():
    tanggal = request.args.get("tanggal")

    if not tanggal:
        tanggal = FuzzyOutput.get_latest_date()

    ranking_data = []

    if tanggal:
        ranking_data = FuzzyOutput.get_ranking_by_date(tanggal)

    pdf = generate_ranking_pdf(ranking_data, tanggal)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=ranking-lq45-{tanggal}.pdf"

    return response

@user_bp.route("/konsultasi")
@login_required
def konsultasi():

    conversations = Conversation.get_all_by_user(current_user.id)

    if conversations:
        active_conversation = conversations[0]
        messages = ChatMessage.get_by_conversation(
            active_conversation["conversation_id"]
        )
    else:
        active_conversation = None
        messages = []

    return render_template(
        "user/konsultasi.html",
        conversations=conversations,
        messages=messages,
        active_conversation=active_conversation
    )


from openai import OpenAI

@user_bp.route("/chat", methods=["POST"])
@login_required
def chat():

    data = request.get_json()
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")

    if not conversation_id:
        conversation_id = Conversation.create(current_user.id)

    ChatMessage.save(
        conversation_id,
        "user",
        user_message
    )
    api_key = os.getenv("CHAT_KEY")  # Ambil API key dari environment variable
    

    # OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    response = client.chat.completions.create(
        model="inclusionai/ling-3.0-flash-sante:free",
        messages=[
            {
                "role": "system",
                "content": "Kamu adalah asisten investasi saham LQ45."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    bot_reply = response.choices[0].message.content

    ChatMessage.save(
        conversation_id,
        "bot",
        bot_reply
    )

    return jsonify({
        "reply": bot_reply,
        "conversation_id": conversation_id
    })


@user_bp.route("/konsultasi/<int:conversation_id>")
@login_required
def open_conversation(conversation_id):

    conversations = Conversation.get_all_by_user(current_user.id)
    messages = ChatMessage.get_by_conversation(conversation_id)

    active_conversation = {
        "conversation_id": conversation_id
    }

    return render_template(
        "user/konsultasi.html",
        conversations=conversations,
        messages=messages,
        active_conversation=active_conversation
    )

@user_bp.route("/new-chat")
@login_required
def new_chat():

    conversation_id = Conversation.create(current_user.id)
    return redirect(f"/user/konsultasi/{conversation_id}")

@user_bp.route("/delete-conversation/<int:conversation_id>", methods=["POST"])
@login_required
def delete_conversation(conversation_id):

    Conversation.delete(conversation_id, current_user.id)

    return jsonify({"success": True})

@user_bp.route("/saham/<ticker>")
@login_required
def detail_saham(ticker):

    tanggal = request.args.get("tanggal")

    if not tanggal:
        tanggal = StockDetail.get_latest_date_by_ticker(ticker)

    detail = StockDetail.get_detail_by_ticker(
        ticker,
        tanggal
    )

    if not detail:
        return "Data saham tidak ditemukan", 404

    membership = StockDetail.get_membership_by_ticker(
        ticker,
        tanggal
    )

    news = StockDetail.get_recent_news(
        ticker,
        tanggal
    )

    performance = StockModel.get_stock_performance(
        detail["id_stock"]
    )

    return render_template(
        "user/detail_saham.html",
        detail=detail,
        membership=membership,
        news=news,
        selected_date=tanggal,
        performance=performance
    )

from datetime import date

@user_bp.route("/berita")
@login_required
def berita():
    selected_date = request.args.get("tanggal")

    if not selected_date:
        selected_date = date.today().strftime("%Y-%m-%d")

    news = News.get_all_news(selected_date)
    available_dates = News.get_available_dates()
    sentiment_summary = News.get_sentiment_summary(selected_date)

    return render_template(
        "user/berita.html",
        news=news,
        available_dates=available_dates,
        selected_date=selected_date,
        sentiment_summary=sentiment_summary
    )

@user_bp.route("/realtime")
@login_required
def realtime_page():

    realtime_data = []
    error_message = None

    try:
        api_key = os.getenv("FUZZY_API_KEY")

        response = requests.get(
            "http://fuzzy_service:5000/realtime/latest",
            headers={
                "X-API-Key": api_key
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        if result.get("status") == "success":
            realtime_data = result.get("data", [])
        else:
            error_message = result.get(
                "message",
                "Gagal mengambil data realtime"
            )

    except Exception as e:
        error_message = str(e)
        print(f"[REALTIME VIEW ERROR] {e}")

    return render_template(
        "user/realtime.html",
        realtime_data=realtime_data,
        error_message=error_message
    )