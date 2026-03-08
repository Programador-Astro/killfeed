from flask import Flask, render_template
from stats import leaderboard, destaques

app = Flask(__name__)


@app.route("/")
def home():

    ranking = leaderboard()
    destaque = destaques()

    return render_template(
        "index.html",
        ranking=ranking,
        destaque=destaque
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )