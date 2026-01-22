from flask import Flask, render_template, request
import numpy as np
import requests
import json
import os
from collections import Counter

app = Flask(__name__)

# ============ KONFIG OPENROUTER ============
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Statistika Deskriptif AI"
}

MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# ============ FUNGSI AI ============
def minta_ai(teks):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Kamu adalah dosen statistika yang menulis kesimpulan analisis data secara formal dan akademik."},
            {"role": "user", "content": teks}
        ],
        "temperature": 0.3
    }
    r = requests.post(OPENROUTER_URL, headers=HEADERS, data=json.dumps(payload))
    return r.json()["choices"][0]["message"]["content"]

# ============ ROUTE ============
@app.route("/", methods=["GET", "POST"])
def index():
    hasil = None
    kesimpulan = ""
    tabel = []

    if request.method == "POST":
        data_input = request.form["data"]
        try:
            data = [float(x.strip()) for x in data_input.split(",") if x.strip() != ""]
            if len(data) == 0:
                raise ValueError("Data kosong")
        except:
            return render_template("index.html", error="Input tidak valid! Pastikan hanya angka dan dipisahkan koma.")

        arr = np.array(data)
        arr_sorted = np.sort(arr)

        # ====== Statistik Dasar ======
        mean = np.mean(arr)
        median = np.median(arr)

        # ====== Modus (DIBENERIN TOTAL) ======
        counts = Counter(arr)
        max_freq = max(counts.values())
        modus_list = [float(k) for k, v in counts.items() if v == max_freq]

        # Format modus supaya TIDAK muncul [ ]
        if len(modus_list) == 1:
            modus_tampil = str(modus_list[0])
        else:
            modus_tampil = ", ".join(str(x) for x in modus_list)

        # ====== Kuartil ======
        Q1 = np.percentile(arr_sorted, 25)
        Q2 = np.percentile(arr_sorted, 50)
        Q3 = np.percentile(arr_sorted, 75)

        # ====== Tabel Distribusi Frekuensi ======
        freq = Counter(arr_sorted)
        for nilai, f in freq.items():
            tabel.append({"nilai": float(nilai), "frekuensi": f})

        hasil = {
            "mean": round(mean, 4),
            "median": round(median, 4),
            "modus": modus_tampil,      # <<< SUDAH STRING BERSIH
            "Q1": round(Q1, 4),
            "Q2": round(Q2, 4),
            "Q3": round(Q3, 4),
            "n": len(arr)
        }

        # ====== Kirim ke AI (PAKAI VERSI TEKS BERSIH) ======
        ringkasan = f"""
Diberikan data numerik sebanyak {len(arr)} buah.

Hasil perhitungan statistik:
- Mean = {round(mean,4)}
- Median = {round(median,4)}
- Modus = {modus_tampil}
- Kuartil 1 (Q1) = {round(Q1,4)}
- Kuartil 2 (Q2) = {round(Q2,4)}
- Kuartil 3 (Q3) = {round(Q3,4)}

Tabel distribusi frekuensi:
{tabel}

Tolong buatkan:
1. Interpretasi karakteristik data (pemusatan dan penyebaran posisi data)
2. Kesimpulan analisis statistik secara formal dan akademik.
"""

        kesimpulan = minta_ai(ringkasan)

        # ====== POSISI KUARTIL UNTUK VISUAL ======
        min_val = float(arr_sorted[0])
        max_val = float(arr_sorted[-1])

        def scale_pos(value, min_v, max_v):
            if max_v == min_v:
                return 50
            return ((value - min_v) / (max_v - min_v)) * 100

        q1_pos = scale_pos(Q1, min_val, max_val)
        q2_pos = scale_pos(Q2, min_val, max_val)
        q3_pos = scale_pos(Q3, min_val, max_val)

        return render_template(
            "index.html",
            hasil=hasil,
            tabel=tabel,
            kesimpulan=kesimpulan,
            q1_pos=q1_pos,
            q2_pos=q2_pos,
            q3_pos=q3_pos,
            hasil_min=min_val,
            hasil_max=max_val
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
