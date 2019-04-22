import os
import aiml
from flask import Flask

kernel = aiml.Kernel()

for filename in os.listdir("brain"):
    if filename.endswith(".aiml"):
        kernel.learn("brain/" + filename)


app = Flask(__name__)

@app.route("/<query>")
def index(query):
    return kernel.respond(query)

if __name__ == '__main__':
    app.run(debug=True)
