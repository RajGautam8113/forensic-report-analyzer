"""
Evidence Media Processor
Handles image OCR and video keyframe extraction for body condition evidence.
Uses EasyOCR for text extraction and OpenCV for video frame extraction.
"""

import os
import easyocr

# Lazy-load the EasyOCR reader (it's heavy)
_ocr_reader = None


def _get_ocr_reader():
    """Get or create the EasyOCR reader (singleton pattern)."""
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}


def get_media_type(filename):
    """
    Determine if a file is an image, video, or unsupported.

    Returns:
        'image', 'video', or None
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    return None


def process_evidence_image(filepath):
    """
    Run OCR on an evidence image to extract any visible text.
    This helps detect injuries, medical info, or scene details visible in photos.

    Args:
        filepath: path to the image file

    Returns:
        str — extracted text (may be empty if no text found)
    """
    try:
        reader = _get_ocr_reader()
        results = reader.readtext(filepath, detail=0)
        return '\n'.join(results).strip()
    except Exception as e:
        print(f"[MediaProcessor] OCR error on {filepath}: {e}")
        return ""


def process_evidence_video(filepath, frame_interval=2, max_frames=10):
    """
    Extract keyframes from a video and run OCR on each frame.
    Hybrid approach: extract a frame every `frame_interval` seconds,
    capped at `max_frames` total.

    Args:
        filepath: path to the video file
        frame_interval: seconds between frame captures
        max_frames: maximum number of frames to process

    Returns:
        str — combined OCR text from all extracted frames
    """
    try:
        import cv2
    except ImportError:
        print("[MediaProcessor] opencv-python not installed, skipping video processing")
        return ""

    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            print(f"[MediaProcessor] Cannot open video: {filepath}")
            return ""

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or total_frames <= 0:
            cap.release()
            return ""

        duration = total_frames / fps
        # Calculate frame positions: every `frame_interval` seconds, capped at max_frames
        frame_positions = []
        t = 0
        while t < duration and len(frame_positions) < max_frames:
            frame_positions.append(int(t * fps))
            t += frame_interval

        # If we got too few frames (very short video), add a few more
        if len(frame_positions) < 3 and total_frames > 10:
            step = total_frames // min(5, total_frames)
            for i in range(0, total_frames, step):
                if i not in frame_positions and len(frame_positions) < max_frames:
                    frame_positions.append(i)
            frame_positions.sort()

        all_texts = []
        reader = _get_ocr_reader()

        # Create temp dir for frames
        temp_dir = os.path.join(os.path.dirname(filepath), '_temp_frames')
        os.makedirs(temp_dir, exist_ok=True)

        try:
            for idx, frame_num in enumerate(frame_positions):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    continue

                # Save frame temporarily for OCR
                frame_path = os.path.join(temp_dir, f'frame_{idx}.jpg')
                cv2.imwrite(frame_path, frame)

                # Run OCR
                try:
                    results = reader.readtext(frame_path, detail=0)
                    text = '\n'.join(results).strip()
                    if text:
                        all_texts.append(f"[Frame at {frame_num/fps:.1f}s] {text}")
                except Exception as e:
                    print(f"[MediaProcessor] OCR error on frame {idx}: {e}")

                # Clean up temp frame
                try:
                    os.remove(frame_path)
                except OSError:
                    pass
        finally:
            # Clean up temp directory
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass

        cap.release()
        return '\n'.join(all_texts).strip()

    except Exception as e:
        print(f"[MediaProcessor] Video processing error on {filepath}: {e}")
        return ""


def process_evidence_file(filepath, frame_interval=2, max_frames=10):
    """
    Process any evidence file (image or video) and extract text.

    Args:
        filepath: path to the evidence file
        frame_interval: for videos — seconds between frame captures
        max_frames: for videos — max frames to process

    Returns:
        dict with keys: media_type, ocr_text
    """
    media_type = get_media_type(filepath)

    if media_type == 'image':
        ocr_text = process_evidence_image(filepath)
    elif media_type == 'video':
        ocr_text = process_evidence_video(filepath, frame_interval, max_frames)
    else:
        ocr_text = ""
        media_type = 'unknown'

    return {
        'media_type': media_type,
        'ocr_text': ocr_text,
    }
