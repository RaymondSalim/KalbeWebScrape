# WebScraping
###Pengunaan:
####Scraping:
```
python main.py scrape
```
```
usage: main.py scrape -m  -q  -p  -r

required arguments:
  -m , --marketplace   nama ecommerce (tokopedia / shopee / bukalapak)
  -q , --query         kata kunci untuk search ("masker" / "ANLENE GOLD")
  -p , --page          jumlah halaman yang akan di scrape (untuk menscrape semua halaman tulis 0)
  -r , --result        the file format for the results (json/csv)

```
Contoh:
```
python main.py scrape -m tokopedia -q "ANLENE GOLD" -p 0 -r csv
```

File akan tersimpan di ./Output