@ghazals_bp.route('/share_image/<int:text_id>')
def share_image(text_id):
    """Generate ghazal PNG, save it, and return shareable URL."""

    import os
    import time

    dedicator = request.args.get('dedicator', '').strip()
    dedicatee = request.args.get('dedicatee', '').strip()

    ghazal, verses = get_ghazal_with_verses(text_id)
    if not ghazal:
        return jsonify({"error": "Ghazal not found"}), 404

    # 🔥 Generate Image
    img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

    # 📁 Ensure directory exists
    generated_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'generated')
    generated_dir = os.path.abspath(generated_dir)
    os.makedirs(generated_dir, exist_ok=True)

    # 🧠 Unique filename
    filename = f"{text_id}_{int(time.time())}.png"
    filepath = os.path.join(generated_dir, filename)

    # 💾 Save image
    img.save(filepath, 'PNG')

    # 🌐 Build URLs
    base_url = request.host_url.rstrip('/')

    image_url = f"{base_url}/static/generated/{filename}"
    share_url = f"{base_url}/share/{filename}"

    # 🔥 RETURN BOTH
    return jsonify({
        "image_url": image_url,
        "share_url": share_url
    })