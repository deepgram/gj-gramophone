import argparse
from flask import Flask, flash, request, jsonify, send_file, Response
import logging
import os
import requests
import sys
import base64
from io import BytesIO

### SETUP: FLASK ###
app = Flask('gramophone')

### Setup logger ###
logger = logging.getLogger(__name__)


###############################################################################
def parse_args():
    """ Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Takes in audio and returns transcription + image'
    )
    parser.add_argument('-v', '--verbose', default=0, action='count', help='Increase verbosity.')
    parser.add_argument('-p', '--port', default=8080, type=int, help='Port to listen on.')
    parser.add_argument('-b', '--bind', default='0.0.0.0', help='IP address to bind to.')
    parser.add_argument('-d', '--debug', action="store_true", help='Run in debug mode.')
    return parser.parse_args()


###############################################################################
def configure_logging(verbosity):
    """ Configures logging.
    """
    logging.basicConfig(
        level={
            0 : logging.INFO,
            1 : logging.DEBUG,
        }.get(verbosity, logging.DEBUG),
        format='[%(levelname)s %(asctime)s %(name)s:%(lineno)s] %(message)s'
    )
    logging.captureWarnings(True)


# lists that hold all the images/phrases in the game so far
image_collection = []
phrase_collection = []


### APIs ###
@app.route('/test', methods=['POST'])
def test():
    pass
    # how to return text and image? do we just save an image and return a path?

@app.route('/speech2img', method=['POST'])
def speech2img():
    response = deepgram_consoleASR(
        request.get_data(), headers=request.headers,
        request_kwargs=request.args
    )
    transcript = response.json()[
        'results']['channels'][0]['alternatives'][0]['transcript']
    # pass transcript to `app.config['TEXT_TO_IMG_MODEL']`
    # how to return text and image? do we just save an image and return a path?

    generated_img = generate_image(transcript)
    image_collection.append(imgToBase64(generated_img))
    phrase_collection.append(transcript)

    phrases_and_images = [{"phrase": phrase, "img": img} for phrase, img in zip(phrase_collection, image_collection)]

    return jsonify(phrases_and_images)


def generate_image(prompt: str):
    # generate image from the text via DALL-E
    pass


def imgToBase64(img):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def deepgram_consoleASR(
        data, headers=None, request_kwargs=None,
        baseURL='https://api.deepgram.com', version='v1'
):
    if headers is None:
        headers = {}
    if request_kwargs is None:
        request_kwargs = {}

    url = "{}/{}/listen?".format(baseURL, version)
    request_kwargs = {**request_kwargs, **{'punctuate': 'true'}}
    response = requests.post(
        url, headers=headers, data=data, params=request_kwargs,
        timeout=600
    )
    return response

###############################################################################
def load_global_state():
    # load the text to image model here
    app.config['TEXT_TO_IMG_MODEL'] = None

###############################################################################
def main():
    """ Entrypoint which runs the server."""
    args = parse_args()
    configure_logging(args.verbose)

    logger.info("Loading text-to-image model")
    load_global_state()

    logger.info("Starting the server.")

    app.config['DEBUG'] = args.debug
    app.run(host=args.bind, port=args.port)

###############################################################################
if __name__ == '__main__':
    sys.exit(main() or 0)
