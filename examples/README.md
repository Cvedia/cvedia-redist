## Method 1: Upload all images then annotations

#### Concept 

You can upload arbitrary images to the system, without any annotation, as long
they pertain to a subset (train, validation or test).

This data can be then annotatated on the site using the tools or thuru the api
via json files.

#### How to

The system will bind annotations to images based on the `image_path` you send,
when uploading the image via the api / ftp / site the file path will be saved,
this path can then be referred when adding an annotation to that image in specific.

Keep in mind that the `image_path` is relative, so if you have subfolders they
will be preserved; With the API you can provide any `image_path`.

If you send an annotation with a `image_path` that the system cannot bind a image
to, it will fail, this means that you must always upload the image before sending
an annotation.

#### Example files

- `image.json`: Contains the `image.png` as base64, without any annotations (note that the image could be uploaded via url, ftp or ui)
- `annotation.json`: Contains a annotation to `image.png` with `image_path` reference
- `image.png`: This is not required for the test, since the image is sent as base64

#### Running

You must upload the image first:

`python cvedia_api.py --dataset_index <index_name> --upload examples/image.json`

Then add the annotation:

`python cvedia_api.py --dataset_index <index_name> --upload examples/annotation.json`

## Method 2: Upload a combination of images and annotations

#### Concept

If you happen to have annotations for the images you want to add to the system
you might just upload them among with the images, this makes ingestion process
faster since the system will do a single pass to collect all the information.

#### How to

Different from the first method, instead of sending a image_path, you will simply
send the image as base64 or a url for the system to fetch it externally among with
an annotation stack.

Note that the annotation stack is optional, so if you happen to have images without
annotations among the ones with annotations it's not a problem, both can be
uploaded using the same method.

#### Example files

- `url_example.json`: Contains a few image urls with annotations

#### Running

`python cvedia_api.py --dataset_index <index_name> --upload examples/url_example.json`

## Hints

- Some of CVEDIA ingestion services are asyncronous, meaning that not all you upload will be instantly available, depending on the system load, image type, queues, etc.
- Ideally you'd upload bulks of json objects containing much information as possible, this way data ingestion would be less fragmented, therefore way faster than sending a million small requests.
