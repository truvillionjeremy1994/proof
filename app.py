@app.route('/upload', methods=['POST', 'GET'])
def upload():
    filename = session.get('filename')
    base_score = session.get('base_score')
    boosted_score = session.get('boosted_score')
    boost_delta = None

    if request.method == 'POST':
        file = request.files['image']
        if not file:
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        increment_upload_count()
        session_id = generate_session_id()

        from logger import compute_texture_score, compute_lighting_score
        tex = compute_texture_score(filepath)
        light = compute_lighting_score(filepath)
        hour = datetime.utcnow().hour
        tap = 1
        drift = 0.0

        base_score = predict_confidence_score([tex, light, hour, tap, drift], proof_model)

        session['session_id'] = session_id
        session['base_score'] = base_score
        session['boosted_score'] = base_score
        session['display_score'] = base_score
        session['filename'] = filename
        session['tap_boost_requested'] = False
        session['tap_count'] = 1

        log_signal_event(
            filepath=SIGNAL_LOG_FILE,
            filename=filename,
            image_path=filepath,
            request_meta={"ip": request.remote_addr, "user_agent": request.headers.get("User-Agent", "")},
            session_meta={"session_id": session_id},
            prior_filenames=PREVIOUS_UPLOADS
        )

        return redirect(url_for('upload'))

    if request.method == 'GET' and not session.get('filename'):
        return redirect(url_for('cleanup'))

    if 'boost' in request.args:
        session['tap_boost_requested'] = True
        return redirect(url_for('upload'))

    if session.get('tap_boost_requested') == True:
        session['tap_boost_requested'] = False
        true_score_before = session.get("boosted_score")
        display_score = session.get("display_score", session.get("base_score", 0))

        filepath = os.path.join(UPLOAD_FOLDER, session.get("filename"))

        from logger import compute_texture_score, compute_lighting_score
        tex = compute_texture_score(filepath)
        light = compute_lighting_score(filepath)
        hour = datetime.utcnow().hour
        tap = session.get("tap_count", 1)
        drift = display_score - session.get("base_score", 0)

        true_score_after = predict_confidence_score([tex, light, hour, tap, drift], proof_model)

        display_score = max(display_score, true_score_after)
        session['boosted_score'] = true_score_after
        session['display_score'] = display_score
        session['tap_count'] = tap + 1
        boost_delta = round(display_score - true_score_before, 2)

        log_click_event(
            filepath=CLICK_LOG_FILE,
            filename=session.get("filename"),
            score_before=true_score_before,
            score_after=true_score_after,
            request_meta={"ip": request.remote_addr, "user_agent": request.headers.get("User-Agent", "")},
            session_meta=session
        )

    score = session.get("display_score", base_score or 0)
    result = "honest" if score >= 80 else "deceptive"
    intent_label = "✅ Honest Photo" if result == "honest" else "❌ Deceptive Photo"

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    base64_image = encode_image_base64(filepath)

    try:
        os.remove(filepath)
        session['filename'] = None
    except Exception:
        pass

    meta = {
        "filename": filename,
        "timestamp": datetime.utcnow().isoformat(),
        "score": score,
        "verdict": result
    }

    return render_template(
        "result.html",
        score=score,
        intent_label=intent_label,
        result=result,
        meta=meta,
        boost_delta=boost_delta,
        base64_image=base64_image
    )