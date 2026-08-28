# AutoID Professional Solutions v0.7.0

- Navigare comercială built-in: meniul WordPress livrează obiect/ID și aplicația rutează intern categorii, produse, pagini, coș, cont și suport.
- Variante: exclusiv relația WooCommerce Grouped Product -> children; când se deschide un child se identifică grouped parent-ul și se folosesc SKU-urile sibling reale.
- Grouped products: interval de preț calculat din child SKU-uri, ex. TVA și incl. TVA.
- Accesorii / Service / Software & Apps / Consumabile: produse publicate care împart `product_tag` cu grouped parent / produsul curent, apoi clasificate pe categoria produsului.
- Taburile goale nu sunt afișate.
- Brand: `product_brands` este taxonomia canonică, cu fallback-uri pentru compatibilitate.
- Prețurile MSRP / AutoID au aceeași dimensiune și în cards.
- Stoc AutoID + stoc distribuție apar împreună când ambele există.
- AI: adapter dedicat AutoID Support Center, cu detecția pluginului și a handlerelor sale REST/AJAX/hook; UI-ul AI rămâne Compose nativ.
- Resursele de suport nu mai deschid browserul extern din Product Hub.
