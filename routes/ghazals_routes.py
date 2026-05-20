@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    # ... existing code ...
    
    # Get ALL verses
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu, couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))
    
    all_verses = cur.fetchall()
    
    # FOR POSTER: ONLY FIRST 2 COUPLETS (4 misras)
    poster_verses = all_verses[:2]  # 2 couplets = 4 lines
    
    # FOR WEB: all verses
    return render_template('view.html', 
                          ghazal=ghazal,
                          all_verses=all_verses,  # full for web
                          verses=poster_verses)   # only 2 for image