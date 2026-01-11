"""Text node builder - creates nodes from text extraction data."""
from pathlib import Path
from typing import Any
import json

import nltk

from pdf_pipeline.base import BaseNodeBuilder
from pdf_pipeline import config

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class TextNodeBuilder(BaseNodeBuilder):
    """Build text nodes with coordinates for highlighting."""

    def __init__(
        self,
        sections_output_dir: Path = None,
        paragraphs_output_dir: Path = None,
        sentences_output_dir: Path = None,
        images_output_dir: Path = None,
    ):
        sections_output_dir = sections_output_dir or config.NODES_TEXT_SECTIONS_DIR
        super().__init__(sections_output_dir)
        self.paragraphs_output_dir = paragraphs_output_dir or config.NODES_TEXT_PARAGRAPHS_DIR
        self.sentences_output_dir = sentences_output_dir or config.NODES_TEXT_SENTENCES_DIR
        self.images_output_dir = images_output_dir or config.NODES_TEXT_IMAGES_DIR

        for d in [self.paragraphs_output_dir, self.sentences_output_dir, self.images_output_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.enriched_images = {}

    def load_enriched_images(self, enriched_images_path: Path):
        """Load enriched image data."""
        if enriched_images_path.exists():
            with open(enriched_images_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for img in data.get("images", []):
                    self.enriched_images[img.get("element_id")] = img

    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build all text nodes with coordinates."""
        source = data.get("source", "unknown")
        elements = data.get("elements", [])

        section_nodes = []
        paragraph_nodes = []
        sentence_nodes = []
        image_nodes = []

        current_section_title = ""
        current_section_elements = []
        current_section_page = 0
        current_section_coords = None

        for element in elements:
            elem_type = element.get("type", "")
            metadata = element.get("metadata", {})
            coords = metadata.get("coordinates", {})

            if elem_type == "Title":
                if current_section_title:
                    section_node = self._build_section_node(
                        current_section_title, current_section_elements, 
                        current_section_page, current_section_coords, source
                    )
                    if section_node:
                        section_nodes.append(section_node)

                current_section_title = element.get("text", "").strip()
                current_section_page = metadata.get("page_number", 0)
                current_section_coords = coords
                current_section_elements = []

            elif elem_type == "NarrativeText":
                current_section_elements.append(element)

                para_node = self._build_paragraph_node(element, current_section_title, source, len(paragraph_nodes))
                if para_node:
                    paragraph_nodes.append(para_node)
                    sent_nodes = self._build_sentence_nodes(element, current_section_title, source, para_node["id"], coords)
                    sentence_nodes.extend(sent_nodes)

            elif elem_type == "Image":
                img_node = self._build_image_node(element, current_section_title, source, len(image_nodes))
                if img_node:
                    image_nodes.append(img_node)

        if current_section_title:
            section_node = self._build_section_node(
                current_section_title, current_section_elements,
                current_section_page, current_section_coords, source
            )
            if section_node:
                section_nodes.append(section_node)

        print(f"  Created {len(section_nodes)} sections, {len(paragraph_nodes)} paragraphs, {len(sentence_nodes)} sentences, {len(image_nodes)} images")

        self._save_nodes(paragraph_nodes, self.paragraphs_output_dir, Path(source).stem)
        self._save_nodes(sentence_nodes, self.sentences_output_dir, Path(source).stem)
        self._save_nodes(image_nodes, self.images_output_dir, Path(source).stem)

        return section_nodes

    def _build_section_node(self, title: str, elements: list, page: int, title_coords: dict, source: str) -> dict[str, Any] | None:
        if not title:
            return None

        content_texts = []
        # Group coordinates by page
        coords_by_page = {}
        
        # Add title coordinates
        if title_coords and title_coords.get("points"):
            coords_by_page[page] = [title_coords]
        
        for elem in elements:
            text = elem.get("text", "").strip()
            if text:
                content_texts.append(text)
            
            metadata = elem.get("metadata", {})
            elem_page = metadata.get("page_number", page)
            elem_coords = metadata.get("coordinates", {})
            if elem_coords and elem_coords.get("points"):
                if elem_page not in coords_by_page:
                    coords_by_page[elem_page] = []
                coords_by_page[elem_page].append(elem_coords)

        full_text = f"# {title}\n{chr(10).join(content_texts)}" if content_texts else f"# {title}"
        
        # Merge regions per page into single bounding box
        coordinates = []
        for p, regions in sorted(coords_by_page.items()):
            all_points = []
            for r in regions:
                all_points.extend(r.get("points", []))
            if all_points:
                xs = [pt[0] for pt in all_points]
                ys = [pt[1] for pt in all_points]
                coordinates.append({
                    "page": p,
                    "bbox": [min(xs), min(ys), max(xs), max(ys)]
                })

        return {
            "id": f"section_p{page}_{hash(title) % 10000}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": title,
                "node_type": "section",
                "coordinates": coordinates,
            },
        }

    def _build_paragraph_node(self, element: dict, section_title: str, source: str, idx: int) -> dict[str, Any] | None:
        text = element.get("text", "").strip()
        if not text:
            return None

        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        coords = metadata.get("coordinates", {})

        full_text = f"# {section_title}\n{text}" if section_title else text

        return {
            "id": f"para_p{page}_{idx}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "paragraph",
                "coordinates": coords,
            },
        }

    def _build_sentence_nodes(self, element: dict, section_title: str, source: str, para_id: str, coords: dict) -> list[dict[str, Any]]:
        text = element.get("text", "").strip()
        if not text:
            return []

        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        sentences = nltk.sent_tokenize(text)

        nodes = []
        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            full_text = f"# {section_title}\n{sentence}" if section_title else sentence

            nodes.append({
                "id": f"{para_id}_s{idx}",
                "text": full_text,
                "metadata": {
                    "source": source,
                    "page": page,
                    "section_title": section_title,
                    "paragraph_id": para_id,
                    "sentence_index": idx,
                    "node_type": "sentence",
                    "coordinates": coords,  # Use paragraph coordinates for sentences
                },
            })

        return nodes

    def _build_image_node(self, element: dict, section_title: str, source: str, idx: int) -> dict[str, Any] | None:
        """Build image node using enriched data."""
        element_id = element.get("element_id", "")
        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        coords = metadata.get("coordinates", {})

        # Get enriched data by element_id
        enriched_img = self.enriched_images.get(element_id)
        if not enriched_img:
            return None

        enriched = enriched_img.get("enriched", {})
        title = enriched.get("title", f"Figure on page {page}")
        description = enriched.get("description", "")
        image_path = enriched_img.get("image_path")

        img_text = f"{title}\n{description}" if description else title
        full_text = f"# {section_title}\n{img_text}" if section_title else img_text

        return {
            "id": f"image_p{page}_{idx}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "image",
                "image_path": image_path,
                "coordinates": coords,
            },
        }

    def _save_nodes(self, nodes: list[dict[str, Any]], output_dir: Path, filename: str):
        output_path = output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.node_builders.text_node_builder <input_json> [enriched_images_json]")
        sys.exit(1)

    config.create_output_dirs()
    builder = TextNodeBuilder()

    if len(sys.argv) > 2:
        builder.load_enriched_images(Path(sys.argv[2]))

    output_path = builder.run(Path(sys.argv[1]))
    print(f"Text nodes saved to: {output_path}")
