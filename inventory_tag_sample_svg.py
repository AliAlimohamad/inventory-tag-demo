import os
import cv2
import base64
import numpy as np
from io import BytesIO
from moms_apriltag import TagGenerator3
import tempfile
from pixels2svg import pixels2svg
from PIL import Image, ImageDraw, ImageFont

def generate_tag_pair(inventory_tag_id, spacing=50, scale=50, font_size=40, top_padding=50, output_svg_path=None):
    """
    Generate a pair of AprilTags based on an input inventory tag ID with vertical padding at the top in SVG format.
    
    The first tag uses tagStandard41h12 (with 2115 unique tags) and the second tag uses 
    tagStandard52h13 (with 48714 unique tags). The valid input range is [0, 103030110).
    
    Args:
        inventory_tag_id (int): Input number in range [0, 103030110)
        spacing (int): Vertical spacing between tags in pixels
        scale (int): Scale factor for tag generation
        font_size (int): Size of the font for ID text
        top_padding (int): Vertical padding at the top of the image
        output_svg_path (str, optional): If provided, the SVG will be saved to this file path.
        
    Returns:
        PIL.Image: Combined image containing SVG tags (compatible with original API)
    """
    # Total unique tag pairs = 2115 * 48714 = 103030110
    if not 0 <= inventory_tag_id < (2115 * 48714):
        raise ValueError("Number must be in range [0, 103030110)")
    
    # Calculate IDs for both tags:
    # - For tagStandard41h12 (2115 unique tags)
    tag_standard1_id = inventory_tag_id // 48714  
    # - For tagStandard52h13 (48714 unique tags)
    tag_standard2_id = inventory_tag_id % 48714   
    
    # Initialize tag generators
    tg_standard1 = TagGenerator3("tagStandard41h12")
    tg_standard2 = TagGenerator3("tagStandard52h13")
    
    # Generate individual tags
    tag_standard1 = tg_standard1.generate(tag_standard1_id, scale=scale*1.171)
    tag_standard2 = tg_standard2.generate(tag_standard2_id, scale=scale)
    
    # Apply binary threshold for cleaner SVG conversion
    _, tag_standard1 = cv2.threshold(tag_standard1, 10, 255, cv2.THRESH_BINARY)
    _, tag_standard2 = cv2.threshold(tag_standard2, 10, 255, cv2.THRESH_BINARY)
    
    # Create a combined image with extra space for text and padding
    height1, width1 = tag_standard1.shape
    height2, width2 = tag_standard2.shape
    
    width = max(width1, width2) + 200  # extra horizontal padding
    text_height = font_size + 20  # space reserved for text annotations
    height = top_padding + height1 + spacing + height2 + (text_height * 4)
    
    # Create a white canvas
    combined_img = np.ones((height, width), dtype=np.uint8) * 255
    
    # Calculate positions to center the tags horizontally
    tag1_x = (width - width1) // 2
    tag2_x = (width - width2) // 2
    
    # Place tags on the canvas
    combined_img[top_padding:top_padding+height1, tag1_x:tag1_x+width1] = tag_standard1
    combined_img[top_padding+height1+spacing+text_height:top_padding+height1+spacing+text_height+height2, tag2_x:tag2_x+width2] = tag_standard2
    
    # Save the combined image to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        temp_path = tmp_file.name
        cv2.imwrite(temp_path, combined_img)
    
    # Convert to SVG using pixels2svg
    svg_base = pixels2svg(temp_path, as_string=True)
    os.unlink(temp_path)  # Clean up temporary file
    
    # Now add text elements to the SVG
    # Find the closing </svg> tag
    end_tag_pos = svg_base.rfind('</svg>')
    
    # Insert text elements before the closing tag
    text_elements = f'''
  <!-- Text Labels -->

  <text x="{width//2}" y="{top_padding + height1 + spacing + text_height + height2 + text_height + 10}"
    font-family="Arial, sans-serif" font-size="{int(font_size * 2)}" font-weight="bold"
    text-anchor="middle" fill="black" stroke-width="3">
    {inventory_tag_id}
  </text>
'''
    
    svg = svg_base[:end_tag_pos] + text_elements + svg_base[end_tag_pos:]
    
    # Optionally save the SVG file to disk if output_svg_path is provided
    if output_svg_path is not None:
        with open(output_svg_path, 'wb') as f:
            f.write(svg.encode('utf-8'))
    
    # Create a PIL Image that will act as a wrapper for the SVG
    # This maintains compatibility with code expecting a PIL Image
    pil_img = Image.new('RGB', (width, height), (255, 255, 255))
    
    # Add the SVG save method to maintain compatibility
    pil_img.save = lambda fp, format=None, **params: fp.write(svg.encode('utf-8')) if hasattr(fp, 'write') else open(fp, 'wb').write(svg.encode('utf-8'))
    
    return pil_img
tag_id_inv=2
img = generate_tag_pair(tag_id_inv, output_svg_path=f"laptop_tagid_{tag_id_inv}.svg")
