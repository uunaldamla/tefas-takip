from datetime import date, timedelta
import pandas as pd
from pytefas import Crawler

FON_KODLARI = [
    "ILH", "YPT", "IOO", "VK6", "TI1", "HLL", "CFO", "YLB",
    "HPV", "HKV", "YVD", "ZP8", "DCB", "GTL", "GJH", "TZL","YP4", "YJY", "BKY",
]

tefas = Crawler()


def araliktaki_veri(baslangic: date, bitis: date) -> pd.DataFrame:
    parcalar = []
    for kind in ["YAT", "EMK", "BYF"]:
        try:
            df = tefas.fetch(
                start=baslangic.isoformat(),
                end=bitis.isoformat(),
                columns="info",
                kind=kind,
            )
            df = df[df["fund_code"].isin(FON_KODLARI)]
            if not df.empty:
                parcalar.append(df)
        except Exception as e:
            print(f"{kind} çekilirken hata: {e}")
    return pd.concat(parcalar, ignore_index=True) if parcalar else pd.DataFrame()


bugun = date.today()
# Hafta sonu / tatil ihtimaline karşı geriye doğru 10 günlük pencere çekiyoruz
baslangic = bugun - timedelta(days=10)

veri = araliktaki_veri(baslangic, bugun)

if veri.empty:
    raise SystemExit("Son 10 gün içinde hiçbir fon için veri bulunamadı.")

veri = veri.sort_values(["fund_code", "date"]).reset_index(drop=True)

# Her fon için günlük getiriyi (bir önceki işlem gününe göre) hesapla
veri["gunluk_getiri_%"] = veri.groupby("fund_code")["price"].pct_change() * 100

# Her fonun EN SON (en güncel) satırını al
son_veri = veri.sort_values("date").groupby("fund_code").tail(1).sort_values("fund_code")

bulunanlar = set(son_veri["fund_code"].unique())
bulunamayanlar = set(FON_KODLARI) - bulunanlar
if bulunamayanlar:
    print(f"UYARI: şu kodlar bulunamadı: {sorted(bulunamayanlar)}\n")

print(son_veri[["date", "fund_code", "fund_name", "price", "gunluk_getiri_%"]].to_string(index=False))

son_veri.to_csv("fonlar_gunluk_getiri.csv", index=False)
print("\nSonuçlar 'fonlar_gunluk_getiri.csv' dosyasına da kaydedildi.")
