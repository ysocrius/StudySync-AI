import fitz  # PyMuPDF
from youtube_transcript_api import YouTubeTranscriptApi
import os
import io
import easyocr
import numpy as np
from PIL import Image

# Initialize EasyOCR reader (lazy loading)
_ocr_reader = None

def get_ocr_reader():
    """Lazy load EasyOCR reader to avoid startup delay."""
    global _ocr_reader
    if _ocr_reader is None:
        print("Initializing EasyOCR (first time only)...")
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader

def process_page_ocr(page_num, doc, reader):
    """Process a single page with OCR. Helper function for parallel processing."""
    try:
        page = doc[page_num]
        
        # Convert page to image using PyMuPDF
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image then to numpy array
        img = Image.open(io.BytesIO(img_data))
        img_array = np.array(img)
        
        # Perform OCR
        result = reader.readtext(img_array, detail=0)
        page_text = " ".join(result)
        
        print(f"  ✓ Completed page {page_num+1}")
        return (page_num, page_text)
    except Exception as e:
        print(f"  ✗ Error on page {page_num+1}: {e}")
        return (page_num, "")

def extract_text_from_pdf(pdf_path, progress_callback=None):
    """
    Extracts text from a PDF file using a True Hybrid Strategy.
    - Checks for cached OCR first.
    - Iterates page by page.
    - Case A (Scanned Page): If text < 50 chars, render full page and OCR.
    - Case B (Hybrid Page): If text > 50 chars, use digital text AND extract/OCR significant images (diagrams).
    - Saves combined result to cache.
    """
    final_text = []
    try:
        if progress_callback:
            progress_callback(f"Checking cache for {os.path.basename(pdf_path)}...")
            
        # Check for cached OCR results
        cache_file = pdf_path + ".ocr_cache.txt"
        pdf_mtime = os.path.getmtime(pdf_path)
        
        # Use cache if it exists and is newer than the PDF
        if os.path.exists(cache_file):
            cache_mtime = os.path.getmtime(cache_file)
            if cache_mtime > pdf_mtime:
                print(f"Loading cached OCR results for {os.path.basename(pdf_path)}...")
                if progress_callback:
                    progress_callback(f"Loading cached results for {os.path.basename(pdf_path)}...")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
        
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        print(f"Processing {os.path.basename(pdf_path)} ({num_pages} pages)...")
        
        ocr_reader = None # Lazy load only if needed
        
        if progress_callback:
             progress_callback(f"Analyzing {num_pages} pages...")

        for page_num, page in enumerate(doc):
            # 1. Try Digital Extraction
            page_text = page.get_text()
            
            # 2. Decision Logic
            if len(page_text.strip()) > 50:
                # Case B: Hybrid Page (Digital Text + Potential Diagrams)
                msg = f"  Page {page_num+1}: Digital content ({len(page_text)} chars). Checking for diagrams..."
                print(msg)
                
                # Check for images
                image_list = page.get_images(full=True)
                if image_list:
                    print(f"    Found {len(image_list)} images on page.")
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Filter small images (icons/logos)
                        try:
                            pil_img = Image.open(io.BytesIO(image_bytes))
                            width, height = pil_img.size
                            if width > 200 and height > 200:
                                # Significant image found - OCR it!
                                print(f"    Running OCR on image {img_index+1} ({width}x{height})...")
                                if progress_callback:
                                    progress_callback(f"OCRing Diagram on Page {page_num+1}...")
                                
                                if ocr_reader is None:
                                    ocr_reader = get_ocr_reader()
                                
                                img_array = np.array(pil_img)
                                result = ocr_reader.readtext(img_array, detail=0)
                                ocr_text = " ".join(result)
                                
                                if len(ocr_text.strip()) > 10:
                                    page_text += f"\n\n[Diagram/Image Text]:\n{ocr_text}\n"
                                    print(f"    ✓ Extracted {len(ocr_text)} chars from image.")
                        except Exception as img_err:
                            print(f"    Warning: Could not process image {img_index}: {img_err}")
                
                final_text.append(page_text)
                
            else:
                # Case A: Scanned Page (Render whole page)
                print(f"  Page {page_num+1}: Mostly image (only {len(page_text.strip())} chars). Full Page OCR.")
                
                if progress_callback:
                    progress_callback(f"Full OCR needed for Page {page_num+1}...")
                
                # Lazy Init OCR
                if ocr_reader is None:
                    ocr_reader = get_ocr_reader()
                
                # Render Page to Image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                img_array = np.array(img)
                
                # Run OCR
                result = ocr_reader.readtext(img_array, detail=0)
                ocr_text = " ".join(result)
                final_text.append(ocr_text)
                print(f"    ✓ Full Page OCR: {len(ocr_text)} chars extracted.")
        
        full_text = "\n".join(final_text)
        doc.close()
        
        # Cache results
        if full_text.strip():
            print(f"  Saving results to cache...")
            if progress_callback:
                progress_callback("Saving to cache...")
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return full_text

    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
        return ""

