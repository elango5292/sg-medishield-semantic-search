"""
Text node builder - creates nodes from text extraction data.
"""
from pathlib import Path
from typing import Any

import nltk

from pdf_pipeline.base import BaseNodeBuilder
from pdf_pipeline import config


# Download punkt tokenizer if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class TextNodeBuilder(BaseNodeBuilder):
    """
    Build text nodes from raw text extraction data.
    
    Creates section, paragraph, sentence, and image nodes.
    """
    
    def __init__(
        self,
        sections_output_dir: Path = None,
        paragraphs_output_dir: Path = None,
        sentences_output_dir: Path = None,
        images_output_dir: Path = None,
    ):
        # Use sections dir as default output
        sections_output_dir = sections_output_dir or config.NODES_TEXT_SECTIONS_DIR
        super().__init__(sections_output_dir)
        
        self.sections_output_dir = sections_output_dir
        self.paragraphs_output_dir = paragraphs_output_dir or config.NODES_TEXT_PARAGRAPHS_DIR
        self.sentences_output_dir = sentences_output_dir or config.NODES_TEXT_SENTENCES_DIR
        self.images_output_dir = images_output_dir or config.NODES_TEXT_IMAGES_DIR
        
        # Create all output directories
        for d in [self.paragraphs_output_dir, self.sentences_output_dir, self.images_output_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.enriched_images = {}
    
    def load_enriched_images(self, enriched_images_path: Path):
        """
        Load enriched image data for image nodes.
        """
        import json
        if enriched_images_path.exists():
            with open(enriched_images_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for img in data.get("images", []):
                    self.enriched_images[img.get("element_id")] = img
    
    def build_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Build all text nodes.
        
        Args:
            data: Raw text extraction data
            
        Returns:
            List of section node dictionaries (others saved separately)
        """
        source = data.get("source", "unknown")
        elements = data.get("elements", [])
        
        section_nodes = []
        paragraph_nodes = []
        sentence_nodes = []
        image_nodes = []
        
        current_section = None
        current_section_elements = []
        
        for element in elements:
            elem_type = element.get("type", "")
            
            # Handle section titles
            if elem_type == "Title":
                # Save previous section
                if current_section:
                    section_node = self._build_section_node(
                        current_section, current_section_elements, source
                    )
                    if section_node:
                        section_nodes.append(section_node)
                
                # Start new section
                current_section = element
                current_section_elements = []
            
            # Handle paragraphs
            elif elem_type == "NarrativeText":
                current_section_elements.append(element)
                
                # Build paragraph node
                para_node = self._build_paragraph_node(
                    element, current_section, source, len(paragraph_nodes)
                )
                if para_node:
                    paragraph_nodes.append(para_node)
                    
                    # Build sentence nodes
                    sent_nodes = self._build_sentence_nodes(
                        element, current_section, source, para_node["id"]
                    )
                    sentence_nodes.extend(sent_nodes)
            
            # Handle images
            elif elem_type == "Image":
                img_node = self._build_image_node(
                    element, current_section, source, len(image_nodes)
                )
                if img_node:
                    image_nodes.append(img_node)
        
        # Save last section
        if current_section:
            section_node = self._build_section_node(
                current_section, current_section_elements, source
            )
            if section_node:
                section_nodes.append(section_node)
        
        # Save other node types
        self._save_nodes(paragraph_nodes, self.paragraphs_output_dir, Path(source).stem)
        self._save_nodes(sentence_nodes, self.sentences_output_dir, Path(source).stem)
        self._save_nodes(image_nodes, self.images_output_dir, Path(source).stem)
        
        return section_nodes
    
    def _build_section_node(
        self,
        title_element: dict[str, Any],
        content_elements: list[dict[str, Any]],
        source: str,
    ) -> dict[str, Any] | None:
        """
        Build a section node from title and content elements.
        """
        title = title_element.get("text", "").strip()
        if not title:
            return None
        
        page = title_element.get("metadata", {}).get("page_number", 0)
        
        # Combine title and content
        content_texts = [title]
        for elem in content_elements:
            text = elem.get("text", "").strip()
            if text:
                content_texts.append(text)
        
        full_text = "\n\n".join(content_texts)
        
        return {
            "id": f"section_p{page}_{hash(title) % 10000}",
            "text": full_text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": title,
                "node_type": "section",
            },
        }
    
    def _build_paragraph_node(
        self,
        element: dict[str, Any],
        section_element: dict[str, Any] | None,
        source: str,
        para_idx: int,
    ) -> dict[str, Any] | None:
        """
        Build a paragraph node.
        """
        text = element.get("text", "").strip()
        if not text:
            return None
        
        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        section_title = section_element.get("text", "") if section_element else ""
        
        return {
            "id": f"para_p{page}_{para_idx}",
            "text": text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "paragraph",
                "coordinates": metadata.get("coordinates"),
            },
        }
    
    def _build_sentence_nodes(
        self,
        element: dict[str, Any],
        section_element: dict[str, Any] | None,
        source: str,
        paragraph_id: str,
    ) -> list[dict[str, Any]]:
        """
        Build sentence nodes from a paragraph.
        """
        text = element.get("text", "").strip()
        if not text:
            return []
        
        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        section_title = section_element.get("text", "") if section_element else ""
        
        # Split into sentences
        sentences = nltk.sent_tokenize(text)
        
        nodes = []
        for sent_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            node = {
                "id": f"{paragraph_id}_s{sent_idx}",
                "text": sentence,
                "metadata": {
                    "source": source,
                    "page": page,
                    "section_title": section_title,
                    "paragraph_id": paragraph_id,
                    "sentence_index": sent_idx,
                    "node_type": "sentence",
                },
            }
            nodes.append(node)
        
        return nodes
    
    def _build_image_node(
        self,
        element: dict[str, Any],
        section_element: dict[str, Any] | None,
        source: str,
        img_idx: int,
    ) -> dict[str, Any] | None:
        """
        Build an image node.
        """
        element_id = element.get("element_id", "")
        metadata = element.get("metadata", {})
        page = metadata.get("page_number", 0)
        section_title = section_element.get("text", "") if section_element else ""
        
        # Get enriched data if available
        enriched = self.enriched_images.get(element_id, {}).get("enriched", {})
        title = enriched.get("title", f"Image on page {page}")
        description = enriched.get("description", "")
        image_path = self.enriched_images.get(element_id, {}).get("image_path")
        
        # Build text: "Title: Description"
        text = f"{title}: {description}" if description else title
        
        return {
            "id": f"image_p{page}_{img_idx}",
            "text": text,
            "metadata": {
                "source": source,
                "page": page,
                "section_title": section_title,
                "node_type": "image",
                "coordinates": metadata.get("coordinates"),
                "image_path": image_path,
            },
        }
    
    def _save_nodes(self, nodes: list[dict[str, Any]], output_dir: Path, filename: str):
        """
        Save nodes to JSON file.
        """
        import json
        output_path = output_dir / f"{filename}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pdf_pipeline.node_builders.text_node_builder <input_json> [enriched_images_json]")
        sys.exit(1)
    
    config.create_output_dirs()
    
    input_path = Path(sys.argv[1])
    builder = TextNodeBuilder()
    
    # Load enriched images if provided
    if len(sys.argv) > 2:
        enriched_images_path = Path(sys.argv[2])
        builder.load_enriched_images(enriched_images_path)
    
    output_path = builder.run(input_path)
    print(f"Text nodes saved to: {output_path}")
