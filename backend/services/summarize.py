import base64
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_image_summaries(image_dir: str) -> tuple[list[str], list[str]]:
    """
    Generate AI summaries for extracted chart images.
    
    Args:
        image_dir: Directory containing extracted images
        
    Returns:
        Tuple of (image_summaries, image_paths)
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    image_summaries = []
    image_paths = []
    
    if not os.path.exists(image_dir):
        return image_summaries, image_paths
    
    images = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    images.sort()
    
    print(f"--- Summarizing {len(images)} images using Gemini ---")
    
    for img_file in images:
        img_path = os.path.join(image_dir, img_file)
        base64_image = encode_image(img_path)
        
        prompt = """You are a financial analyst. Analyze this chart or graph. 
                    Describe the trends, axis labels, and numeric values.
                    If it's not a chart, return 'skip'."""
                    
        msg = model.invoke(
            [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"},
                    ]
                )
            ]
        )
        
        if msg.content.strip().lower() != 'skip':
            image_summaries.append(msg.content)
            image_paths.append(img_path)
        
    return image_summaries, image_paths
