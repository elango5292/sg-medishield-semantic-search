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
    """Build text nodes from raw text extraction data.
    
    Only creates image nodes for images that have existing files.
    Includes section title in all nodes for semantic matching.
    """

    def __init__(
        self,
        sections_output_dir: Path = None,
        paragraphs_output_dir: Path = None,
        sentences_output_dir: Path = None,
        images_output_dir: Path = None,
    ):
        sections_output_dir = sections_output_dir or config.NODES_TEXT_SECTIONS_DIR
        super().__init__(sections_output_dir)
        self.sections_output_dir = sections_output_dir
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
        """Build all text nodes. Only creates image nodes for existing images."""
        source = data.get("source", "unknown")
        elements = data.get("elements", [])

        section_nodes = []
        paragraph_nodes = []
        sentence_nodes = []
        image_nodes = []

        current_section_title = ""
        current_section_elements = []
        current_section_page = 0

        for element in elements:
            elem_type = element.get("type", "")

            if elem_type == "Title":
                # Save previous section
                if current_section_title:
                    section_node = self._build_section_node(
                        current_section_title, current_section_elements, current_section_page, source
                    )
                    if section_node:
                        section_nodes.append(section_node)

                current_section_title = element.get("text", "").strip()
                current_section_page = element.get("metadata", {}).get("page_number", 0)
                current_section_elements = []

            elif elem_type == "NarrativeText":
                current_section_elements.append(element)

                para_node = self._build_paragraph_node(element, current_section_title, source, len(paragraph_nodes))
                if para_node:
                    paragraph_nodes.append(para_node)
                    sent_nodes = self._build_sentence_nodes(element, current_section_title, source, para_node["id"])
                    sentence_nodes.extend(sent_nodes)

            elif elem_type == "Image":
                img_node = self._build_image_node(element, current_section_title, source, len(image_nodes))
                if img_node:
                    image_nodes.append(img_node)

        # Save last section
        if current_section_title:
            section_node = self._build_section_node(
                current_section_title, current_section_elements, current_section_page, source
            )
            if section_node:
                section_nodes.append(section_node)

        print(f"  Created {len(section_nodes)} sections, {len(paragraph_nodes)} paragraphs, {len(sentence_nodes)} sentences, {len(image_nodes)} images")

        self._save_nodes(paragraph_nodes, self.paragraphs_output_dir, Path(source).stem)
        self._save_nodes(sentence_nodes, self.sentences_output_dir, Path(source).stem)
        self._save_nodes(image_nodes, self.images_output_dir, Path(source).stem)

        return section_nodes

    def _build_section_node(self, title: str, elements: list, page: int, source: str) -> dict[str, Any] | None:
        if not title:
            return None

        content_texts = [title]
        for elem in elements:
            text = elem.get("text", "").strip()
            if text:
                content_texts.append(text)

        return {
            "id": f"section_p{page}_{hash(title) % 10000}",
            "text": "\n\n".join(content_texts),
            "metadata": {"source": source, "page": page, "section_title": title, "node_type": "section"},
        }

    def _build_paragraph_node(self, element: dict, section_title: str, source: str, idx: int) -> dict[str, Any] | None:
        text = element.get("text", "").strip()
        if not text:
            return None

        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)

        # Include section title in text for semantic matching
        full_text = f"{section_title}: {text}" if section_title else text

        return {
            "id": f"para_p{page}_{idx}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "paragraph",
            },
        }

    def _build_sentence_nodes(self, element: dict, section_title: str, source: str, para_id: str) -> list[dict[str, Any]]:
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

            # Include section title in text for semantic matching
            full_text = f"{section_title}: {sentence}" if section_title else sentence

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
                },
            })

        return nodes

    def _build_image_node(self, element: dict, section_title: str, source: str, idx: int) -> dict[str, Any] | None:
        """Build image node only if image file exists."""
        element_id = element.get("element_id", "")
        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)

        # Check if image file exists
        image_path = metadata.get("image_path")
        if not image_path or not Path(image_path).exists():
            return None

        # Get enriched data if available
        enriched = self.enriched_images.get(element_id, {}).get("enriched", {})
        title = enriched.get("title", f"Figure on page {page}")
        description = enriched.get("description", "")

        # Build text with section title for semantic matching
        img_text = f"{title}: {description}" if description else title
        full_text = f"{section_title} - {img_text}" if section_title else img_text

        return {
            "id": f"image_p{page}_{idx}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "image",
                "image_path": image_path,
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
