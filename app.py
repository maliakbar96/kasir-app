from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
import csv
import os

app = Flask(__name__)

PRODUK_FILE = 'produk.csv'
TRANSAKSI_FILE = 'transaksi.csv'

def load_produk():
    produk = []
    if os.path.exists(PRODUK_FILE):
        with open(PRODUK_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                produk.append({"nama": row["Nama"], "harga": int(row["Harga"])})
    return produk

def save_all_produk(produk_list):
    with open(PRODUK_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Nama", "Harga"])
        for p in produk_list:
            writer.writerow([p["nama"], p["harga"]])

produk_list = load_produk()
transaksi_list = []
last_transaction_date = datetime.now().date()

@app.route("/", methods=["GET", "POST"])
def index():
    global last_transaction_date, transaksi_list

    current_date = datetime.now().date()
    if current_date != last_transaction_date:
        transaksi_list.clear()
        last_transaction_date = current_date

    kembalian = None
    error = None
    total_tagihan = 0

    if request.method == "POST":
        if "tambah_produk" in request.form:
            nama_baru = request.form["nama_produk_baru"]
            harga_baru = int(request.form["harga_produk_baru"])
            produk_list.append({"nama": nama_baru, "harga": harga_baru})
            save_all_produk(produk_list)
        else:
            nama_produk_list = request.form.getlist("produk[]")
            jumlah_list = request.form.getlist("jumlah[]")

            manual_nama = request.form.getlist("manual_nama[]")
            manual_harga = request.form.getlist("manual_harga[]")
            manual_jumlah = request.form.getlist("manual_jumlah[]")

            bayar = int(request.form["bayar"])
            transaksi_items = []

            # Produk dari daftar
            for nama, jumlah_str in zip(nama_produk_list, jumlah_list):
                if not nama.strip() or not jumlah_str.strip():
                    continue
                jumlah = int(jumlah_str)
                harga = next((p["harga"] for p in produk_list if p["nama"] == nama), 0)
                total = harga * jumlah
                total_tagihan += total
                transaksi_items.append({"produk": nama, "jumlah": jumlah, "total": total})

            # Produk manual
            for n, h, j in zip(manual_nama, manual_harga, manual_jumlah):
                if not n.strip() or not h.strip() or not j.strip():
                    continue
                nama = n.strip()
                harga = int(h.strip())
                jumlah = int(j.strip())
                total = harga * jumlah
                total_tagihan += total
                transaksi_items.append({"produk": nama, "jumlah": jumlah, "total": total})

            if total_tagihan == 0:
                error = "Transaksi tidak valid. Isi setidaknya satu produk atau manual."
            elif bayar < total_tagihan:
                error = f"Uang bayar kurang. Total: Rp{total_tagihan}, Bayar: Rp{bayar}"
            else:
                kembalian = bayar - total_tagihan
                waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for item in transaksi_items:
                    transaksi_list.append({**item, "waktu": waktu})
                with open(TRANSAKSI_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not os.path.exists(TRANSAKSI_FILE) or os.stat(TRANSAKSI_FILE).st_size == 0:
                        writer.writerow(["Produk", "Jumlah", "Total", "Waktu"])
                    for item in transaksi_items:
                        writer.writerow([item["produk"], item["jumlah"], item["total"], waktu])

    return render_template("index_final.html", 
                           produk_list=produk_list, 
                           transaksi_list=transaksi_list, 
                           kembalian=kembalian, 
                           error=error,
                           total_tagihan=total_tagihan)

@app.route("/edit_produk/<int:idx>", methods=["GET", "POST"])
def edit_produk(idx):
    if idx < 0 or idx >= len(produk_list):
        return redirect(url_for("index"))

    produk = produk_list[idx]

    if request.method == "POST":
        produk_list[idx]["nama"] = request.form["nama_produk"]
        produk_list[idx]["harga"] = int(request.form["harga_produk"])
        save_all_produk(produk_list)
        return redirect(url_for("index"))

    return render_template("edit_produk.html", idx=idx, nama_lama=produk["nama"], harga_lama=produk["harga"], produk_list=produk_list)

@app.route("/hapus_produk/<int:idx>")
def hapus_produk(idx):
    if 0 <= idx < len(produk_list):
        del produk_list[idx]
        save_all_produk(produk_list)
    return redirect(url_for("index"))

@app.route("/download_produk")
def download_produk():
    return send_file(PRODUK_FILE, as_attachment=True)
@app.route("/backup_produk")
def backup_produk():
    import shutil
    from datetime import datetime

    tanggal = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = "backup"
    os.makedirs(backup_folder, exist_ok=True)
    backup_path = os.path.join(backup_folder, f"produk_backup_{tanggal}.csv")
    shutil.copy(PRODUK_FILE, backup_path)

    return f"✅ Backup berhasil disimpan ke <code>{backup_path}</code>"

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
