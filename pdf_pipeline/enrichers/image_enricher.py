"""Image enricher - adds title and description to images."""
import base64
import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from pdf_pipeline.base import BaseEnricher
from pdf_pipeline import config
from pdf_pipeline.models import ModelProvider, get_default_provider, ModelConfig


class ImageEnricher(BaseEnricher):
    """Enrich images with title and description using LLM."""

    def __init__(self, output_dir: Path = None, model_provider: ModelProvider = None):
        output_dir = output_dir or config.ENRICHED_IMAGES_DIR
        super().__init__(output_dir)
        self.provider = model_provider or get_default_provider()

    def enrich(self, data: dict[str, Any]) -> dict[str, Any]:
        """Enrich only images that have existing image files."""
        enriched_images = []
        skipped = 0

        for element in data.get("elements", []):
            if element.get("type") != "Image":
                continue

            # Get filename from metadata and look in local figures dir
            metadata = element.get("metadata", {})
            original_path = metadata.get("image_path", "")
            if original_path:
                filename = Path(original_path).name
                local_path = config.IMAGES_FIGURES_DIR / filename

                if local_path.exists():
                    enriched_images.append(self._enrich_image(element, local_path))
                    continue

            skipped += 1

        if skipped > 0:
            print(f"  Skipped {skipped} images (no image file)")
        print(f"  Processing {len(enriched_images)} images with files")

        return {"source": data.get("source"), "images": enriched_images}

    def _enrich_image(self, element: dict[str, Any], image_path: Path) -> dict[str, Any]:
        """Enrich a single image with metadata."""
        metadata = element.get("metadata", {})

        return {
            "element_id": element.get("element_id"),
            "page": metadata.get("page_number"),
            "image_path": str(image_path),
            "enriched": self._enrich_with_llm(image_path),
        }

    def _enrich_with_llm(self, image_path: Path) -> dict[str, Any]:
        """Use multimodal LLM to describe the image."""
        try:
            llm = self.provider.get_llm()

            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            message = HumanMessage(content=[
                {"type": "text", "text": """Analyze this image and provide:
1. A short descriptive title
2. A description of what the image shows

Respond in JSON format only:
{"title": "...", "description": "..."}"""},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ])

            response = llm.invoke([message])
            content = response.content

            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

        except Exception as e:
            print(f"LLM failed for {image_path.name}: {e}")

        return {"title": f"Figure", "description": ""}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.enrichers.image_enricher <input_json>")
        sys.exit(1)
    config.create_output_dirs()
    enricher = ImageEnricher()
    output_path = enricher.run(Path(sys.argv[1]))
    print(f"Images enriched to: {output_path}")
