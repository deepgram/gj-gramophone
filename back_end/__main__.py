import argparse
from flask import Flask, flash, request, jsonify, send_file, Response
import logging
import os
import requests
import sys
import base64
from io import BytesIO
from dalle_mini import DalleBart, DalleBartProcessor
from functools import partial

import jax
import random
import numpy as np
import jax.numpy as jnp
from PIL import Image
from vqgan_jax.modeling_flax_vqgan import VQModel

from flax.jax_utils import replicate
from flax.training.common_utils import shard_prng_key


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


# model

DALLE_MODEL = "dalle-mini/dalle-mini/wzoooa1c:latest"
DALLE_COMMIT_ID = None
model = DalleBart.from_pretrained(DALLE_MODEL, revision=DALLE_COMMIT_ID)
model._params = replicate(model.params)
processor = DalleBartProcessor.from_pretrained(DALLE_MODEL, revision=DALLE_COMMIT_ID)

# VQGAN model
VQGAN_REPO = "dalle-mini/vqgan_imagenet_f16_16384"
VQGAN_COMMIT_ID = "e93a26e7707683d349bf5d5c41c5b0ef69b677a9"
vqgan = VQModel.from_pretrained(VQGAN_REPO, revision=VQGAN_COMMIT_ID)
vqgan._params = replicate(vqgan.params)


gen_top_k = None
gen_top_p = 0.9
temperature = None
cond_scale = 3.0

# model inference
@partial(jax.pmap, axis_name="batch", static_broadcasted_argnums=(3, 4, 5, 6))
def p_generate(tokenized_prompt, key, params, top_k, top_p, temperature, condition_scale):
    return model.generate(
        **tokenized_prompt,
        prng_key=key,
        params=params,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        condition_scale=condition_scale,
    )


# decode images
@partial(jax.pmap, axis_name="batch")
def p_decode(indices, params):
    return vqgan.decode_code(indices, params=params)

  
def tokenize_prompt(prompt: str):
  tokenized_prompt = processor([prompt])
  return replicate(tokenized_prompt)



### APIs ###
@app.route('/test', methods=['GET'])
def test():
    return "Hello world"
    # how to return text and image? do we just save an image and return a path?

@app.route('/speech2img', methods=['POST'])
def speech2img():
    # response = deepgram_consoleASR(
    #     request.get_data(), headers=request.headers,
    #     request_kwargs=request.args
    # )
    # transcript = response.json()[
    #     'results']['channels'][0]['alternatives'][0]['transcript']

    transcript = request.json["text"]
    # print(transcript)
    
    # pass transcript to `app.config['TEXT_TO_IMG_MODEL']`
    # how to return text and image? do we just save an image and return a path?

    generated_img = generate_image(transcript)
    image_collection.append(imgToBase64(generated_img))
    phrase_collection.append(transcript)

    phrases_and_images = [{"phrase": phrase, "img": img} for phrase, img in zip(phrase_collection, image_collection)]

    return jsonify(phrases_and_images)
    # return transcript


def generate_image(prompt: str):
    # generate image from the text via DALL-E
    tokenized_prompt = tokenize_prompt(prompt)
    
    # create a random key
    seed = random.randint(0, 2**32 - 1)
    key = jax.random.PRNGKey(seed)

    key, subkey = jax.random.split(key)
    
    encoded_image = p_generate(tokenized_prompt, shard_prng_key(subkey),
        model.params, gen_top_k, gen_top_p, temperature, cond_scale,
    )
    
    # remove BOS
    encoded_image = encoded_image.sequences[..., 1:]

    # decode images
    decoded_image = p_decode(encoded_image, vqgan.params)
    decoded_image = decoded_image.clip(0.0, 1.0).reshape((-1, 256, 256, 3))
    image = Image.fromarray(np.asarray(img * 255, dtype=np.uint8))
            
    return image


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