# ... End of extract_text_from_pdf ...

def get_video_id(url):
    """Extracts video ID from a YouTube URL."""
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    if "youtube.com" in url:
        return url.split("v=")[1].split("&")[0]
    return url

def extract_transcript_from_youtube(video_url):
    """Extracts transcript from a YouTube video."""
    video_id = get_video_id(video_url)
    try:
        api = YouTubeTranscriptApi()
        fetched_transcript = api.fetch(video_id)
        transcript_text = " ".join([snippet.text for snippet in fetched_transcript.snippets])
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript for {video_url}: {e}")
        return ""

def validate_video_captions(video_url):
    """
    Checks if a video has available transcripts/captions.
    Returns (True, None) if valid, or (False, error_message) if invalid.
    """
    try:
        video_id = get_video_id(video_url)
        
        # This version of the library requires instantiation and uses .list()
        api = YouTubeTranscriptApi()
        
        if hasattr(api, 'list'):
            # It returns a string representation or object, just need to see if it raises error
            api.list(video_id)
        elif hasattr(YouTubeTranscriptApi, 'list_transcripts'):
             # Standard newer static method
             YouTubeTranscriptApi.list_transcripts(video_id)
        elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
             # Standard older static method
             YouTubeTranscriptApi.get_transcript(video_id)
        else:
             # Fallback: try fetching directly
             api.fetch(video_id)
            
        return True, None
    except Exception as e:
        error_msg = str(e)
        if "TranscriptsDisabled" in error_msg:
             return False, "Captions are disabled for this video."
        if "NoTranscriptFound" in error_msg:
             return False, "No captions found for this video. Please upload a video with captions."
        
        return False, f"Could not find captions: {error_msg}"

def load_data(pdf_paths=None, video_urls=None, progress_callback=None):
    """Loads content from provided PDF paths and YouTube URLs."""
    content = []
    
    # 1. Defaults for backward compatibility
    if pdf_paths is None:
        default_pdf = os.path.join(os.path.dirname(__file__), "data", "chapter.pdf")
        if os.path.exists(default_pdf):
             pdf_paths = [default_pdf]
        else:
             pdf_paths = []
             print(f"Warning: Default PDF not found at {default_pdf}")

    if video_urls is None:
        video_urls = [
            "https://youtu.be/Ec19ljjvlCI",
            "https://www.youtube.com/watch?v=Z_S0VA4jKes"
        ]

    # 2. PDF Ingestion
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            print(f"Loading PDF: {pdf_path}")
            if progress_callback:
                progress_callback(f"Loading PDF: {os.path.basename(pdf_path)}...")
            pdf_text = extract_text_from_pdf(pdf_path, progress_callback)
            if pdf_text:
                content.append({"source": os.path.basename(pdf_path), "text": pdf_text, "type": "pdf"})
        else:
            print(f"Warning: PDF path not found: {pdf_path}")

    # 3. YouTube Ingestion
    for url in video_urls:
        print(f"Loading YouTube: {url}")
        if progress_callback:
             progress_callback(f"Fetching Transcript: {url}...")
        transcript = extract_transcript_from_youtube(url)
        if transcript:
            content.append({"source": f"YouTube ({get_video_id(url)[:4]}...)", "text": transcript, "type": "video"})
            
    return content

if __name__ == "__main__":
    # Test ingestion
    data = load_data()
    print(f"Loaded {len(data)} content items.")
    for item in data:
        print(f"Source: {item['source']}, Length: {len(item['text'])}")
