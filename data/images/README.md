# Multi-Modal Evaluation Images

This folder contains test images for multi-modal (vision) model evaluation.

## Folder Structure

- **ocr/**: Images with text that models should read and extract (receipts, documents, signs)
- **charts/**: Graphs, bar charts, pie charts, line plots that models should interpret
- **visual_reasoning/**: Images requiring spatial or logical reasoning
- **diagrams/**: Technical diagrams, flowcharts, architecture diagrams
- **real_world/**: General photos requiring scene understanding

## Image Naming Convention

Use descriptive names that indicate the expected task:
- `receipt_coffee_shop.jpg` - Receipt from coffee shop for OCR
- `bar_chart_sales.png` - Bar chart showing sales data
- `traffic_light_red.jpg` - Traffic light image for color/state recognition
- `flowchart_login.png` - Login flow diagram

## Adding Images

1. Place images in the appropriate category folder
2. Use common formats: JPG, PNG, WEBP
3. Keep file sizes reasonable (<2MB per image)
4. Update `golden_dataset.csv` with the relative path (e.g., `images/ocr/receipt_coffee_shop.jpg`)

## Image Sources

For testing, you can use:
- Public domain images (Unsplash, Pexels)
- Self-created screenshots/diagrams
- Synthetic test images

Ensure you have the right to use any images you add.
