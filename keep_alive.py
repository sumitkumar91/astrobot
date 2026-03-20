from threading import Thread
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "AstroBot is alive."


def keep_alive():
    Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
