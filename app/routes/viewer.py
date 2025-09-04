from flask import Blueprint, request, render_template, session

viewer_bp = Blueprint("viewer", __name__)

@viewer_bp.route("/viewer", methods=["GET"])
def viewer():
    page = request.args.get("page", default=1, type=int)
    bbox_str = request.args.get("bbox", default="")
    filename = request.args.get("filename") or session.get("uploaded_filename")

    if not filename:
        return "Error: Filename missing", 400

    # Convert bbox string "x0,y0,x1,y1" to list of floats
    try:
        bbox = [float(coord) for coord in bbox_str.split(",")] if bbox_str else []
        if bbox and len(bbox) != 4:
            bbox = []
    except ValueError:
        bbox = []

    return render_template("viewer.html", page=page, bbox=bbox, filename=filename)
