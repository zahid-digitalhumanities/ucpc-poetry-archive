@ghazals_bp.route('/share_image/<int:text_id>')
def share_image(text_id):
    dedicator = request.args.get('dedicator', '').strip()
    dedicatee = request.args.get('dedicatee', '').strip()

    ghazal, verses = get_ghazal_with_verses(text_id)
    if not ghazal:
        return jsonify({"error": "Ghazal not found"}), 404

    # Generate image
    img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

    # Absolute path from current working directory (works on Render)
    generated_dir = os.path.join(os.getcwd(), 'static', 'generated')
    os.makedirs(generated_dir, exist_ok=True)

    filename = f"{text_id}_{int(time.time())}.png"
    filepath = os.path.join(generated_dir, filename)

    # Save image
    img.save(filepath, 'PNG')
    file_size = os.path.getsize(filepath)
    print(f"✅ Image saved: {filepath} (size: {file_size} bytes)")

    # If file size is zero, something went wrong
    if file_size == 0:
        return jsonify({"error": "Image generation failed (zero size)"}), 500

    base_url = request.host_url.rstrip('/')
    share_url = f"{base_url}/share/{filename}"
    return jsonify({"share_url": share_url})