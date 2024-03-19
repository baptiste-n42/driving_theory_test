import uuid
import random
import time
import sqlite3
from datetime import datetime, timedelta, timezone

import math
from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
from flask_jwt_extended import (
    jwt_required,
    JWTManager,
    create_access_token,
    set_access_cookies,
    get_jwt,
    unset_jwt_cookies,
)

# --- GLOBAL VARIABLES ---
MINI_NUMBER_OF_QUESTIONS = 10
FULL_NUMBER_OF_QUESTIONS = 50
SECONDS_PER_QUESTION = 60
YEAR = time.localtime().tm_year

# initiates app
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
jwt = JWTManager(app)


# this function given a question ID returns information for that question from the SQL database
def get_question_id(q_id):
    db = sqlite3.connect("question_bank.db")
    cursor = db.cursor()

    rows = cursor.execute(
        "SELECT * FROM question_bank WHERE q_id = ?",
        (q_id,),
    ).fetchall()
    return rows[0]


def get_all_questions_id():
    db = sqlite3.connect("question_bank.db")
    cursor = db.cursor()

    rows = cursor.execute(
        "SELECT q_id FROM question_bank",
    ).fetchall()
    return rows


def format_duration(value: float):
    return datetime.fromtimestamp(value).strftime("%Mm %Ssec")


def update_user_token(
        resp,
        claims: dict,
        exam_type=None,
        exam_mode=None,
        number_of_questions=None,
        end_exam=None,
        answers=None,
        current_index=None,
        score=None,
        time_elapsed=None,
        start_time=None,
        time_remaining=None,
):
    exam_data = {
        "exam_type": exam_type or claims.get("exam_type"),
        "exam_mode": exam_mode or claims.get("exam_mode"),
        "number_of_questions": number_of_questions or claims.get("number_of_questions"),
        "end_exam": end_exam or claims.get("end_exam"),
        "answers": answers or claims.get("answers"),
        "current_index": current_index or claims.get("current_index", 0),
        "score": score or claims.get("score"),
        "time_elapsed": time_elapsed or claims.get("time_elapsed"),
        "start_time": start_time or claims.get("start_time"),
        "time_remaining": time_remaining or claims.get("time_remaining"),
    }
    set_access_cookies(resp, create_access_token(claims.get("sub"), additional_claims=exam_data))


def create_question_bank(nb_q=50):
    # creates a list of distinct random ints from 1-150
    all_questions = get_all_questions_id()
    questions = []
    for _ in range(nb_q):
        selected_q = random.choices(all_questions)
        questions.append(selected_q[0][0])
        all_questions.pop(all_questions.index(selected_q[0]))

    return questions


@app.route("/")
def home():
    return render_template(
        "cover.html",
        year=YEAR,
        full_questions=FULL_NUMBER_OF_QUESTIONS,
        full_time=(int((FULL_NUMBER_OF_QUESTIONS * SECONDS_PER_QUESTION) / 60)),
        mini_questions=MINI_NUMBER_OF_QUESTIONS,
        mini_time=(int((MINI_NUMBER_OF_QUESTIONS * SECONDS_PER_QUESTION) / 60)),
    )


@app.route("/exam/is_correct", methods=["POST"])
def is_correct():
    claims = get_jwt()
    answers: list = claims.get("answers")
    question = get_question_id(answers[claims.get("current_index")][0])

    return jsonify({"ans_id": question[11]})


@app.route("/exam/results")
@jwt_required()
def results():
    claims = get_jwt()
    current_index = claims.get("current_index")
    answers: list = claims.get("answers")
    time_elapsed: float = claims.get("time_elapsed")
    time_remaining: float = claims.get("time_remaining")
    number_of_questions: int = int(claims.get("number_of_questions"))
    time_up = False
    if datetime.now().timestamp() > claims.get("end_exam"):
        time_up = True
    failed_questions = []
    score = 0
    #  Compute result
    for answer in answers:
        question = get_question_id(answer[0])
        if question[11] == answer[1]:
            score += 1
        else:
            wrong_answer = {
                "true_answer": question[11],
                "quest_txt": question[1],
                "quest_pic": question[2],
                "user_txt": None,
                "user_pic": None,
                "true_txt": question[12],
                "true_pic": None,
                "q_id": question[0],
            }
            if answer[1] == "1":
                wrong_answer["user_txt"] = question[3]
                wrong_answer["user_pic"] = question[4]
            elif answer[1] == "2":
                wrong_answer["user_txt"] = question[5]
                wrong_answer["user_pic"] = question[6]
            elif answer[1] == "3":
                wrong_answer["user_txt"] = question[7]
                wrong_answer["user_pic"] = question[8]
            elif answer[1] == "4":
                wrong_answer["user_txt"] = question[9]
                wrong_answer["user_pic"] = question[10]
            failed_questions.append(wrong_answer)

    percent_s = int((score / number_of_questions) * 100)
    pass_fail = "FAIL🥹"
    if percent_s >= 90:
        pass_fail = "PASS🥳"

    if not time_elapsed or not time_remaining:
        time_elapsed = datetime.now().timestamp() - float(claims.get("start_time"))
        time_remaining = float(claims.get("end_exam")) - datetime.now().timestamp()

    resp = make_response(
        render_template(
            "results.html",
            year=YEAR,
            total_quest=number_of_questions,
            total_correct=score,
            pass_fail=pass_fail,
            percent_score=percent_s,
            time_elapsed=format_duration(time_elapsed),
            time_remaining=format_duration(time_remaining),
            time_up=time_up,
            time_per_quest=math.ceil(time_elapsed / number_of_questions),
            failed_questions=failed_questions,
        )
    )
    update_user_token(
        resp,
        claims,
        answers=answers,
        current_index=current_index,
        time_elapsed=time_elapsed,
        score=score,
        time_remaining=time_remaining,
    )
    return resp


