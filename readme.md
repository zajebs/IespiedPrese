# 🛠️ IespiedPrese.lv Projekts

Sveicināti IespiedPrese.lv projektā! Šī ir Flask bāzēta tīmekļa lietotne, kas ļauj lietotājiem pārlūkot un lejupielādēt dažādas tēmas un spraudņus. Lietotne arī atbalsta lietotāju autentifikāciju, cron-jobus produktu un lietotāju atjaunināšanai, abonementu plānus, vēsturi u.c.

## 🚀 Instalācija

Lai palaistu šo projektu lokāli, seko šiem soļiem:

1. Klonē repozitoriju:  
   git clone https://github.com/zajebs/IespiedPrese.lv.git

2. Ieej projekta direktorijā:  
   cd iespiedprese

3. Izveido un aktivizē virtuālo vidi:  
   python -m venv venv  
   source venv/bin/activate  # MacOS/Linux  
   .\venv\Scripts\activate  # Windows

4. Instalē nepieciešamās atkarības:  
   pip install -r requirements.txt

5. Izveido .env failu projekta saknes direktorijā un pievienoj savus mainīgos:  
   COOKIE=[Lapas cepums]  
   HOST=[Pluginu un tēmu repozitorijs]  
   SITEMAP_URLS=[Repozitorija sitemapi, comma separated]  
   USER_AGENT=Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0 (vai kāds cits user agent)  
   STRIPE_KEY=[Stripe testa/live atslēga]  
   SECRET_KEY=[jebkāda atslēga/parole]  
   PORT=[80 vai 443]  
   DEBUG=[True vai False]
   DATABASE_URL=[postgres pilns links]  
   BUCKETEER_AWS_ACCESS_KEY_ID=  
   BUCKETEER_AWS_SECRET_ACCESS_KEY=  
   BUCKETEER_AWS_REGION=eu-west-1=  
   BUCKETEER_BUCKET_NAME=  
   CACHE_AGE=[dienas, piemēram 365]  
   GA_MEASUREMENT_ID=[Google ID no Analytics]  
   GA_CSS_PATH=[Klase, kurai obligāti jābūt, lai GTag ielādētos]  

7. Izmanto skriptus, lai iegūtu sākotnējos datus:  
   python cron_scripts\full_update.py  
   python cron_scripts\download_images.py

6. Palaid lietotni:  
   python iespiedprese.py

## 📜 Licence

Šis projekts ir licencēts saskaņā ar MIT licenci.

## 📞 Kontakti

Ja tev ir kādi jautājumi vai ieteikumi, lūdzu, sazinies ar mani pa e-pastu hello@rihards.dev. Vairāk kontakti atrodami https://rihards.dev

Priecīgu Wordpressingu! 😊
