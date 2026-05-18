"""
Crea las carpetas + data.json de los productos de ejemplo bajo content/.

Uso:
    python scripts/seed_products.py
    python manage.py sync_content

Estructura generada por cada producto:
    content/categorias/<parent>/<sub>/productos/<product-slug>/data.json

Cada data.json incluye: slug, name, price (COP), stock, sku, brand,
description, active=true, images=[]. Es idempotente: si ya existe
data.json, lo sobrescribe (datos = fuente de verdad del script).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / 'content' / 'categorias'

# Cada item:
#   (parent_slug, sub_slug, product_slug, name, price, stock, sku, brand, description)
PRODUCTS = [
    # ─────────────────────── CCTV / Videovigilancia ───────────────────────
    # Cámaras IP
    ('cctv-videovigilancia', 'camaras-ip', 'hikvision-ds-2cd1043g0-i',
     'Cámara IP Bullet 4MP Hikvision DS-2CD1043G0-I', 380000, 18,
     'DS-2CD1043G0-I', 'Hikvision',
     'Cámara IP tipo bala 4MP (2560×1440) con IR de 30 m. Compatible con H.265+ que reduce ancho de banda hasta 70%. PoE 802.3af, carcasa metálica IP67 para exteriores. Detección de movimiento por software con notificaciones push vía Hik-Connect.'),
    ('cctv-videovigilancia', 'camaras-ip', 'dahua-dh-ipc-hdw1230t1-s5',
     'Cámara IP Domo 2MP Dahua DH-IPC-HDW1230T1-S5', 290000, 22,
     'DH-IPC-HDW1230T1-S5', 'Dahua',
     'Domo IP 2MP con lente fija 2.8 mm e IR 30 m. Tecnología Starlight para color en 0.008 lux. Micrófono integrado, slot microSD 256 GB, PoE, H.265+ y WDR 120 dB.'),
    ('cctv-videovigilancia', 'camaras-ip', 'hanwha-wisenet-xnf-5010v',
     'Cámara IP Fisheye 5MP Hanwha Wisenet XNF-5010V', 1450000, 6,
     'XNF-5010V', 'Hanwha',
     'Fisheye 5MP con vista panorámica 360°. Modos desenvuelto, panorámico o multivista. H.265 con análisis IVS (merodeo, paso de línea). PoE, IK10 antivandálica, dewarping en vivo sin licencia.'),

    # Cámaras analógicas
    ('cctv-videovigilancia', 'camaras-analogicas', 'hikvision-ds-2ce16d0t-itf',
     'Cámara analógica Turbo HD 2MP Hikvision DS-2CE16D0T-ITF', 95000, 30,
     'DS-2CE16D0T-ITF', 'Hikvision',
     'Bullet HD-TVI 2MP (1920×1080) con lente fija 2.8 mm e IR EXIR 20 m. Soporte coaxial hasta 500 m sin pérdida. Carcasa IP66.'),
    ('cctv-videovigilancia', 'camaras-analogicas', 'dahua-hac-hdw1400tlp-0280b',
     'Cámara analógica Domo 4MP Dahua HAC-HDW1400TLP-0280B', 145000, 25,
     'HAC-HDW1400TLP-0280B', 'Dahua',
     'Domo 4MP con sensor CMOS y señal seleccionable HDCVI/AHD/TVI/CVBS. IR 20 m, micrófono integrado, audio por coaxial. WDR digital, IP67/IK10.'),
    ('cctv-videovigilancia', 'camaras-analogicas', 'hikvision-ds-2ce79h0t-ait3zf',
     'Cámara analógica Motorizada 5MP TVI Hikvision DS-2CE79H0T-AIT3ZF', 280000, 12,
     'DS-2CE79H0T-AIT3ZF', 'Hikvision',
     'Bullet motorizada 5MP con varifocal 2.7–13.5 mm (5x) ajustable desde el DVR. IR 40 m, OSD multilenguaje y control UTC. IP67.'),

    # Cámaras PTZ
    ('cctv-videovigilancia', 'camaras-ptz', 'hikvision-ds-2de5225iw-ae',
     'Cámara PTZ IP 2MP 25x Hikvision DS-2DE5225IW-AE(S6)', 3850000, 4,
     'DS-2DE5225IW-AE-S6', 'Hikvision',
     'PTZ domo 2MP zoom óptico 25x. Pan 360° continuo, tilt -5°/90°, 200°/s. Autotracking 2.0, IR 100 m, WDR 120 dB. PoE+ o 24 VAC, IK10.'),
    ('cctv-videovigilancia', 'camaras-ptz', 'dahua-sd42212t-hn-s2',
     'Cámara PTZ IP 4MP 20x Dahua SD42212T-HN(-S2)', 3450000, 5,
     'SD42212T-HN-S2', 'Dahua',
     'PTZ exterior 4MP zoom 20x. Pan 360° infinito, tilt -15°/90°. H.265, microSD 256 GB, IVS, IR 100 m, IP66.'),
    ('cctv-videovigilancia', 'camaras-ptz', 'hikvision-ds-2ae4225t-d',
     'Cámara PTZ Analógica 2MP 18x Hikvision DS-2AE4225T-D', 2150000, 6,
     'DS-2AE4225T-D', 'Hikvision',
     'PTZ HD-TVI 2MP zoom 18x compatible HDCVI/TVI/AHD/CVBS. 120°/s, 256 presets, IR 100 m, control RS-485 o UTC.'),

    # Cámaras WiFi
    ('cctv-videovigilancia', 'camaras-wifi', 'tplink-tapo-c310',
     'Cámara WiFi 3MP TP-Link Tapo C310', 175000, 35,
     'TAPO-C310', 'TP-Link',
     'Bullet exterior 3MP (2304×1296), WiFi 2.4 GHz, IR 30 m, audio bidireccional, microSD 128 GB. Compatible con Alexa y Google Assistant. IP66.'),
    ('cctv-videovigilancia', 'camaras-wifi', 'imou-ranger-2',
     'Cámara WiFi 2K Imou Ranger 2', 215000, 28,
     'IPC-A22EP', 'Imou',
     'Domo robótica interior 2K, pan 355° tilt 90°, WiFi dual banda. Detección IA de personas con seguimiento automático. Modo privacidad mecánico, microSD 256 GB.'),
    ('cctv-videovigilancia', 'camaras-wifi', 'ezviz-c3w-pro',
     'Cámara WiFi 4MP Ezviz C3W Pro', 320000, 20,
     'CS-C3W-A0-3H4WFRL', 'Ezviz',
     'Bullet exterior 4MP con WiFi y doble antena. IR 30 m, audio bidireccional, microSD 256 GB. Detección IA de personas. IP67.'),

    # Cámaras ocultas
    ('cctv-videovigilancia', 'camaras-ocultas', 'oculta-usb-1080p',
     'Cámara oculta USB con grabación en SD', 95000, 40,
     'SPY-USB-1080', 'Generic',
     'Minicámara camuflada en adaptador USB funcional. 1080p, lente 140°, grabación continua o por movimiento en microSD hasta 32 GB.'),
    ('cctv-videovigilancia', 'camaras-ocultas', 'oculta-detector-humo',
     'Cámara oculta en detector de humo 1080p', 165000, 22,
     'SPY-SMOKE-1080', 'Generic',
     'Apariencia de detector de humo. Sensor 2MP, ángulo 130°, IR 5 m, WiFi para visualización en vivo. Batería 3000 mAh hasta 15 días en modo PIR.'),
    ('cctv-videovigilancia', 'camaras-ocultas', 'oculta-cargador-pared-4k',
     'Cámara oculta en cargador de pared 4K', 230000, 15,
     'SPY-CHRG-4K', 'Generic',
     'Espía 4K integrada en cargador USB de pared. WiFi 2.4 GHz, IR invisible, grabación local SD 256 GB y transmisión remota. Sensor PIR de alta sensibilidad.'),

    # Cámaras para exterior
    ('cctv-videovigilancia', 'camaras-exterior', 'hikvision-ds-2cd1047g2-l',
     'Cámara Bala 4MP Exterior IP67 Hikvision DS-2CD1047G2-L(UF)', 510000, 16,
     'DS-2CD1047G2-LUF', 'Hikvision',
     'IP bullet 4MP con iluminación híbrida IR + luz blanca y ColorVu para color 24/7. Alarma disuasoria audio/visual. PoE, microSD 256 GB, IP67.'),
    ('cctv-videovigilancia', 'camaras-exterior', 'dahua-ipc-hdw3241emp-as',
     'Cámara Domo Varifocal Motorizado 2MP Exterior Dahua IPC-HDW3241EMP-AS-0280B', 720000, 10,
     'IPC-HDW3241EMP-AS-0280B', 'Dahua',
     'Domo exterior con varifocal motorizada 2.8–12 mm. Sensor 2MP Starlight, audio/alarma, IP67/IK10, PoE. IVS con clasificación humano/vehículo.'),
    ('cctv-videovigilancia', 'camaras-exterior', 'hikvision-ds-2ce12h0t-ait3zf',
     'Cámara Bala Analógica 5MP Exterior Hikvision DS-2CE12H0T-AIT3ZF', 285000, 14,
     'DS-2CE12H0T-AIT3ZF', 'Hikvision',
     'Bullet Turbo HD 5MP con varifocal motorizada 2.7–13.5 mm. IR EXIR 40 m, IP67, OSD por UTC. 2560×1944 para captura de matrículas.'),

    # Cámaras domo
    ('cctv-videovigilancia', 'camaras-domo', 'hikvision-ds-2cd2143g2-iu',
     'Domo IP 4MP Hikvision DS-2CD2143G2-IU', 545000, 18,
     'DS-2CD2143G2-IU', 'Hikvision',
     'Domo interior IP 4MP fijo 2.8 mm, IR 30 m. Micrófono y altavoz integrados, microSD 256 GB, PoE, WDR 120 dB y detección IA Human/Vehicle.'),
    ('cctv-videovigilancia', 'camaras-domo', 'dahua-hac-hdw1200tlqp',
     'Domo Analógico 2MP Dahua HAC-HDW1200TLQP-0280B', 130000, 26,
     'HAC-HDW1200TLQP-0280B', 'Dahua',
     'Domo HDCVI 2MP con micrófono, WDR digital. IR 20 m, lente 2.8 mm. Coaxial hasta 500 m. Penta-brid (HDCVI/AHD/TVI/CVBS). IP67.'),
    ('cctv-videovigilancia', 'camaras-domo', 'uniview-ipc-d226-af40',
     'Domo IP Anti-vandálico 6MP Uniview IPC-D226-AF40', 690000, 9,
     'IPC-D226-AF40', 'Uniview',
     'Domo IP 6MP fijo 4 mm, IR 30 m. IK10/IP67, Smart IR, microSD 256 GB, PoE, H.265 triple flujo. Análisis IVS con detección de rostros.'),

    # Cámaras bala
    ('cctv-videovigilancia', 'camaras-bala', 'hikvision-ds-2cd1a23g0-iz',
     'Bala IP 2MP Larga Distancia Hikvision DS-2CD1A23G0-IZ', 460000, 17,
     'DS-2CD1A23G0-IZ', 'Hikvision',
     'Bala IP 2MP con varifocal motorizada 2.8–12 mm. IR 40 m, IP66, slot SD, PoE o 12 VDC, H.265+, WDR 120 dB.'),
    ('cctv-videovigilancia', 'camaras-bala', 'hikvision-ds-2ce12kf3t-pirx',
     'Bala Analógica 5MP TVI Hikvision DS-2CE12KF3T-PIRX(B)', 340000, 12,
     'DS-2CE12KF3T-PIRX-B', 'Hikvision',
     'Bala 5MP con detector PIR incorporado para reducir falsas alarmas. Luz blanca parpadeante y sirena disuasoria. Lente 2.8 mm, IR 20 m, UTC.'),
    ('cctv-videovigilancia', 'camaras-bala', 'dahua-ipc-hfw2441t-zas',
     'Bala IP 4MP con IA Dahua IPC-HFW2441T-ZAS', 615000, 11,
     'IPC-HFW2441T-ZAS', 'Dahua',
     'Bala IP 4MP varifocal 2.7–13.5 mm, IR 40 m. IVS humano/vehículo, audio/alarma, microSD, PoE, H.265, IP67.'),

    # DVR
    ('cctv-videovigilancia', 'dvr', 'dahua-xvr5116hs-i3',
     'DVR Híbrido Penta-brid 16CH 5MP Dahua XVR5116HS-I3', 980000, 8,
     'XVR5116HS-I3', 'Dahua',
     'Híbrido HDCVI/AHD/TVI/CVBS + IP, 16 analógicos + 8 IP. 5MP analógico, 12MP IP. H.265+, HDMI/VGA, 2 SATA hasta 16 TB, IA en canales seleccionados.'),
    ('cctv-videovigilancia', 'dvr', 'hikvision-ids-7208huhi-m1-p',
     'DVR Turbo HD 8CH 4MP Hikvision iDS-7208HUHI-M1/P', 1150000, 7,
     'iDS-7208HUHI-M1-P', 'Hikvision',
     '8 canales TVI con DeepinMind para analíticas (facial, conteo, mapa de calor). 4MP por canal, H.265Pro+, 1 SATA, 2 USB.'),
    ('cctv-videovigilancia', 'dvr', 'zosi-mini-4ch-1080p',
     'DVR Mini 4CH Full HD 1080p ZOSI H.265+', 320000, 14,
     'ZOSI-DVR-4CH', 'ZOSI',
     'DVR analógico 4 canales 1080p, AHD/TVI/CVI. H.265, HDMI/VGA, 1 SATA hasta 2 TB. Control por app.'),

    # NVR
    ('cctv-videovigilancia', 'nvr', 'hikvision-ds-7608nxi-i2-8p-s',
     'NVR 8CH PoE 8MP Hikvision DS-7608NXI-I2/8P/S', 1980000, 6,
     'DS-7608NXI-I2-8P-S', 'Hikvision',
     '8 puertos PoE, 8MP por canal, H.265+, 2 SATA, IA con cámaras compatibles, 4K HDMI, app Hik-Connect.'),
    ('cctv-videovigilancia', 'nvr', 'dahua-nvr5216-4ks2',
     'NVR 16CH 12MP Dahua NVR5216-4KS2', 2350000, 5,
     'NVR5216-4KS2', 'Dahua',
     '16 canales IP hasta 12MP, ancho de banda 320 Mbps, 2 SATA, IVS y búsqueda inteligente. ONVIF, app DMSS.'),
    ('cctv-videovigilancia', 'nvr', 'reolink-rln8-410',
     'NVR 4CH Compacto Reolink RLN8-410', 980000, 9,
     'RLN8-410', 'Reolink',
     '4 canales con HDD 2 TB y 4 puertos PoE. Plug & play, soporte 4K, gestión por app Reolink.'),

    # Kits de videovigilancia
    ('cctv-videovigilancia', 'kits-videovigilancia', 'kit-hikvision-4ip-4mp',
     'Kit 4 Cámaras IP 4MP con NVR Hikvision DS-2CD2043G0-I', 2150000, 5,
     'KIT-HIK-4IP-4MP', 'Hikvision',
     'NVR 4 canales PoE + 4 bullet IP 4MP IR 30 m IP67 con micrófono. HDD 1 TB y cables incluidos.'),
    ('cctv-videovigilancia', 'kits-videovigilancia', 'kit-dahua-8analog-5mp',
     'Kit 8 Cámaras Analógicas 5MP Dahua XVR-5108HS-4KL-I3', 1850000, 6,
     'KIT-DAH-8AN-5MP', 'Dahua',
     'XVR Penta-brid + 8 bullet 5MP IR 30 m. Cableado coaxial, fuente y HDD 2 TB incluidos.'),
    ('cctv-videovigilancia', 'kits-videovigilancia', 'kit-tplink-tapo-c310-4',
     'Kit Inalámbrico 4 Cámaras WiFi 2K TP-Link Tapo C310', 720000, 8,
     'KIT-TAPO-C310-4', 'TP-Link',
     '4 cámaras bullet WiFi 2K exterior IP66. Sin cables de video. Almacenamiento SD local en cada cámara.'),

    # Discos duros para CCTV
    ('cctv-videovigilancia', 'discos-duros-cctv', 'seagate-skyhawk-4tb',
     'Disco Duro Seagate SkyHawk 4TB ST4000VX007', 460000, 18,
     'ST4000VX007', 'Seagate',
     'HDD para vigilancia 4TB, 7200 RPM, caché 256 MB, SATA III. ImagePerfect para hasta 64 cámaras. 180 TB/año, 24/7.'),
    ('cctv-videovigilancia', 'discos-duros-cctv', 'wd-purple-8tb',
     'WD Purple 8TB WD84PURZ', 780000, 12,
     'WD84PURZ', 'Western Digital',
     'HDD 3.5", 7200 RPM, 256 MB caché. AllFrame para reproducción fluida. Resistente a vibraciones, ideal NVR gama media/alta.'),
    ('cctv-videovigilancia', 'discos-duros-cctv', 'toshiba-s300-2tb',
     'Disco Duro Toshiba S300 2TB', 295000, 22,
     'HDWT720UZSVA', 'Toshiba',
     'Disco para vigilancia, 5400 RPM, SATA 6 Gb/s. Diseñado para 24/7, hasta 32 cámaras. Costo-beneficio para sistemas pequeños.'),

    # Fuentes de poder (CCTV)
    ('cctv-videovigilancia', 'fuentes-poder-cctv', 'fuente-12v-10a-18ch',
     'Fuente de poder 12V 10A Centralizada de 18 Canales', 145000, 30,
     'PSU-12V-18CH', 'Generic',
     'AC/DC conmutada 12V 10A con 18 salidas y fusibles PTC independientes. Carcasa metálica con cerradura y ventilación.'),
    ('cctv-videovigilancia', 'fuentes-poder-cctv', 'switch-poe-8p-120w',
     'Fuente PoE 8 Puertos 10/100Mbps con 120W', 285000, 20,
     'POE-SW-8P-120W', 'Generic',
     'Switch PoE escritorio 8 puertos Fast Ethernet, 120W totales, IEEE 802.3af/at. Protección por puerto.'),
    ('cctv-videovigilancia', 'fuentes-poder-cctv', 'adaptador-12v-2a',
     'Adaptador individual 12V 2A con enchufe', 22000, 80,
     'ADP-12V-2A', 'Generic',
     'Fuente individual 100-240VAC, salida 12V 2A, conector DC 2.1×5.5 mm. Cable 1.2 m.'),

    # Accesorios CCTV
    ('cctv-videovigilancia', 'accesorios-cctv', 'balun-pasivo-utp',
     'Balun Pasivo para Video y Datos por Par Trenzado', 18000, 100,
     'BALUN-UTP-PAR', 'Generic',
     'Par de baluns para video analógico HD (5MP) y control PTZ por UTP CAT5e/6 hasta 300 m. Conector BNC y terminales.'),
    ('cctv-videovigilancia', 'accesorios-cctv', 'caja-conexiones-ip66',
     'Caja de Conexiones de Exterior para Cámaras (Junction Box)', 35000, 60,
     'JBOX-IP66', 'Generic',
     'Caja hermética IP66 de aluminio con prensaestopas. Compatible con cámaras Hikvision/Dahua.'),
    ('cctv-videovigilancia', 'accesorios-cctv', 'soporte-ptz-30cm',
     'Soporte de Pared Ajustable para PTZ de 30 cm', 65000, 25,
     'SPT-PTZ-30', 'Generic',
     'Brazo de acero inoxidable 30 cm articulado. Soporta hasta 15 kg. Para postes o pared.'),

    # ─────────────────────── Alarmas de Seguridad ───────────────────────
    # Kits
    ('alarmas-seguridad', 'kits-alarmas', 'pgst-pa-055-10p',
     'Kit Alarma WiFi PGST PA-055 con 10 Piezas', 380000, 14,
     'PGST-PA-055', 'PGST',
     'Central + sirena, 4 sensores de puerta, 1 PIR, 2 mandos, 2 RFID. WiFi y GSM (SMS y llamadas), batería de respaldo, app sin cuotas.'),
    ('alarmas-seguridad', 'kits-alarmas', 'ajax-hub2-starter',
     'Kit Ajax Hub 2 Starter con 3 Sensores', 1850000, 8,
     'AJAX-HUB2-STARTER', 'Ajax',
     'Hub 2 con 3 MotionProtect, 1 DoorProtect y 1 SpaceControl. Ethernet/WiFi + SIM 2G/3G/4G, Jeweller cifrado hasta 2000 m.'),
    ('alarmas-seguridad', 'kits-alarmas', 'dsc-hs2128-cableado',
     'Kit DSC PowerSeries Neo 8 Zonas con Sensores Cableados', 1450000, 6,
     'HS2128-KIT', 'DSC',
     'Central HS2128 + teclado, 3 PIR cableados, 2 magnéticos, sirena interior. Expansible a 128 zonas.'),

    # Paneles de control
    ('alarmas-seguridad', 'paneles-control', 'ajax-hub2-plus-4g',
     'Panel Ajax Hub 2 Plus 4G', 1750000, 7,
     'AJAX-HUB2-PLUS', 'Ajax',
     'Centro inteligente Jeweller, hasta 200 dispositivos, 50 cámaras, 50 usuarios. Ethernet/WiFi/4G dual SIM. AES, fotos por demanda.'),
    ('alarmas-seguridad', 'paneles-control', 'dsc-neo-hs2128',
     'Panel DSC Neo HS2128', 980000, 9,
     'HS2128', 'DSC',
     'Panel cableado/inalámbrico 8 zonas expandibles a 128. Compatible con teclados táctiles y módulo IP/GSM. Grado 2.'),
    ('alarmas-seguridad', 'paneles-control', 'paradox-sp5500-plus',
     'Panel Paradox SP5500+', 720000, 10,
     'SP5500-PLUS', 'Paradox',
     'Panel modular 8-32 zonas, sensores inalámbricos y teclados. Bidireccional, llave de proximidad, programación PC.'),

    # Sensores de movimiento
    ('alarmas-seguridad', 'sensores-movimiento', 'ajax-motionprotect-plus',
     'Sensor PIR Inalámbrico Ajax MotionProtect Plus', 380000, 18,
     'AJAX-MP-PLUS', 'Ajax',
     'Dual PIR + microondas, inmunidad a mascotas hasta 20 kg. Alcance 12 m, ángulo 88°. SmartDetect, CR123A hasta 5 años.'),
    ('alarmas-seguridad', 'sensores-movimiento', 'optex-ax-100',
     'Detector PIR Cableado Optex AX-100', 285000, 14,
     'AX-100', 'Optex',
     'Largo alcance 24 m, 90°, lente esférica de alta precisión. Compensación de temperatura, inmunidad a mascotas 24 kg.'),
    ('alarmas-seguridad', 'sensores-movimiento', 'bosch-isc-bpr2-w12',
     'Sensor Movimiento Bosch Blue Line ISC-BPR2-W12', 175000, 22,
     'ISC-BPR2-W12', 'Bosch',
     'PIR cableado con procesamiento de primer paso, 12×12 m, montaje en esquina. Carcasa anti-vandálica.'),

    # Sensores magnéticos
    ('alarmas-seguridad', 'sensores-magneticos', 'ajax-doorprotect-plus',
     'Contacto magnético Ajax DoorProtect Plus', 195000, 25,
     'AJAX-DP-PLUS', 'Ajax',
     'Sensor inalámbrico con sensor de inclinación y acelerómetro (vibración de rotura). Alcance 2000 m LOS, CR123A hasta 6 años.'),
    ('alarmas-seguridad', 'sensores-magneticos', 'ck-2450-g',
     'Contacto Magnético Cableado C&K 2450-G', 18000, 90,
     'CK-2450-G', 'C&K',
     'Sensor de superficie con separación hasta 19 mm. Reed sellado, ABS blanco, tornillos antimanipulación.'),
    ('alarmas-seguridad', 'sensores-magneticos', 'bosch-isn-sm-50',
     'Contacto Magnético Empotrable Bosch ISN-SM-50', 32000, 70,
     'ISN-SM-50', 'Bosch',
     'Empotrable en marco de madera, 6.5 mm de diámetro, separación 10 mm. Cola de cables para conexión discreta.'),

    # Sensores de humo
    ('alarmas-seguridad', 'sensores-humo', 'ajax-fireprotect-plus',
     'Detector de Humo Inalámbrico Ajax FireProtect Plus', 415000, 16,
     'AJAX-FP-PLUS', 'Ajax',
     'Fotoeléctrico + temperatura + CO. Interconexión inalámbrica hasta 50 detectores, sirena 85 dB, batería litio 4 años.'),
    ('alarmas-seguridad', 'sensores-humo', 'notifier-sd-851',
     'Detector de Humo Cableado Notifier SD-851', 180000, 30,
     'SD-851', 'Notifier',
     'Fotoeléctrico direccionable para centrales de incendio. Sensibilidad ajustable, montaje en base B501.'),
    ('alarmas-seguridad', 'sensores-humo', 'kidde-10y29',
     'Detector de Humo Autónomo Kidde 10Y29', 95000, 40,
     'KIDDE-10Y29', 'Kidde',
     'Fotoeléctrico con batería sellada de litio 10 años. Botón de prueba/silencio, alarma 85 dB.'),

    # Sensores de gas
    ('alarmas-seguridad', 'sensores-gas', 'tgs-2611-12v',
     'Detector de Gas Natural 12V TGS 2611', 78000, 35,
     'TGS-2611', 'Figaro',
     'Sensor de gas metano con relé NA/NC, 12 VDC. Calentamiento 3 min, LED y zumbador. Conecta a panel o electroválvula.'),
    ('alarmas-seguridad', 'sensores-gas', 'nest-protect-co',
     'Detector de Monóxido de Carbono Nest Protect', 380000, 12,
     'NEST-PROTECT', 'Google Nest',
     'Autónomo con batería 5 años, también detecta humo. Alarma vocal, app, autoprueba cada 200 s.'),
    ('alarmas-seguridad', 'sensores-gas', 'ajax-relay-glp',
     'Detector de Gas LP/GLP Ajax con Relay', 250000, 15,
     'AJAX-GAS-RELAY', 'Ajax',
     'Solución Ajax con módulo Relay para cortar suministro al activarse alarma. Configuración desde app.'),

    # Sensores de vibración
    ('alarmas-seguridad', 'sensores-vibracion', 'ajax-glassprotect',
     'Sensor de Vibración Ajax GlassProtect', 185000, 20,
     'AJAX-GP', 'Ajax',
     'Detecta rotura de vidrio templado, laminado y blindado. Sensibilidad ajustable digital, sirena interna, 5 años de batería.'),
    ('alarmas-seguridad', 'sensores-vibracion', 'honeywell-is-3050',
     'Detector de Vibración Cableado Honeywell IS-3050', 120000, 18,
     'IS-3050', 'Honeywell',
     'Para cajas fuertes, puertas metálicas y muros. Ajuste por potenciómetro, salida NC sólida.'),
    ('alarmas-seguridad', 'sensores-vibracion', 'satel-vd-29',
     'Sensor Vibración Inalámbrico Satel VD-29', 165000, 15,
     'VD-29', 'Satel',
     'Para sistemas ABAX 2. Detección de vibraciones y movimientos de superficie, programación remota.'),

    # Sirenas internas
    ('alarmas-seguridad', 'sirenas-internas', 'ajax-homesiren',
     'Sirena Interior Ajax HomeSiren', 220000, 22,
     'AJAX-HOMESIREN', 'Ajax',
     'Sirena interior compacta 81 dB con notificaciones luminosas. Jeweller, alarma + retardo + timbre. Batería o fuente externa.'),
    ('alarmas-seguridad', 'sirenas-internas', 'dsc-wss-100',
     'Sirena Interior con Luz DSC WSS-100', 175000, 18,
     'WSS-100', 'DSC',
     'Sirena indoor inalámbrica 90 dB con flash LED. CR123A, montaje en pared. Para paneles DSC.'),
    ('alarmas-seguridad', 'sirenas-internas', 'ecos-piezo-120db',
     'Sirena Cableada Para Interior Ecos 5W 120 dB', 35000, 50,
     'ECOS-PIEZO-120', 'Ecos',
     'Piezoeléctrica 120 dB, 12 VDC, bajo consumo. Diodo LED de estado. Totalmente cableada.'),

    # Sirenas externas
    ('alarmas-seguridad', 'sirenas-externas', 'ajax-streetsiren',
     'Sirena Exterior Ajax StreetSiren', 380000, 14,
     'AJAX-STREETSIREN', 'Ajax',
     'Inalámbrica exterior 113 dB con flash. IP54, autoprotegida contra sabotaje. 4 años de batería, Jeweller.'),
    ('alarmas-seguridad', 'sirenas-externas', 'dsc-wss-200',
     'Sirena Exterior DSC WSS-200', 295000, 12,
     'WSS-200', 'DSC',
     'Exterior inalámbrica 90 dB con estroboscopio rojo y azul, intemperie. Compatible PowerSeries Neo, 4 años de batería.'),
    ('alarmas-seguridad', 'sirenas-externas', 'sirena-aluminio-12v',
     'Sirena Exterior Óptico-Acústica Cableada 12V', 95000, 25,
     'SIR-EXT-12V', 'Generic',
     'Aluminio anticorrosivo 120 dB, flash LED, 12 VDC con batería de respaldo opcional. Antisabotaje y tamper.'),

    # Controles remotos
    ('alarmas-seguridad', 'controles-remotos-alarma', 'ajax-keypad-plus',
     'Llavero Ajax SpaceControl', 95000, 35,
     'AJAX-SPACECTRL', 'Ajax',
     'Llavero 4 botones (armar, desarmar, parcial, pánico). LED de estado, Jeweller, alcance 1700 m.'),
    ('alarmas-seguridad', 'controles-remotos-alarma', 'dsc-ws4929',
     'Mando DSC WS4929', 75000, 30,
     'WS4929', 'DSC',
     'Control bidireccional 4 botones para PowerSeries. Confirmación de armado vía LED.'),
    ('alarmas-seguridad', 'controles-remotos-alarma', 'pgst-pst-rc05',
     'Mando PGST PST-RC05', 28000, 60,
     'PST-RC05', 'PGST',
     '4 botones (armar/desarmar/pánico/timbre). 433 MHz, compatible con centrales PGST y genéricas.'),

    # Teclados
    ('alarmas-seguridad', 'teclados-alarma', 'ajax-keypad-touchscreen',
     'Teclado Táctil Ajax KeyPad TouchScreen', 1450000, 6,
     'AJAX-KP-TOUCH', 'Ajax',
     'Pantalla IPS 4.3" táctil. Centro de control de toda la casa Ajax. Lector DESFire y PIN de coacción.'),
    ('alarmas-seguridad', 'teclados-alarma', 'dsc-hs2lcdwf',
     'Teclado DSC Neo HS2LCDWF', 480000, 10,
     'HS2LCDWF', 'DSC',
     'Inalámbrico LCD 2×16, hasta 1000 zonas particionadas. Transceptor PowerG, tamper.'),
    ('alarmas-seguridad', 'teclados-alarma', 'paradox-k32-plus',
     'Teclado Paradox K32+', 220000, 14,
     'K32-PLUS', 'Paradox',
     'LED 32 zonas con mapeo, iconos intuitivos, retroiluminación. Compatible serie SP/MG.'),

    # Módulos GSM/WiFi
    ('alarmas-seguridad', 'modulos-gsm-wifi', 'ajax-sim-4g-ya4g',
     'Módulo Ajax SIM 4G (YA-4G)', 320000, 12,
     'YA-4G', 'Ajax',
     'Expansión para Hub 2 Plus, 4G/LTE primario o respaldo. nano SIM, antena externa, conmutación automática.'),
    ('alarmas-seguridad', 'modulos-gsm-wifi', 'dsc-3g2080r',
     'Módulo GSM/GPRS DSC 3G2080R', 280000, 10,
     '3G2080R', 'DSC',
     'Comunicación celular para PowerSeries y Alexor. Contact ID y SMS, 2G/3G.'),
    ('alarmas-seguridad', 'modulos-gsm-wifi', 'ajax-wifibridge',
     'Módulo WiFi Ajax WifiBridge', 195000, 14,
     'AJAX-WIFIBRIDGE', 'Ajax',
     'Conecta hubs Ajax a WiFi en lugar de Ethernet. USB, configuración rápida.'),

    # Baterías de alarma
    ('alarmas-seguridad', 'baterias-alarma', 'agm-12v-7ah',
     'Batería Recargable 12V 7Ah AGM', 65000, 50,
     'AGM-12V-7AH', 'Generic',
     'Sellada de plomo-ácido AGM, estándar en paneles de alarma. Sin mantenimiento, 3-5 años de vida útil.'),
    ('alarmas-seguridad', 'baterias-alarma', 'panasonic-cr123a-2pk',
     'Batería Litio CR123A 3V Panasonic (Paquete 2)', 28000, 80,
     'CR123A-2PK', 'Panasonic',
     'Pilas de litio para sensores Ajax y similares. 1550 mAh, baja autodescarga.'),
    ('alarmas-seguridad', 'baterias-alarma', 'agm-12v-18ah',
     'Batería de Respaldo 12V 18Ah para Sirena Exterior', 195000, 18,
     'AGM-12V-18AH', 'Generic',
     'AGM 18 Ah para sirenas autónomas. Terminal Faston, horas de autonomía.'),

    # ─────────────────────── Control de Acceso ───────────────────────
    # Lectores biométricos
    ('control-acceso', 'lectores-biometricos', 'zkteco-sf400',
     'Lector Biométrico ZKTeco SF400', 450000, 12,
     'SF400', 'ZKTeco',
     '1500 huellas, 50 000 eventos. LCD 2.8", huella/tarjeta/PIN. Wiegand, TCP/IP, USB, timbre y reportes.'),
    ('control-acceso', 'lectores-biometricos', 'hikvision-ds-k1t341cmfw',
     'Lector Facial y Huella Hikvision DS-K1T341CMFW', 1850000, 6,
     'DS-K1T341CMFW', 'Hikvision',
     'Cámara dual facial (300 rostros), huella (3000) y MIFARE. 3.97" táctil, TCP/IP y WiFi, desbloqueo <0.2 s.'),
    ('control-acceso', 'lectores-biometricos', 'suprema-biolite-net',
     'Lector Multibiométrico Suprema BioLite Net', 1380000, 8,
     'BLN-OC', 'Suprema',
     'IP65 exterior, 5000 huellas, 200 000 registros. Detección de huella viva, PoE, RS-485 y Wiegand.'),

    # Lectores RFID
    ('control-acceso', 'lectores-rfid', 'hikvision-ds-k1801em',
     'Lector RFID Hikvision DS-K1801EM', 95000, 25,
     'DS-K1801EM', 'Hikvision',
     'Lector EM 125 kHz con Wiegand, 3-8 cm. LED y buzzer, IP65. Diseño elegante para marco o pared.'),
    ('control-acceso', 'lectores-rfid', 'dahua-asr1200a',
     'Lector RFID Mifare Dahua DHI-ASR1200A', 145000, 20,
     'DHI-ASR1200A', 'Dahua',
     'MIFARE Classic 13.56 MHz, Wiegand 26/34, hasta 5 cm. Tamper antisabotaje.'),
    ('control-acceso', 'lectores-rfid', 'zkteco-kr602l',
     'Lector RFID con Teclado ZKTeco KR602L', 175000, 18,
     'KR602L', 'ZKTeco',
     'Teclado retroiluminado + RFID 125 kHz/13.56 MHz. Tarjeta + PIN o combinación. Wiegand. IP66.'),

    # Controladores de acceso
    ('control-acceso', 'controladores-acceso', 'zkteco-atlas-200',
     'Controlador de Acceso ZKTeco Atlas 200', 850000, 9,
     'ATLAS-200', 'ZKTeco',
     'Multibiométrico para 1 puerta, huella (3000), tarjeta y PIN. TCP/IP y USB, 100 000 eventos. Software ZKBio CVSecurity.'),
    ('control-acceso', 'controladores-acceso', 'hikvision-ds-k2604',
     'Controlador IP 4 Puertas Hikvision DS-K2604', 1450000, 7,
     'DS-K2604', 'Hikvision',
     '4 lectores Wiegand, hasta 100 000 tarjetas y 300 000 eventos. TCP/IP y RS-485, iVMS-4200 / HikCentral. PoE+.'),
    ('control-acceso', 'controladores-acceso', 'essl-sa-05',
     'Controlador Sencillo de 1 Puerta ESSL SA-05', 145000, 16,
     'SA-05', 'ESSL',
     'Autónomo para tarjeta EM con teclado y pantalla. 2000 usuarios, salida de relé y puerta.'),

    # Tarjetas RFID
    ('control-acceso', 'tarjetas-rfid', 'tarjeta-em-125khz-10pk',
     'Tarjeta de Proximidad EM 125 kHz (Paquete 10)', 35000, 60,
     'EM-CARD-10PK', 'Generic',
     'Tarjetas ISO 0.8 mm con número serigrafiado. Compatible con lectores EM estándar.'),
    ('control-acceso', 'tarjetas-rfid', 'mifare-1k-zkteco',
     'Tarjeta Mifare Classic 1K 13.56 MHz ZKTeco', 5500, 200,
     'MIFARE-1K', 'ZKTeco',
     'NXP MF1S50, 1 KB, sectores y llaves. Compatible con la mayoría de lectores MIFARE.'),
    ('control-acceso', 'tarjetas-rfid', 'nxp-ntag216',
     'Tarjeta NFC NXP NTAG216', 8500, 150,
     'NTAG216', 'NXP',
     'NFC Forum tipo 2, 888 bytes. Integración con smartphones y sistemas modernos.'),

    # Tags / llaveros
    ('control-acceso', 'tags-llaveros', 'llavero-em-10pk',
     'Llavero RFID EM 125 kHz (Pack 10)', 35000, 70,
     'EM-KEYFOB-10', 'Generic',
     'Tag llavero ABS con argolla metálica. Código único de fábrica. Resistente al agua y golpes.'),
    ('control-acceso', 'tags-llaveros', 'llavero-mifare-1k',
     'Tag Llavero Mifare Classic 1K', 6500, 120,
     'MIF-KEYFOB', 'Generic',
     'Llavero ABS MIFARE 13.56 MHz, lectoescritura. Útil como monedero y acceso. Colores surtidos.'),
    ('control-acceso', 'tags-llaveros', 'pulsera-em-silicona',
     'Pulsera RFID de Silicona EM-Marin', 12000, 80,
     'EM-WRIST', 'EM-Marin',
     'Tag pulsera ajustable, ideal para gimnasios o piscinas, resistente al agua. Código único.'),

    # Cerraduras eléctricas
    ('control-acceso', 'cerraduras-electricas', 'yli-ym-280',
     'Cerradura Eléctrica de Embutir Yli YM-280', 220000, 14,
     'YM-280', 'Yli',
     '12V DC para puertas de madera, muelle regulable, cromado. Fail-safe/secure configurable. 1000 kg estática.'),
    ('control-acceso', 'cerraduras-electricas', 'fsh-500kg',
     'Cerradura de Sobreponer FSH 500 kg', 280000, 12,
     'FSH-500', 'FSH',
     'Electromecánica de sobreponer para puertas metálicas o madera. 12 VDC consumo bajo (300 mA), incluye contraplaca.'),
    ('control-acceso', 'cerraduras-electricas', 'cerradura-sensor-puerta',
     'Cerradura Eléctrica con Sensor de Puerta', 195000, 16,
     'LCK-DR-SENS', 'Generic',
     'Microswitch NC/NO de estado, montaje en marco, salida para confirmación de bloqueo.'),

    # Cerraduras magnéticas
    ('control-acceso', 'cerraduras-magneticas', 'shelo-sl-300s',
     'Electroimán 300 kg Shelo SL-300S', 195000, 18,
     'SL-300S', 'Shelo',
     '300 kg (660 lb) interior, 12V/24V DC, LED y protección electrónica. Incluye placa magnética.'),
    ('control-acceso', 'cerraduras-magneticas', 'zl-600',
     'Electroimán 600 kg Z&L ZL-600', 380000, 10,
     'ZL-600', 'Z&L',
     '600 kg de retención, aluminio anodizado. 12/24V dual, sensor de puerta, protección golpe de ariete.'),
    ('control-acceso', 'cerraduras-magneticas', 'electroiman-vidrio-300',
     'Electroimán de Marco para Puerta de Vidrio 300 kg', 285000, 12,
     'EM-GLASS-300', 'Generic',
     'Soporte tipo "L" incluido para vidrio. 300 kg, satinado. Para oficinas acristaladas.'),

    # Videoporteros
    ('control-acceso', 'videoporteros', 'hikvision-ds-kv6113-wpe1',
     'Videoportero IP Hikvision DS-KV6113-WPE1(C)', 980000, 9,
     'DS-KV6113-WPE1', 'Hikvision',
     'Placa con cámara 2MP gran angular y WiFi. Llamada a Hik-Connect o monitor. RFID integrado, PoE, IR nocturno.'),
    ('control-acceso', 'videoporteros', 'aiphone-gt-1c7',
     'Videoportero 2 Hilos Aiphone GT-1C7', 1450000, 6,
     'GT-1C7', 'Aiphone',
     '2 hilos, monitor 7" manos libres, apertura de puerta. Expandible a 8 monitores. Placa con cámara incluida.'),
    ('control-acceso', 'videoporteros', 'dahua-vto3221e-p',
     'Videoportero WiFi Empotrable Dahua VTO3221E-P', 1180000, 7,
     'VTO3221E-P', 'Dahua',
     'Placa con cámara 2MP, WiFi o RJ45. Teclas retroiluminadas. App iDMSS, IP65, IK08.'),

    # Citofonos
    ('control-acceso', 'citofonos', 'fermax-duox-4n',
     'Citofono Intercomunicador Fermax 4+N DUOX', 1280000, 8,
     'FERMAX-DUOX', 'Fermax',
     '4 hilos con placa antivandálica, videoteléfono 4.3" manos libres. Bus Duox sencillo, hasta 128 viviendas.'),
    ('control-acceso', 'citofonos', 'bticino-334000',
     'Citofono Analógico Bticino Kit 334000', 680000, 10,
     'BT-334000', 'Bticino',
     'Kit de portero electrónico 2 hilos, teléfono interior y placa de 1 botón. Sencillo en reformas.'),
    ('control-acceso', 'citofonos', 'dahua-vto2000a',
     'Citofono IP Dahua VTO2000A', 850000, 9,
     'VTO2000A', 'Dahua',
     'Adaptador para convertir citófono analógico en IP. Bidireccional, control remoto desde app.'),

    # Botones de salida
    ('control-acceso', 'botones-salida', 'boton-led-verde',
     'Botón de Salida de Sobreponer con LED Verde', 28000, 80,
     'BTN-EXIT-LED', 'Generic',
     'Contacto momentáneo NA con LED verde. Carcasa plástica, montaje en pared o caja.'),
    ('control-acceso', 'botones-salida', 'hikvision-ds-k7p02',
     'Botón de Salida Táctil Capacitivo Hikvision DS-K7P02', 95000, 30,
     'DS-K7P02', 'Hikvision',
     'Táctil retroiluminado, sin partes móviles, señalización acústica. IP66, NO/NC, temporizador ajustable.'),
    ('control-acceso', 'botones-salida', 'boton-emergencia-barra',
     'Botón de Salida de Emergencia a Barra', 220000, 14,
     'BTN-PANIC-BAR', 'Generic',
     'Barra antipánico de empuje con microswitch NO. Para puertas de emergencia con normativa.'),

    # ─────────────────────── Redes y Conectividad ───────────────────────
    # Routers
    ('redes-conectividad', 'routers', 'tplink-archer-ax55',
     'Router WiFi 6 AX3000 TP-Link Archer AX55', 320000, 18,
     'ARCHER-AX55', 'TP-Link',
     'Doble banda 3000 Mbps, WiFi 6 (802.11ax). 4 antenas, 4× Gigabit LAN, USB 3.0. OFDMA y MU-MIMO 4×4. HomeShield.'),
    ('redes-conectividad', 'routers', 'mikrotik-hex-s-rb760igs',
     'Router VPN Gigabit MikroTik hEX S RB760iGS', 285000, 12,
     'RB760IGS', 'MikroTik',
     '5 Gigabit Ethernet + SFP, PoE pasivo. RouterOS L4, IPsec/OpenVPN/WireGuard, firewall, QoS. Dual-core 880 MHz.'),
    ('redes-conectividad', 'routers', 'tplink-archer-mr600',
     'Router 4G LTE TP-Link Archer MR600', 380000, 14,
     'ARCHER-MR600', 'TP-Link',
     'AC1200 con SIM 4G+ Cat6 (300 Mbps). Modo router 4G o WAN respaldo. 4 LAN Gigabit, 2 antenas LTE.'),

    # Switches
    ('redes-conectividad', 'switches', 'tplink-tl-sg108',
     'Switch Gigabit 8 Puertos No Administrable TP-Link TL-SG108', 95000, 30,
     'TL-SG108', 'TP-Link',
     '8 puertos Gigabit, carcasa metálica, sin ventilador. Plug & play, auto-negociación.'),
    ('redes-conectividad', 'switches', 'dahua-pfs3016-16et-135',
     'Switch PoE+ 16 Puertos 2 SFP Dahua PFS3016-16ET-135', 680000, 9,
     'PFS3016-16ET-135', 'Dahua',
     'Administrable 16 PoE 100M + 2 SFP Gigabit. 135 W PoE, VLAN, QoS, SNMP. Modo CCTV, montaje rack.'),
    ('redes-conectividad', 'switches', 'aruba-instant-on-1930',
     'Switch Capa 3 24 Puertos Aruba Instant On 1930', 1850000, 5,
     'JL682A', 'Aruba',
     'Gestionable 24 Gigabit + 4 SFP+ 10G. PoE+ 370W. Capa 3 estática, ACL, VLAN, gestión por app/nube.'),

    # Access Points
    ('redes-conectividad', 'access-points', 'ubiquiti-u6-lite',
     'AP WiFi 6 PoE Ubiquiti UniFi U6-Lite', 480000, 14,
     'U6-LITE', 'Ubiquiti',
     'Doble banda 1.5 Gbps. 300+ clientes. PoE 802.3af. Gestión UniFi Network Controller. MU-MIMO/OFDMA.'),
    ('redes-conectividad', 'access-points', 'engenius-ews850-ap',
     'AP de Exterior Engenius EWS850-AP', 850000, 8,
     'EWS850-AP', 'Engenius',
     'WiFi 6 exterior IP68, doble banda, 2×2 MU-MIMO, 1800 Mbps. PoE+ 802.3at, gestión ezMaster.'),
    ('redes-conectividad', 'access-points', 'tplink-deco-x50-poe',
     'AP Mesh TP-Link Deco X50-PoE', 580000, 10,
     'DECO-X50-POE', 'TP-Link',
     'Mesh mini con puerto PoE, WiFi 6 AX3000, roaming sin interrupciones. Modo router o AP.'),

    # Repetidores WiFi
    ('redes-conectividad', 'repetidores-wifi', 'tplink-re600xd',
     'Repetidor WiFi 6 TP-Link RE600XD', 220000, 16,
     'RE600XD', 'TP-Link',
     'Extensor doble banda AX1800 con Gigabit. OneMesh para roaming único, app Tether.'),
    ('redes-conectividad', 'repetidores-wifi', 'tenda-a18',
     'Repetidor WiFi AC1200 Tenda A18', 95000, 28,
     'TENDA-A18', 'Tenda',
     'Sobremesa con 2 antenas externas. WPS, modo AP, puerto Ethernet 10/100. Compacto.'),
    ('redes-conectividad', 'repetidores-wifi', 'devolo-magic2-wifi6',
     'Repetidor Powerline WiFi Devolo Magic 2 WiFi 6', 950000, 5,
     'DEVOLO-M2-W6', 'Devolo',
     'Powerline + Mesh WiFi 6 integrado. Hasta 2400 Mbps Powerline, 2 puertos Gigabit.'),

    # Cable UTP
    ('redes-conectividad', 'cable-utp', 'furukawa-cat6-305m',
     'Cable UTP Cat6 Bobina 305 m Furukawa F/UTP', 850000, 8,
     'FUR-CAT6-305', 'Furukawa',
     'Cobre sólido 23 AWG, cubierta LSZH. Cat6 250 MHz, 1000BASE-T. Etiquetado métrico.'),
    ('redes-conectividad', 'cable-utp', 'cat6a-exterior-sftp-305m',
     'Cable UTP Cat6a Exterior Blindado S/FTP 305 m', 1450000, 5,
     'CAT6A-EXT-305', 'Generic',
     'Cobre sólido S/FTP, cubierta PE negra resistente a UV. 500 MHz, 10 Gbps. Para tendidos exteriores.'),
    ('redes-conectividad', 'cable-utp', 'cat5e-cca-305m',
     'Cable UTP Cat5e Económico 305 m', 285000, 14,
     'CAT5E-CCA-305', 'Generic',
     'Cobre/aluminio (CCA), cubierta PVC. Soporta hasta 1000 Mbps. Para distancias cortas y presupuestos ajustados.'),

    # Patch cords
    ('redes-conectividad', 'patch-cords', 'furukawa-cat6-2m-azul',
     'Patch Cord Cat6 UTP 2 m Furukawa (Azul)', 18000, 100,
     'FUR-PC-CAT6-2M', 'Furukawa',
     'Conductores trenzados, RJ45 estándar. Botas con alivio de tensión.'),
    ('redes-conectividad', 'patch-cords', 'pc-cat6a-1m-stp',
     'Patch Cord Cat6A Blindado 1 m RJ45', 25000, 80,
     'PC-CAT6A-1M', 'Generic',
     'S/FTP snagless, blindado, 10G. Conectores para tierra, ideal rack y EMI.'),
    ('redes-conectividad', 'patch-cords', 'ugreen-cat7-3m-plano',
     'Patch Cord Plano Cat7 3 m Ugreen', 32000, 60,
     'UGREEN-CAT7-3M', 'Ugreen',
     'Plano ultra delgado, Cat7 con blindaje. 10 Gbps, 600 MHz. Para cableado visible o bajo alfombras.'),

    # Patch panels
    ('redes-conectividad', 'patch-panels', 'furukawa-cat6-24p',
     'Patch Panel Cat6 24 Puertos Furukawa', 380000, 12,
     'FUR-PP-24', 'Furukawa',
     '1U, 24 RJ45, K5 categoría 6. Manejo de cables y etiquetas. Bronce fosforoso.'),
    ('redes-conectividad', 'patch-panels', 'pp-cat6a-24p-stp',
     'Patch Panel Cat6A Blindado 24 Puertos', 580000, 8,
     'PP-CAT6A-24', 'Generic',
     '1U, 24 RJ45 blindados con conexión a tierra. 10G, entornos industriales.'),
    ('redes-conectividad', 'patch-panels', 'pp-modular-12-vacio',
     'Patch Panel Modular de 12 Puertos Vacío', 145000, 18,
     'PP-MOD-12', 'Generic',
     '0.5U sin keystones. Personalizar con módulos RJ45/coaxial/fibra/HDMI.'),

    # Rack
    ('redes-conectividad', 'rack-comunicaciones', 'rack-pared-6u-450',
     'Rack de Pared 6U 450 mm Profundidad Ventilado', 480000, 10,
     'RACK-W-6U-450', 'Generic',
     '6U desmontable, vidrio templado con llave, ventilación superior. Bandeja opcional.'),
    ('redes-conectividad', 'rack-comunicaciones', 'rack-piso-42u-600x800',
     'Rack de Piso 42U 600×800 mm', 1850000, 4,
     'RACK-F-42U', 'Generic',
     'Autoestable, acrílico frontal, perforado posterior, ruedas y patas niveladoras. 3 bandejas.'),
    ('redes-conectividad', 'rack-comunicaciones', 'rack-techo-12u-600x400',
     'Rack de Techo 12U 600×400 mm', 720000, 6,
     'RACK-C-12U', 'Generic',
     'Apertura trasera para techo, bandeja ventilada y soporte de cables. Carga 30 kg.'),

    # Conectores RJ45
    ('redes-conectividad', 'conectores-rj45', 'rj45-cat6-pass-through-50',
     'Conectores RJ45 Cat6 Pass Through Plug (50 uds)', 38000, 60,
     'RJ45-PT-50', 'Generic',
     'Pass-through para crimpado fácil, Cat6, 23-26 AWG. Contactos dorados de 3 puntas.'),
    ('redes-conectividad', 'conectores-rj45', 'rj45-cat6a-stp-30',
     'Conectores RJ45 Blindados Cat6A (30 uds)', 75000, 40,
     'RJ45-STP-30', 'Generic',
     'Metálicos con blindaje 360°, F/UTP o S/FTP, 10G. Botas anti-tensión.'),
    ('redes-conectividad', 'conectores-rj45', 'keystone-cat6-10pk',
     'Conectores RJ45 Keystone Cat6 Hembra-Hembra (10 uds)', 45000, 50,
     'KEYSTONE-10', 'Generic',
     'IDC en ambos extremos, dorados 50µ, Cat6. Para patch panels y tomas. Herramienta de impacto.'),

    # PoE
    ('redes-conectividad', 'poe', 'tplink-tl-poe160s',
     'Inyector PoE+ 30W 802.3at Gigabit TP-Link TL-PoE160S', 95000, 25,
     'TL-POE160S', 'TP-Link',
     'PoE/PoE+ 30W. Entrada y salida Gigabit, plug & play. Protección contra cortocircuitos.'),
    ('redes-conectividad', 'poe', 'splitter-poe-12v-2a-usbc',
     'Splitter PoE Activo 12V 2A con Puerto USB-C', 65000, 30,
     'SPL-POE-12V', 'Generic',
     'Toma PoE 802.3af/at, entrega 12V DC 2A + Gigabit. Aislación 1500V.'),
    ('redes-conectividad', 'poe', 'dahua-pfs3005-4et-60',
     'Switch PoE 5 Puertos 60W Dahua DH-PFS3005-4ET-60', 195000, 18,
     'PFS3005-4ET-60', 'Dahua',
     'No administrable 4 PoE 100M + 1 uplink. 60 W, modo CCTV.'),

    # ─────────────────────── Domótica / Smart Home ───────────────────────
    # Sensores inteligentes
    ('domotica-smart-home', 'sensores-inteligentes', 'aqara-multi-zigbee',
     'Sensor Multifunción Aqara 4 en 1 Zigbee 3.0', 95000, 30,
     'AQARA-MULTI', 'Aqara',
     'Apertura/cierre, lumínica, aceleración y vibración. Hub Aqara, HomeKit, Alexa, Google. CR1632 2 años.'),
    ('domotica-smart-home', 'sensores-inteligentes', 'philips-hue-outdoor-pir',
     'Sensor de Movimiento Philips Hue Outdoor', 285000, 14,
     'HUE-OUT-PIR', 'Philips',
     'PIR exterior Zigbee a puente Hue. 12 m, 160°, también temp y luminosidad. Notificaciones y escenas.'),
    ('domotica-smart-home', 'sensores-inteligentes', 'xiaomi-mi-water-leak',
     'Sensor de Inundación Xiaomi Mi Water Leak', 65000, 35,
     'XM-WLEAK', 'Xiaomi',
     'Disco con electrodos, Zigbee, alerta a app y sirena al detectar humedad. Mi Home.'),

    # Interruptores inteligentes
    ('domotica-smart-home', 'interruptores-inteligentes', 'sonoff-t0-1ch-eu',
     'Interruptor Inteligente WiFi Sonoff T0 EU 1 Canal', 95000, 28,
     'SONOFF-T0-1CH', 'Sonoff',
     'Cristal táctil WiFi 2.4 GHz, 1 luz. App eWeLink, Alexa y Google. Requiere neutro.'),
    ('domotica-smart-home', 'interruptores-inteligentes', 'aqara-doble-sin-neutro',
     'Interruptor Zigbee Aqara Doble Canal sin Neutro', 165000, 18,
     'AQ-D2-NN', 'Aqara',
     'Sin neutro, hasta 1100 W. Doble canal, requiere hub Aqara. HomeKit y voz.'),
    ('domotica-smart-home', 'interruptores-inteligentes', 'fibaro-fgs-223',
     'Módulo Interruptor Fibaro FGS-223 Doble Relé Z-Wave', 285000, 12,
     'FGS-223', 'Fibaro',
     'Detrás de interruptor convencional, 2 cargas 6.5 A. Asociación directa y autómatas.'),

    # Enchufes inteligentes
    ('domotica-smart-home', 'enchufes-inteligentes', 'tplink-tapo-p110',
     'Enchufe Inteligente WiFi TP-Link Tapo P110', 65000, 40,
     'TAPO-P110', 'TP-Link',
     'Medición de consumo en tiempo real, control remoto, programación. WiFi 2.4 GHz, Alexa y Google.'),
    ('domotica-smart-home', 'enchufes-inteligentes', 'aqara-sp-euc01',
     'Enchufe Zigbee Aqara Smart Plug SP-EUC01', 85000, 28,
     'SP-EUC01', 'Aqara',
     'Zigbee 3.0, monitorización de potencia. Requiere Hub Aqara. HomeKit, protección de sobrecarga.'),
    ('domotica-smart-home', 'enchufes-inteligentes', 'meross-mss620',
     'Enchufe Outdoor IP44 Meross MSS620', 145000, 18,
     'MSS620', 'Meross',
     'Doble exterior IP44, control independiente, cortinilla de seguridad. HomeKit/Alexa/Google.'),

    # Automatización por app
    ('domotica-smart-home', 'automatizacion-app', 'samsung-smartthings-station',
     'Hub Central SmartThings Station', 320000, 12,
     'STH-EHS', 'Samsung',
     'Multiprotocolo Zigbee/Z-Wave/Thread/Matter. App SmartThings con rutinas avanzadas. Cargador inalámbrico.'),
    ('domotica-smart-home', 'automatizacion-app', 'homey-bridge',
     'Aplicación/Autómata Homey Bridge', 480000, 8,
     'HOMEY-BRIDGE', 'Homey',
     'Unifica 50 000+ dispositivos. Zigbee, Z-Wave, WiFi, IR y RF 433. Flujos sin programar.'),
    ('domotica-smart-home', 'automatizacion-app', 'homey-pro-2023',
     'Servidor de Automatizaciones Homey Pro (Early 2023)', 1480000, 5,
     'HOMEY-PRO-23', 'Homey',
     'Procesamiento local potente, Matter, todos los protocolos. Suscripción nube opcional.'),

    # Automatización por voz
    ('domotica-smart-home', 'automatizacion-voz', 'amazon-echo-dot-5',
     'Altavoz Inteligente Amazon Echo Dot (5ta Gen)', 215000, 22,
     'ECHO-DOT-5', 'Amazon',
     'Alexa con sensor de temperatura, control por voz, integración masiva. WiFi dual, Bluetooth, LED reloj opcional.'),
    ('domotica-smart-home', 'automatizacion-voz', 'google-nest-hub-2',
     'Pantalla Inteligente Google Nest Hub (2da Gen)', 380000, 14,
     'NEST-HUB-2', 'Google',
     'Pantalla 7" con Google Assistant. Soporta Matter y Thread. Reproductor de cámaras de seguridad.'),
    ('domotica-smart-home', 'automatizacion-voz', 'athom-homey-voice',
     'Controlador de Voz Athom Homey Voice', 380000, 9,
     'HOMEY-VOICE', 'Athom',
     'Voz local en ecosistema Homey, comandos personalizados sin depender de la nube.'),

    # Integraciones smart home
    ('domotica-smart-home', 'integraciones-smart-home', 'hubitat-c-8',
     'Hubitat Elevation Model C-8', 750000, 8,
     'HE-C8', 'Hubitat',
     'Hub local Z-Wave 800, Zigbee 3.0, Matter y WiFi. Rule Machine, sin internet. Dashboard personalizable.'),
    ('domotica-smart-home', 'integraciones-smart-home', 'gira-x1-knx',
     'Controlador KNX/IP Gira X1', 4850000, 3,
     'GIRA-X1', 'Gira',
     'Servidor KNX profesional con app Gira Smart Home, Alexa/Google. Programación ETS.'),
    ('domotica-smart-home', 'integraciones-smart-home', 'sonoff-nspanel-pro',
     'Bridge Universal SONOFF NSPanel Pro', 980000, 6,
     'NSPANEL-PRO', 'Sonoff',
     'Panel táctil de pared con Zigbee 3.0 + WiFi + Ethernet. 3.9", widgets de cámara y eWeLink.'),

    # ─────────────────────── Energía y Respaldo ───────────────────────
    # UPS
    ('energia-respaldo', 'ups', 'apc-bx1500u',
     'UPS Interactivo APC Back-UPS 1500VA BX1500U', 850000, 12,
     'BX1500U', 'APC',
     '1500VA/900W, 8 NEMA (4 con respaldo). AVR, USB. Para oficina, NVR y router.'),
    ('energia-respaldo', 'ups', 'eaton-5e-2000va',
     'UPS Online Doble Conversión Eaton 5E 2000VA', 2480000, 5,
     '5E-2000VA', 'Eaton',
     '2000VA/1600W online (VFI), onda senoidal pura. LCD, baterías ampliables. Para servidores y CCTV crítico.'),
    ('energia-respaldo', 'ups', 'forza-fx-1500lcd',
     'UPS Compacto Forza FX-1500LCD', 580000, 14,
     'FX-1500LCD', 'Forza',
     'Interactivo 1500VA/900W, LCD, USB, 4 NEMA respaldadas. AVR, hasta 10 min a plena carga.'),

    # Reguladores
    ('energia-respaldo', 'reguladores-voltaje', 'apc-le1200i',
     'Regulador de Voltaje APC Line-R 1200VA LE1200I', 380000, 16,
     'LE1200I', 'APC',
     '1200VA con 4 salidas, protección sobretensión, subtensión y ruido. Sin batería.'),
    ('energia-respaldo', 'reguladores-voltaje', 'trv-2000va-pro',
     'Regulador Electrónico 2000VA TRV Professional', 480000, 12,
     'TRV-2000VA', 'TRV',
     'Automático 2000VA con 4 contactos, sobrecarga, retardo programable. Rango 90-280V.'),
    ('energia-respaldo', 'reguladores-voltaje', 'regulador-500va-camara',
     'Regulador de 500VA Para Cámaras Específico', 95000, 25,
     'REG-500VA', 'Generic',
     'De pared 500VA, 1 salida, picos y filtro EMI. Para cámara o videoportero remoto.'),

    # Fuentes de poder (energía)
    ('energia-respaldo', 'fuentes-poder', 'fuente-12v-20a-bateria',
     'Fuente Switching 12V 20A con Salida de Batería', 195000, 18,
     'PSU-12V-20A-BAT', 'Generic',
     'Conmutada 12V 20A con cargador y salida de respaldo. Indica fallo AC por contacto seco.'),
    ('energia-respaldo', 'fuentes-poder', 'fuente-24vac-5a-ptz',
     'Fuente 24VAC 5A Para PTZ', 145000, 20,
     'PSU-24VAC-5A', 'Generic',
     'Transformador AC 220/24V, 100VA, fusible térmico. Para PTZ que requiere 24VAC.'),
    ('energia-respaldo', 'fuentes-poder', 'poe-pasivo-24v-1a',
     'Módulo de Fuente PoE Pasiva 24V 1A (Inyector y Splitter)', 38000, 35,
     'POE-PAS-24V', 'Generic',
     'Alimentación 24V pasiva sobre UTP. Inyector + splitter con DC 2.1mm.'),

    # Baterías
    ('energia-respaldo', 'baterias', 'gel-12v-7ah-ups',
     'Batería de Gel 12V 7Ah para UPS/Alarma', 65000, 60,
     'GEL-12V-7AH', 'Generic',
     'AGM/Gel sellada 12V 7Ah, terminal Faston F1. Sin mantenimiento.'),
    ('energia-respaldo', 'baterias', 'lifepo4-12v-20ah',
     'Banco de Baterías Litio 12V 20Ah LiFePO4', 580000, 12,
     'LFP-12V-20AH', 'Generic',
     'LiFePO4 con BMS, 2000 ciclos profundos. Para solar o respaldo robusto.'),
    ('energia-respaldo', 'baterias', 'agm-12v-18ah-ups',
     'Batería 12V 18Ah Ciclo Profundo para UPS/Emergencia', 195000, 22,
     'AGM-12V-18AH-UPS', 'Generic',
     'AGM mayor capacidad, UPS gama media y respaldo de sirena. Terminal F2. 3-5 años.'),

    # Sistemas de respaldo
    ('energia-respaldo', 'sistemas-respaldo', 'ecoflow-river-2-pro',
     'Planta de Energía Portátil EcoFlow River 2 Pro', 1850000, 7,
     'RIVER-2-PRO', 'EcoFlow',
     '768 Wh, CA 800W (pico 1600W), USB, DC y carga rápida (70% en 1h). Panel solar opcional.'),
    ('energia-respaldo', 'sistemas-respaldo', 'mustek-1000va-ats',
     'Inversor Cargador 1000VA Mustek con Transferencia Automática', 580000, 9,
     'MUSTEK-1000VA', 'Mustek',
     'UPS con batería externa opcional 12V. 1000VA/600W, onda modificada, transferencia <10ms.'),
    ('energia-respaldo', 'sistemas-respaldo', 'kit-solar-100w-12v-50ah',
     'Sistema Solar de Respaldo 12V con Panel y Controlador', 980000, 5,
     'SOLAR-100W-12V', 'Generic',
     'Panel 100W + controlador MPPT + AGM 12V 50Ah. Para switch PoE y cámaras off-grid.'),
]


def main():
    if not CONTENT.exists():
        sys.exit(f'No existe {CONTENT}')

    created = 0
    overwritten = 0
    skipped_no_sub = 0

    for parent, sub, pslug, name, price, stock, sku, brand, desc in PRODUCTS:
        sub_dir = CONTENT / parent / sub
        if not sub_dir.is_dir():
            print(f'  [skip] no existe subcategoria: {parent}/{sub}')
            skipped_no_sub += 1
            continue

        prod_dir = sub_dir / 'productos' / pslug
        was_existing = prod_dir.exists()
        prod_dir.mkdir(parents=True, exist_ok=True)

        data = {
            'slug': pslug,
            'name': name,
            'price': price,
            'stock': stock,
            'sku': sku,
            'brand': brand,
            'description': desc,
            'images': [],
            'active': True,
        }
        (prod_dir / 'data.json').write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )
        if was_existing:
            overwritten += 1
        else:
            created += 1

    print(f'OK: {created} creados, {overwritten} sobrescritos, {skipped_no_sub} omitidos por subcategoria faltante')


if __name__ == '__main__':
    main()
