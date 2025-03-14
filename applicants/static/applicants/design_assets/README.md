# Design Assets Directory

This directory contains design assets used throughout the TAU Agrostudies System Portal.

## Directory Structure

- `/icons`: Contains SVG and PNG icons used in the interface
- `/backgrounds`: Contains background images and patterns
- `/illustrations`: Contains illustrations and decorative images

## Usage Guidelines

1. **File Formats**:
   - Icons: Prefer SVG format for scalability, fallback to PNG if necessary
   - Backgrounds: Use optimized JPG or PNG files
   - Illustrations: SVG preferred, high-quality PNG acceptable

2. **Naming Convention**:
   - Use lowercase letters and hyphens (e.g., `farm-icon.svg`)
   - Include size in filename if relevant (e.g., `hero-background-1920x1080.jpg`)
   - Use descriptive names that indicate the purpose of the asset

3. **Optimization**:
   - Compress all images before adding them to the repository
   - Keep file sizes as small as possible without sacrificing quality
   - Consider using WebP format for better compression when browser support is not an issue

## How to Use

To use these assets in templates:

```html
<!-- For an icon -->
<img src="{% static 'applicants/design_assets/icons/example-icon.svg' %}" alt="Example Icon">

<!-- For a background -->
<div style="background-image: url('{% static 'applicants/design_assets/backgrounds/example-bg.jpg' %}')">
    <!-- Content -->
</div>
```

Remember to include `{% load static %}` at the top of your template file. 