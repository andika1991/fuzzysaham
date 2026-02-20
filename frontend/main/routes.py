from flask import Blueprint, render_template
from flask_login import login_required,current_user
from models.detail import StockDetail
from openai import OpenAI
from flask import request, jsonify, current_app, redirect
from models.chat import Conversation, ChatMessage
from flask import abort
from models.fuzzy import FuzzyOutput


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
    return render_template("user/dashboard.html")

@main_bp.route("/user")
@login_required
def user_page():
    if current_user.role != "user":
        return abort(403)
    return render_template("user/dashboard.html")


@main_bp.route("/admin")
@login_required
def admin_page():
    if current_user.role != "admin":
        return abort(403)
    return render_template("admin/dashboard.html")

@user_bp.route("/ranking")
@login_required
def ranking():

    ranking_data = FuzzyOutput.get_latest_ranking()

    return render_template(
        "user/ranking.html",
        ranking=ranking_data
    )



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


@user_bp.route("/chat", methods=["POST"])
@login_required
def chat():

    data = request.get_json()
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")

    if not conversation_id:
        conversation_id = Conversation.create(current_user.id)

    ChatMessage.save(conversation_id, "user", user_message)

    client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Kamu adalah asisten investasi saham LQ45."},
            {"role": "user", "content": user_message}
        ]
    )

    bot_reply = response.choices[0].message.content

    ChatMessage.save(conversation_id, "bot", bot_reply)

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

    # Buat conversation baru
    conversation_id = Conversation.create(current_user.id)

    # Redirect langsung ke conversation baru
    return redirect(f"/user/konsultasi/{conversation_id}")

@user_bp.route("/delete-conversation/<int:conversation_id>", methods=["POST"])
@login_required
def delete_conversation(conversation_id):

    Conversation.delete(conversation_id, current_user.id)

    return jsonify({"success": True})

@user_bp.route("/saham/<ticker>")
@login_required
def detail_saham(ticker):

    detail, membership = StockDetail.get_detail_by_ticker(ticker)
    news = StockDetail.get_recent_news(ticker)

    if not detail:
        return "Data tidak ditemukan", 404

    return render_template(
        "user/detail_saham.html",
        detail=detail,
        membership=membership,
        news=news
    )