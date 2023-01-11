#!/bin/bash
# This script downloads the latest shapefiles from ISTAT and imports them into the database.

# creating a temporary working directory
mkdir -p download_shapes
cd download_shapes

#downloading and unzipping the shapefiles from ISTAT (2022 link)
wget https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/Limiti01012022_g.zip
unzip Limiti01012022_g.zip

wget https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/Limiti01012022.zip
unzip Limiti01012022.zip

# importing via django management command
cd ..
python manage.py update_geo download_shapes/Limiti01012022_g/Reg01012022_g/Reg01012022_g_WGS84.shp download_shapes/Limiti01012022_g/ProvCM01012022_g/ProvCM01012022_g_WGS84.shp download_shapes/Limiti01012022_g/Com01012022_g/Com01012022_g_WGS84.shp download_shapes/Limiti01012022/Com01012022/Com01012022_WGS84.shp

# cleaning up
rm -rf download_shapes