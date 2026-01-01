# app.py
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import io
import pandas as pd
from weather import get_latitude_longitude, get_past_n_days_max_min_temperature, json_to_dataframe, create_plot_image_bytes

app = Flask(__name__)
app.secret_key = "change_this_for_production"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        days = request.form.get("days", "7").strip()
        try:
            days = int(days)
        except ValueError:
            flash("Days must be a number")
            return redirect(url_for("index"))
        if not city:
            flash("Enter a city name")
            return redirect(url_for("index"))
        if days <= 0 or days > 365:
            flash("Days must be between 1 and 365")
            return redirect(url_for("index"))
        return redirect(url_for("results", city=city, days=days))
    return render_template("index.html")

@app.route("/results")
def results():
    city = request.args.get("city", "")
    days = int(request.args.get("days", 7))
    try:
        lat, lon = get_latitude_longitude(city)
        daily = get_past_n_days_max_min_temperature(lat, lon, days)
        df = json_to_dataframe(daily)
    except Exception as e:
        flash(f"Error fetching data: {e}")
        return redirect(url_for("index"))

    img_buf = create_plot_image_bytes(df, city)
    img_b64 = "data:image/png;base64," + (io.BytesIO(img_buf.getvalue()).getvalue()).hex()  # placeholder, replaced in template with proper encoding

    # Better approach: encode base64 properly in template
    import base64
    img_b64 = "data:image/png;base64," + base64.b64encode(img_buf.read()).decode("utf-8")
    table_html = df.to_html(classes="table table-striped", index=False, float_format="%.2f")
    return render_template("results.html", city=city, days=days, plot_data=img_b64, table_html=table_html)

@app.route("/download_csv")
def download_csv():
    city = request.args.get("city", "")
    days = int(request.args.get("days", 7))
    lat, lon = get_latitude_longitude(city)
    daily = get_past_n_days_max_min_temperature(lat, lon, days)
    df = json_to_dataframe(daily)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     attachment_filename=f"{city}_weather_{days}d.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
