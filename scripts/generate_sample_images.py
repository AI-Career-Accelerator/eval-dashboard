"""
Generate sample test images for multi-modal evaluation.
This script creates simple test images for OCR, charts, visual reasoning, and diagrams.
"""
import os
from PIL import Image, ImageDraw, ImageFont
import random

# Create output directories
BASE_DIR = os.path.join("data", "images")
categories = ["ocr", "charts", "visual_reasoning", "diagrams"]

def create_text_image(text, filename, size=(800, 200), font_size=48):
    """Create a simple image with text for OCR testing."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    try:
        # Try to use a better font if available
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    draw.text((x, y), text, fill='black', font=font)
    img.save(filename)
    print(f"[CREATED] {filename}")
    return filename

def create_bar_chart(filename, data=None, size=(600, 400)):
    """Create a simple bar chart image."""
    if data is None:
        data = {"A": 45, "B": 30, "C": 65, "D": 20}

    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    # Draw bars
    bar_width = 80
    max_value = max(data.values())
    x_start = 50
    y_bottom = size[1] - 50

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

    for i, (label, value) in enumerate(data.items()):
        x = x_start + i * (bar_width + 30)
        bar_height = (value / max_value) * (size[1] - 100)
        y = y_bottom - bar_height

        # Draw bar
        draw.rectangle([x, y, x + bar_width, y_bottom], fill=colors[i % len(colors)])

        # Draw value on top
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((x + 10, y - 25), str(value), fill='black', font=font)

        # Draw label
        draw.text((x + 10, y_bottom + 10), label, fill='black', font=font)

    # Draw title
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
    draw.text((size[0]//2 - 80, 20), "Sales Data", fill='black', font=title_font)

    img.save(filename)
    print(f"[CREATED] {filename}")
    return filename

def create_traffic_light(filename, state="red", size=(200, 400)):
    """Create a traffic light image."""
    img = Image.new('RGB', size, color='#333333')
    draw = ImageDraw.Draw(img)

    # Draw background rectangle
    draw.rectangle([40, 40, 160, 360], fill='black', outline='white', width=3)

    # Light positions
    lights = {
        'red': (100, 90, 50),
        'yellow': (100, 200, 50),
        'green': (100, 310, 50)
    }

    # Draw all lights (dark when off)
    for light_name, (x, y, radius) in lights.items():
        if light_name == state:
            colors = {'red': '#FF0000', 'yellow': '#FFFF00', 'green': '#00FF00'}
            color = colors[light_name]
        else:
            color = '#222222'  # Dark when off

        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline='white', width=2)

    img.save(filename)
    print(f"[CREATED] {filename}")
    return filename

def create_counting_image(filename, num_objects=5, size=(600, 400)):
    """Create an image with colored circles for counting."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#95E1D3']

    for i in range(num_objects):
        x = random.randint(60, size[0] - 60)
        y = random.randint(60, size[1] - 60)
        radius = random.randint(30, 50)
        color = colors[i % len(colors)]

        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline='black', width=2)

    img.save(filename)
    print(f"[CREATED] {filename}")
    return filename

