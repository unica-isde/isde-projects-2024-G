import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.forms.classification_upload_form import ClassificationUploadForm
from app.ml.classification_utils import classify_image
from app.ml.classification_utils import fetch_image_bytes
from app.utils import list_images


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
    return templates.TemplateResponse(
        "classification_upload_image.html",
        {"request": request, "models": Configuration.models, "errors": []},
    )


@app.post("/upload-and-classify")
async def request_classification_upload(request: Request):

    # Load the form data from the post request
    form = ClassificationUploadForm(request)
    await form.load_data()

    if form.is_valid():
        # Retrive image_bytes loaded and model id from the form
        bytes_img = form.image_bytes
        model_id = form.model_id

        # Classify the image using raw bytes instead of a file, utilizing fetch_image_bytes to process the input
        classification_scores = classify_image(model_id=model_id, img_id=bytes_img, fetch_image=fetch_image_bytes)

        # Render the classification results template
        return templates.TemplateResponse(
            "classification_output.html",
            {
                "request": request,
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