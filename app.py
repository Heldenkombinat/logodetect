import os
from flask import (
    Flask,
    flash,
    request,
    redirect,
    url_for,
    send_from_directory,
    after_this_request,
)
from werkzeug.utils import secure_filename
from logodetect import Recognizer, PATH_DATA
from logodetect.recognizer import append_to_file_name

PATH_EXEMPLARS = os.path.join(PATH_DATA, "exemplars_100x100_aug")
UPLOAD_FOLDER = "."
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

RECOGNIZER = Recognizer(exemplars_path=PATH_EXEMPLARS)


def allowed_file(filename):
    """Check if this is an allowed file extension.

    :param filename: name of the file to upload
    :return: boolean
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def predict_image():
    """HTTP request for either rendering the upload form (GET) or
    sending the request form data to the logo detector and returning
    the resulting image (POST).

    :return:
    """
    if request.method == "POST":
        if "image" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["image"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            local_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(local_file)
            RECOGNIZER.predict_image(local_file)
            os.remove(local_file)
            prediction = append_to_file_name(filename, "_output")
            return redirect(url_for("processed_image", image=prediction))
    return """
    <!doctype html>
    <title>Upload image file for detection</title>
    <h1>Upload image file for detection</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=image>
      <input type=submit value=Upload>
    </form>
    """


@app.route("/<image>")
def processed_image(image: str):
    """Return prediction and clean up temp file after sending.

    :param image: predicted image file name
    :return: the image itself
    """

    @after_this_request
    def remove_file(response):
        try:
            os.remove(image)
        except Exception as error:
            app.logger.error("Error removing downloaded file", error)
        return response

    return send_from_directory(app.config["UPLOAD_FOLDER"], image)


if __name__ == "__main__":
    app.run()