def create_flowchart(filename, size=(700, 500)):
    """Create a simple flowchart diagram."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    # Start box
    draw.rectangle([250, 30, 450, 80], fill='#4ECDC4', outline='black', width=2)
    draw.text((300, 50), "Start", fill='black', font=font)

    # Arrow down
    draw.line([350, 80, 350, 120], fill='black', width=2)
    draw.polygon([(350, 120), (345, 110), (355, 110)], fill='black')

    # Decision diamond
    draw.polygon([(350, 120), (250, 200), (350, 280), (450, 200)], fill='#FFE66D', outline='black')
    draw.text((290, 190), "Condition?", fill='black', font=font)

    # Yes arrow
    draw.line([450, 200, 550, 200], fill='black', width=2)
    draw.polygon([(550, 200), (540, 195), (540, 205)], fill='black')
    draw.text((480, 180), "Yes", fill='black', font=font)

    # Yes action box
    draw.rectangle([550, 170, 670, 230], fill='#95E1D3', outline='black', width=2)
    draw.text((570, 195), "Action 1", fill='black', font=font)

    # No arrow
    draw.line([350, 280, 350, 320], fill='black', width=2)
    draw.polygon([(350, 320), (345, 310), (355, 310)], fill='black')
    draw.text((360, 290), "No", fill='black', font=font)

    # End box
    draw.rectangle([250, 320, 450, 370], fill='#FF6B6B', outline='black', width=2)
    draw.text((310, 340), "End", fill='black', font=font)

    img.save(filename)
    print(f"[CREATED] {filename}")
    return filename

def main():
    """Generate all sample images."""
    print("[START] Generating sample test images...")

    # Ensure directories exist
    for cat in categories:
        os.makedirs(os.path.join(BASE_DIR, cat), exist_ok=True)

    # OCR samples
    create_text_image("Main Street", os.path.join(BASE_DIR, "ocr", "sample_text.jpg"))
    create_text_image("Total: $45.99", os.path.join(BASE_DIR, "ocr", "receipt.jpg"))
    create_text_image("Oak Avenue", os.path.join(BASE_DIR, "ocr", "street_sign.jpg"))
    create_text_image("contact@example.com", os.path.join(BASE_DIR, "ocr", "business_card.jpg"))
    create_text_image("Premium Coffee Beans", os.path.join(BASE_DIR, "ocr", "product_label.jpg"))

    # Chart samples
    create_bar_chart(os.path.join(BASE_DIR, "charts", "bar_chart.png"))
    create_bar_chart(os.path.join(BASE_DIR, "charts", "line_graph.png"), {"Q1": 40, "Q2": 55, "Q3": 70, "Q4": 60})
    create_bar_chart(os.path.join(BASE_DIR, "charts", "pie_chart.png"), {"A": 45, "B": 30, "C": 25})
    create_bar_chart(os.path.join(BASE_DIR, "charts", "sales_chart.png"), {"Product A": 65, "Product B": 30, "Product C": 85, "Product D": 40})

    # Add y-axis label chart
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    draw.text((10, 200), "Revenue ($)", fill='black', font=font, anchor="lm")
    create_bar_chart(os.path.join(BASE_DIR, "charts", "axis_label.png"))

    # Visual reasoning samples
    create_counting_image(os.path.join(BASE_DIR, "visual_reasoning", "count_objects.jpg"), 7)
    create_traffic_light(os.path.join(BASE_DIR, "visual_reasoning", "traffic_light.jpg"), "red")

    # Create colored car
    img = Image.new('RGB', (400, 300), color='#87CEEB')  # Sky blue background
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 120, 300, 200], fill='#FF0000', outline='black', width=2)  # Red car body
    draw.ellipse([120, 180, 160, 220], fill='#333333', outline='black', width=2)  # Wheel
    draw.ellipse([240, 180, 280, 220], fill='#333333', outline='black', width=2)  # Wheel
    img.save(os.path.join(BASE_DIR, "visual_reasoning", "car_color.jpg"))
    print(f"[CREATED] {os.path.join(BASE_DIR, 'visual_reasoning', 'car_color.jpg')}")

    # Size comparison
    img = Image.new('RGB', (500, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 100, 150, 200], fill='#4ECDC4', outline='black', width=2)  # Small circle
    draw.ellipse([250, 50, 450, 250], fill='#FF6B6B', outline='black', width=2)  # Large circle
    img.save(os.path.join(BASE_DIR, "visual_reasoning", "size_comparison.jpg"))
    print(f"[CREATED] {os.path.join(BASE_DIR, 'visual_reasoning', 'size_comparison.jpg')}")

    # Person action (stick figure waving)
    img = Image.new('RGB', (400, 500), color='white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([170, 50, 230, 110], outline='black', width=3)  # Head
    draw.line([200, 110, 200, 250], fill='black', width=3)  # Body
    draw.line([200, 150, 280, 120], fill='black', width=3)  # Right arm (waving)
    draw.line([200, 150, 120, 180], fill='black', width=3)  # Left arm
    draw.line([200, 250, 150, 350], fill='black', width=3)  # Left leg
    draw.line([200, 250, 250, 350], fill='black', width=3)  # Right leg
    img.save(os.path.join(BASE_DIR, "visual_reasoning", "person_action.jpg"))
    print(f"[CREATED] {os.path.join(BASE_DIR, 'visual_reasoning', 'person_action.jpg')}")

    # Diagram samples
    create_flowchart(os.path.join(BASE_DIR, "diagrams", "flowchart.png"))
    create_flowchart(os.path.join(BASE_DIR, "diagrams", "process_flow.png"))
    create_flowchart(os.path.join(BASE_DIR, "diagrams", "flowchart_start.png"))

    # System architecture
    img = Image.new('RGB', (700, 400), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    # Frontend
    draw.rectangle([50, 150, 150, 250], fill='#4ECDC4', outline='black', width=2)
    draw.text((70, 195), "Frontend", fill='black', font=font)

    # Backend
    draw.rectangle([300, 150, 400, 250], fill='#FFE66D', outline='black', width=2)
    draw.text((315, 195), "Backend", fill='black', font=font)

    # Database
    draw.ellipse([550, 150, 650, 250], fill='#95E1D3', outline='black', width=2)
    draw.text((570, 195), "Database", fill='black', font=font)

    # Connections
    draw.line([150, 200, 300, 200], fill='black', width=2)
    draw.polygon([(300, 200), (290, 195), (290, 205)], fill='black')
    draw.line([400, 200, 550, 200], fill='black', width=2)
    draw.polygon([(550, 200), (540, 195), (540, 205)], fill='black')

    img.save(os.path.join(BASE_DIR, "diagrams", "system_architecture.png"))
    print(f"[CREATED] {os.path.join(BASE_DIR, 'diagrams', 'system_architecture.png')}")

    # Database connection diagram
    img.save(os.path.join(BASE_DIR, "diagrams", "database_connection.png"))
    print(f"[CREATED] {os.path.join(BASE_DIR, 'diagrams', 'database_connection.png')}")

    print("\n[DONE] All sample images generated successfully!")
    print(f"[INFO] Images saved to: {BASE_DIR}")
    print("\n[NEXT] Update the expected_output values in golden_dataset.csv for questions 51-70")
    print("       based on the actual content of these generated images.")

if __name__ == "__main__":
    main()
