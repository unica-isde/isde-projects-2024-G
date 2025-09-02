import json
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.forms.classification_upload_form import ClassificationUploadForm
from app.forms.histogram_form import HistogramForm
from app.histogram.histogram_utils import histogram_hub
from app.ml.classification_utils import classify_image
from app.ml.classification_utils import fetch_image_bytes
from app.utils import list_images
from app.forms.transformation_form import TransformForm
from app.ml.transformation_utils import transform_image, cleanup_transforms

import io
import base64
import matplotlib.pyplot as plt

app = FastAPI()
config = Configuration()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/info")
def info() -> dict[str, list[str]]:
    """Returns a dictionary with the list of models and
    the list of available image files."""
    list_of_images = list_images()
    list_of_models = Configuration.models
    data = {"models": list_of_models, "images": list_of_images}
    return data


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """The home page of the service."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/classifications")
def create_classify(request: Request):
    return templates.TemplateResponse(
        "classification_select.html",
        {"request": request, "images": list_images(), "models": Configuration.models},
    )


@app.post("/classifications")
async def request_classification(request: Request):
    form = ClassificationForm(request)
    await form.load_data()
    image_id = form.image_id
    model_id = form.model_id
    classification_scores = classify_image(model_id=model_id, img_id=image_id)
    return templates.TemplateResponse(
        "classification_output.html",
        {
            "request": request,
            "image_id": image_id,
            "classification_scores": json.dumps(classification_scores),
        },
    )


@app.get("/upload-image", response_class=HTMLResponse)
def upload_image(request: Request):
    """
       Returns the image upload page along with the upload form.

       Parameters
       ----------
       request : Request
           The request sent by the user.

       Returns
       -------
       templates.TemplateResponse
           An HTML page containing the image upload form,
           the list of available models, and an empty error list.
       """
    return templates.TemplateResponse(
        "classification_upload_image.html",
        {"request": request, "models": Configuration.models, "errors": []},
    )


@app.post("/upload-and-classify")
async def request_classification_upload(request: Request):
    """
    This function processes the image classification request submitted via the upload form.

    Parameters
    ----------
    request : Request
        The request that the user sends to the server containing the image and selected model.

    Returns
    -------
    templates.TemplateResponse
        The page with the uploaded image and its classification scores,
        or the upload form page with error messages if the submitted data is invalid.
    """

    # Load the form data from the post request
    form = ClassificationUploadForm(request)
    await form.load_data()

    if form.is_valid():
        # Retrive image_bytes loaded and model id from the form
        bytes_img = form.image_bytes
        model_id = form.model_id

        # Classify the image using raw bytes instead of a file, utilizing fetch_image_bytes to process the input
        classification_scores = classify_image(model_id=model_id, img_id=bytes_img, fetch_image=fetch_image_bytes)

        # Encode the image in Base64 to embed it directly in the HTML template
        b64_img = base64.b64encode(bytes_img).decode('utf-8')


        # Render the classification results template
        return templates.TemplateResponse(
            "classification_upload_output.html",
            {
                "request": request,
                "image_base64": b64_img,
                "classification_scores": classification_scores,
            },
        )
    else:
        # if the form is not valid, then return the home page template
        return templates.TemplateResponse(
            "classification_upload_image.html",
            {
                "request": request,
                "models": Configuration.models,
                "errors": form.errors,
            }
        )



@app.get("/transform", response_class=HTMLResponse)
def transform_form(request: Request):
    """Renders a form to select an image and specify transformation parameters."""
    return templates.TemplateResponse(
        "image_transform_selection.html", {"request": request, "images": list_images()}
    )


@app.post("/transform")
async def transform_post(
        request: Request,
        background_tasks: BackgroundTasks,
):
    form = TransformForm(request)
    await form.load_data()

    if not form.is_valid():
        return templates.TemplateResponse(
            "image_transform_selection.html",
            {
                "request": request,
                "images": list_images(),
                "errors": form.errors
            },
            status_code=400
        )

    try:
        transformed_name = transform_image(
            image_id=form.image_id,
            brightness=form.brightness,
            contrast=form.contrast,
            color=form.color,
            sharpness=form.sharpness,
        )

        # Clean up old files first
        background_tasks.add_task(cleanup_transforms)

        return templates.TemplateResponse(
            "image_transform_output.html",
            {
                "request": request,
                "image_id": form.image_id,
                "transformed_name": transformed_name,
                "color": form.color,
                "brightness": form.brightness,
                "contrast": form.contrast,
                "sharpness": form.sharpness
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "image_transform_selection.html",
            {
                "request": request,
                "images": list_images(),
                "errors": [str(e)]
            },
            status_code=400
        )


@app.get("/histogram")
def create_histogram(request: Request):
    return templates.TemplateResponse(
        "histogram_select.html",
        {"request": request, "images": list_images()},
    )


@app.post("/histogram")
async def request_histogram(request: Request):
    """
    Shows both the selected image and the histogram of said image.
    """
    form = HistogramForm(request)
    await form.load_data()

    image_id = form.image_id
    histogram_type = form.type
    print(histogram_type)
    histogram_base64 = histogram_hub(image_id, histogram_type)
    return templates.TemplateResponse(
        "histogram_output.html",
        {
            "request": request,
            "image_id": image_id,
            "histogram": histogram_base64,
        }
    )

@app.get("/download/json")
async def download_json(scores: str):
    """
    Returns classification scores as a downloadable JSON file.
    """

    try:
        classification_scores = json.loads(scores)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    scores_data = json.dumps(classification_scores, indent=2).encode("utf-8")
    file_buffer = io.BytesIO(scores_data)

    return StreamingResponse(
        file_buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=classification_scores.json"
        },
    )


@app.get("/download/png")
async def download_png(scores: str):
    """
    Returns classification scores as a downloadable bar chart (PNG).
    """

    try:
        classification_scores = json.loads(scores)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    labels = [item[0] for item in classification_scores]
    data = [item[1] for item in classification_scores]

    plt.barh(
        labels,
        data,
        color=["#1a4a04", "#750014", "#795703", "#06216c", "#3f0355"],
    )
    plt.grid()
    plt.title("Classification Scores")
    plt.gca().invert_yaxis()

    img_buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    plt.close()

    return StreamingResponse(
        img_buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": "attachment; filename=top5_scores.png"
        },
    )