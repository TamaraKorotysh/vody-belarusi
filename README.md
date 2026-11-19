# Воды Беларуси

Интерактивная low-poly 3D-карта рек и озёр Беларуси (three.js).

- `vody-belarusi.html` (и его копия `index.html` для GitHub Pages) — готовая страница, один файл, открывается в браузере.
- Сайт: https://tamarakorotysh.github.io/vody-belarusi/
- `lp_template.html` — код страницы (сцена, булавки, карточки, поиск).
- `cards.js`, `cards2.js` — тексты карточек по-русски; `cards_be.js` — те же карточки по-белорусски. Цифры сверены с «Блакітнай кнігай Беларусі» (1994).
- `blakitnaja-kniha-bielarusi-dzisko.pdf` (с распознанным текстом) и `Blakitnaja_kniha_Bielarusi.djvu` (только сканы) — две копии одного издания; `data/book.txt` — текст из PDF. Сканы и текст книги защищены авторским правом и в репозиторий не входят: положите их в папку проекта сами.
- `data/` — данные OpenStreetMap (реки, озёра, граница, города), рельеф (`dem/`), промежуточные файлы сборки.
- `scripts/` — скачивание и обработка данных.

## Пересборка

Скрипты обработки запускаются из папки `data`:

    cd data
    python ../scripts/group_rivers.py   # малые реки из tiles/ -> rivers_auto.json
    python ../scripts/fix_mouths.py     # белорусские названия устьев
    python ../scripts/book_rivers.py book.txt   # цифры малых рек по книге -> book_auto.json
    python ../scripts/fix_mouths.py     # ручные поправки устьев и совпадений с книгой
    python ../scripts/make_lake_cards.py   # карточки озёр из nom_lakes.json (fetch_lakes.py) -> ../cards_lakes.js
    python ../scripts/export_geo.py     # -> geo_ll.json
    python ../scripts/prep3d.py         # -> d3.json
    python ../scripts/prep_lp.py        # рельеф и вода -> lp.json
    python ../scripts/build_lp.py       # -> ../vody-belarusi.html

Если менялись только тексты карточек или `lp_template.html`, достаточно `build_lp.py`.

## Источники данных

- Реки, озёра, граница, города: © участники OpenStreetMap, лицензия ODbL (https://www.openstreetmap.org/copyright).
- Рельеф: Mapzen / AWS Terrain Tiles.
- Цифры в карточках: «Блакітная кніга Беларусі», Мінск, Беларуская энцыклапедыя, 1994.
