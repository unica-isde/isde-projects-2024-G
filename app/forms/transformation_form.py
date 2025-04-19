from fastapi import Request


class TransformForm:
    def __init__(self, request: Request) -> None:
        self.request: Request = request
        self.errors: list = []
        self.image_id: str = ""
        self.brightness: float = 1.0
        self.contrast: float = 1.0
        self.color: float = 1.0
        self.sharpness: float = 1.0

    async def load_data(self):
        form = await self.request.form()
        self.image_id = form.get("image_id")
        self.brightness = float(form.get("brightness", 1.0))
        self.contrast = float(form.get("contrast", 1.0))
        self.color = float(form.get("color", 1.0))
        self.sharpness = float(form.get("sharpness", 1.0))

    def is_valid(self):
        if not self.image_id or not isinstance(self.image_id, str):
            self.errors.append("A valid image id is required")

        for param, value in [('color', self.color), ('brightness', self.brightness),
                             ('contrast', self.contrast), ('sharpness', self.sharpness)]:
            if not 0.1 <= value <= 2.0:
                self.errors.append(f"{param} must be between 0.1 and 2.0")

        return not bool(self.errors)