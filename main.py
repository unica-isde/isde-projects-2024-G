import io
import json
import zipfile
import matplotlib.pyplot as plt
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.ml.classification_utils import classify_image
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


@app.get("/download")
async def download(scores: str):
    """
    Processes classification scores, generates a bar chart, 
    and packages the chart and scores into a downloadable ZIP file.
    Args:
        scores (str): A JSON-formatted string containing classification scores. 
                      Each item in the JSON should be a list where the first 
                      element is the label (str) and the second element is the 
                      score (float).
    Returns:
        StreamingResponse: A response containing a ZIP file with:
            - "classification_scores.json": The original classification scores in JSON format.
            - "top5_scores.png": A horizontal bar chart visualizing the scores.
    Raises:
        HTTPException: If the input `scores` is not valid JSON data.
    """
    
    try:
        classification_scores = json.loads(scores)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    labels = [item[0] for item in classification_scores]
    data = [item[1] for item in classification_scores]

    plt.barh(
        labels, data,
        color=["#1a4a04", "#750014", "#795703", "#06216c", "#3f0355"]
    )
    plt.grid()
    plt.title("Classification Scores")
    plt.gca().invert_yaxis()
    img_buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    plt.close()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        scores_data = json.dumps(classification_scores, indent=2).encode("utf-8")
        zip_file.writestr("classification_scores.json", scores_data)
        zip_file.writestr("top5_scores.png", img_buffer.getvalue())

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=results.zip",
            "Content-Type": "application/zip",
        }
    )
