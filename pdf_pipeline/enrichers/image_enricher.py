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
    """Enrich images with title and description using LLM.
    
    Only processes images that have a valid image file (allows manual curation).
    """

    def __init__(
        self,
        output_dir: Path = None,
        images_dir: Path = None,
        model_provider: ModelProvider = None,
        llm_config: ModelConfig = None,
        use_llm: bool = True,
    ):
        output_dir = output_dir or config.ENRICHED_IMAGES_DIR
        super().__init__(output_dir)
        self.images_dir = images_dir or config.IMAGES_FIGURES_DIR
        self.use_llm = use_llm

        if model_provider:
            self.provider = model_provider
        elif llm_config:
            self.provider = ModelProvider(llm_config=llm_config)
        else:
            self.provider = get_default_provider()

    def enrich(self, data: dict[str, Any]) -> dict[str, Any]:
        """Enrich only images that have existing image files."""
        enriched_images = []
        skipped = 0

        for element in data.get("elements", []):
            if element.get("type") != "Image":
                continue
            
            # Check if image file exists
            image_path = self._get_image_path(element)
            if not image_path or not image_path.exists():
                skipped += 1
                continue

            enriched_images.append(self._enrich_image(element, image_path))

        if skipped > 0:
            print(f"  Skipped {skipped} images (no image file)")
        print(f"  Processing {len(enriched_images)} images with files")

        return {"source": data.get("source"), "images": enriched_images}

    def _get_image_path(self, element: dict[str, Any]) -> Path | None:
        """Get image path from element metadata."""
        metadata = element.get("metadata", {})
        image_path = metadata.get("image_path")
        
        if image_path:
            return Path(image_path)
        return None

    def _enrich_image(self, element: dict[str, Any], image_path: Path) -> dict[str, Any]:
        """Enrich a single image with metadata."""
        metadata = element.get("metadata", {})

        enriched = {
            "element_id": element.get("element_id"),
            "page": metadata.get("page_number"),
            "coordinates": metadata.get("coordinates"),
            "image_path": str(image_path),
        }

        if self.use_llm:
            enriched["enriched"] = self._enrich_with_llm(image_path)
        else:
            enriched["enriched"] = self._enrich_with_heuristics(element)

        return enriched

    def _enrich_with_llm(self, image_path: Path) -> dict[str, Any]:
        """Use multimodal LLM to describe the image."""
        try:
            llm = self.provider.get_llm()
            if not llm:
                return {"title": "Image", "description": "", "enrichment_method": "none"}

            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            message = HumanMessage(content=[
                {"type": "text", "text": """Analyze this image and provide:
1. A short descriptive title
2. A detailed description of what the image shows

Respond in JSON format only:
{"title": "...", "description": "..."}"""},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ])

            response = llm.invoke([message])
            content = response.content

            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
                result["enrichment_method"] = "llm"
                return result

        except Exception as e:
            print(f"LLM enrichment failed for {image_path.name}: {e}")

        return self._enrich_with_heuristics({})

    def _enrich_with_heuristics(self, element: dict[str, Any]) -> dict[str, Any]:
        """Use heuristics to describe the image."""
        page = element.get("metadata", {}).get("page_number", "?")
        return {
            "title": f"Figure on page {page}",
            "description": "Image extracted from document",
            "enrichment_method": "heuristics",
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.enrichers.image_enricher <input_json>")
        sys.exit(1)

    config.create_output_dirs()
    enricher = ImageEnricher()
    output_path = enricher.run(Path(sys.argv[1]))
    print(f"Images enriched to: {output_path}")