# standard question page template
@app.route("/exam/", methods=["GET", "POST"])
@jwt_required()
def exam():
    claims = get_jwt()
    if claims.get("score", False):
        return redirect(url_for("results"))
    current_index = claims.get("current_index")
    answers: list = claims.get("answers")
    exam_mode: bool = claims.get("exam_mode")
    number_of_questions: int = int(claims.get("number_of_questions"))

    seconds_left = float(claims.get("end_exam")) - datetime.now().timestamp()

    # check for time up. If so, send user to results page
    if datetime.now().timestamp() > claims.get("end_exam"):
        return make_response(redirect(url_for("results")))
    if current_index >= len(answers):
        # End exam
        return redirect(url_for("results"))
    # update question bank with info from previous question
    if request.method == "POST":
        data = request.form
        # answer == 0 means the user clicked 'previous' or 'next' button, question bank should not be updated
        if data["Answer"] != "0":
            answers[current_index][1] = data["Answer"]
        current_index += 1
        resp = make_response(redirect(url_for("exam")))
    else:
        question = get_question_id(answers[current_index][0])
        question_formatted = {
            "id": question[0],
            "question_text": question[1],
            "question_pic": question[2],
            "answers": {
                "1": {
                    "text": question[3],
                    "pic": question[4]
                },
                "2": {
                    "text": question[5],
                    "pic": question[6]
                },
                "3": {
                    "text": question[7],
                    "pic": question[8]
                },
                "4": {
                    "text": question[9],
                    "pic": question[10]
                },
            }
        }

        resp = make_response(
            render_template(
                "question.html",
                year=YEAR,
                total=number_of_questions,
                question=question_formatted,
                current_index=current_index,
                exam_mode=exam_mode,
                seconds=seconds_left,
                progress=int((current_index / number_of_questions) * 100),
            )
        )

    update_user_token(resp, claims, answers=answers, current_index=current_index)
    # serves up new question data to template
    return resp


# user navigates backwards using "previous button", revised question page template
@app.route("/exam/p", methods=["GET", "POST"])
@jwt_required()
def previous_exam():
    claims = get_jwt()
    current_index = claims.get("current_index")
    if current_index > 0:
        current_index -= 1
    resp = make_response(redirect(url_for("exam")))
    update_user_token(resp, claims, current_index=current_index)
    return resp


@app.route("/exam/start_exam", methods=["POST"])
@jwt_required()
def start_exam():
    claims = get_jwt()
    resp = make_response(redirect(url_for("exam")))
    update_user_token(
        resp,
        claims,
        current_index=0,
        start_time=datetime.now().timestamp(),
        end_exam=datetime.now().timestamp() + int(claims.get("number_of_questions")) * SECONDS_PER_QUESTION,
    )
    return resp


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    resp = make_response(redirect(url_for("home")))
    unset_jwt_cookies(resp)
    return resp


# Pre-exam page with instructions for user
@app.route("/pre-exam/", methods=["GET", "POST"])
def pre_exam():
    exam_type = ""
    data = request.form

    if request.method == "POST":
        exam_type = data["Length"]
    if exam_type == "Full Exam":
        number_of_questions = FULL_NUMBER_OF_QUESTIONS
    else:
        number_of_questions = MINI_NUMBER_OF_QUESTIONS

    create_question_bank()

    resp = make_response(
        render_template("pre-exam.html", year=YEAR, minutes=number_of_questions, questions=number_of_questions)
    )

    exam_data = {
        "exam_type": exam_type,
        "exam_mode": True if data.get("exam_mode", False) else False,
        "number_of_questions": str(number_of_questions),
        "answers": [],
    }
    for selected_question in create_question_bank(number_of_questions):
        # Q_id, user answer
        exam_data["answers"].append(
            (
                selected_question,
                0,
            )
        )
    set_access_cookies(resp, create_access_token(uuid.uuid4().hex[:10].upper(), additional_claims=exam_data))
    return resp


# About page
@app.route("/about/")
def about():
    return render_template("about.html", year=YEAR)


if __name__ == "__main__":
    app.run(debug=True)
