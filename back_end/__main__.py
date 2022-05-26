import argparse
from flask import Flask, flash, request, jsonify, send_file, Response
import logging
import requests
import sys


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



### APIs ###
@app.route('/test', methods=['GET'])
def test():
    return "Hello world"
    # how to return text and image? do we just save an image and return a path?

@app.route('/speech2img', methods=['POST'])
def speech2img():
    response = deepgram_consoleASR(
        request.get_data(), headers=request.headers,
        request_kwargs=request.args
    )
    transcript = response.json()[
        'results']['channels'][0]['alternatives'][0]['transcript']

    generated_img = generate_image(transcript)

    return jsonify({"prompt": transcript, "img": generated_img})


def generate_image(prompt: str):
    response = requests.post("http://sv1-j.node.sv1.consul:8093/dalle", json={"text": prompt, "num_images": 1})
    img_str = response.json()[0]

    return img_str

    # img_data = base64.b64decode(img_str)
    # with open("gramophone.jpg", "wb") as f:
    #     f.write(img_data)

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
