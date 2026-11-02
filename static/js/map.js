(function () {
  "use strict";
  if (typeof L === "undefined") return;

  // آیکون پیش‌فرض Leaflet را به فایل‌های محلی وصل می‌کنیم (بدون اتصال به سرورهای خارجی)
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: window.LEAFLET_IMG_BASE + "marker-icon-2x.png",
    iconUrl: window.LEAFLET_IMG_BASE + "marker-icon.png",
    shadowUrl: window.LEAFLET_IMG_BASE + "marker-shadow.png",
  });

  function addTiles(map) {
    L.tileLayer(window.MAP_TILE_URL, { attribution: window.MAP_TILE_ATTRIBUTION, maxZoom: 19 }).addTo(map);
  }

  // ---------- انتخابگر موقعیت (پنل فروشگاه / پنل اصلی) ----------
  var picker = document.getElementById("map-picker");
  if (picker) {
    var latInput = document.getElementById(picker.dataset.lat);
    var lngInput = document.getElementById(picker.dataset.lng);
    var hasInitial = latInput.value && lngInput.value;
    var start = hasInitial
      ? [parseFloat(latInput.value), parseFloat(lngInput.value)]
      : [window.MAP_DEFAULT_LAT, window.MAP_DEFAULT_LNG];

    var map = L.map(picker).setView(start, hasInitial ? 15 : 11);
    addTiles(map);
    var marker = L.marker(start, { draggable: true }).addTo(map);

    function setPoint(lat, lng) {
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
      var box = document.getElementById("map-coords");
      if (box) box.textContent = lat.toFixed(6) + ", " + lng.toFixed(6);
    }
    if (hasInitial) setPoint(start[0], start[1]);

    marker.on("dragend", function () {
      var p = marker.getLatLng();
      setPoint(p.lat, p.lng);
    });
    map.on("click", function (e) {
      marker.setLatLng(e.latlng);
      setPoint(e.latlng.lat, e.latlng.lng);
    });

    var locateBtn = document.getElementById("map-locate-btn");
    if (locateBtn && navigator.geolocation) {
      locateBtn.addEventListener("click", function () {
        locateBtn.disabled = true;
        navigator.geolocation.getCurrentPosition(
          function (pos) {
            var ll = [pos.coords.latitude, pos.coords.longitude];
            map.setView(ll, 16);
            marker.setLatLng(ll);
            setPoint(ll[0], ll[1]);
            locateBtn.disabled = false;
          },
          function () {
            window.alert("دسترسی به موقعیت مکانی ممکن نشد. روی نقشه کلیک کنید یا پین را جابه‌جا کنید.");
            locateBtn.disabled = false;
          }
        );
      });
    }
  }

  // ---------- نقشهٔ یک فروشگاه در صفحه عمومی آن ----------
  var single = document.getElementById("shop-map");
  if (single) {
    var lat = parseFloat(single.dataset.lat);
    var lng = parseFloat(single.dataset.lng);
    var smap = L.map(single, { scrollWheelZoom: false }).setView([lat, lng], 16);
    addTiles(smap);
    L.marker([lat, lng]).addTo(smap).bindPopup(single.dataset.name || "");
  }

  // ---------- نقشهٔ کلی همهٔ پت‌شاپ‌ها ----------
  var full = document.getElementById("shops-map");
  if (full) {
    var fmap = L.map(full).setView([window.MAP_DEFAULT_LAT, window.MAP_DEFAULT_LNG], 11);
    addTiles(fmap);
    var markers = L.layerGroup().addTo(fmap);
    var allPoints = [];
    var shopIcon = L.divIcon({
      className: "shop-marker",
      html: '<span class="shop-marker-pin"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9 4.5 4h15L21 9a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0ZM5 11.5V20h14v-8.5M10 20v-5h4v5"/></svg></span>',
      iconSize: [38, 46],
      iconAnchor: [19, 44],
      popupAnchor: [0, -40]
    });

    function renderShops(shops) {
      markers.clearLayers();
      allPoints = [];
      shops.forEach(function (s) {
        var m = L.marker([s.lat, s.lng], { icon: shopIcon }).addTo(markers);
        var logoHtml = s.logo
          ? '<img class="logo" src="' + s.logo + '" alt="">'
          : '<div class="ph" style="background:' + (s.theme_color || "#0d9488") + '">' + (s.name ? s.name.charAt(0) : "پ") + "</div>";
        var popupHtml =
          '<div class="map-popup">' +
          logoHtml +
          "<h4>" + s.name + "</h4>" +
          (s.city ? '<div class="muted small">' + s.city + "</div>" : "") +
          '<a class="btn btn-sm" href="' + s.url + '">مشاهده کاتالوگ</a>' +
          "</div>";
        m.bindPopup(popupHtml);
        allPoints.push([s.lat, s.lng]);
      });
      if (allPoints.length) fmap.fitBounds(allPoints, { padding: [30, 30], maxZoom: 14 });
    }

    fetch(full.dataset.src)
      .then(function (r) { return r.json(); })
      .then(function (data) { renderShops(data.shops || []); })
      .catch(function () {});

    var nearBtn = document.getElementById("near-me-btn");
    if (nearBtn && navigator.geolocation) {
      nearBtn.addEventListener("click", function () {
        nearBtn.disabled = true;
        navigator.geolocation.getCurrentPosition(
          function (pos) {
            var me = [pos.coords.latitude, pos.coords.longitude];
            L.marker(me, { icon: L.divIcon({ className: "me-dot", html: "", iconSize: [16, 16] }) }).addTo(fmap);
            fmap.setView(me, 14);
            nearBtn.disabled = false;
          },
          function () {
            window.alert("دسترسی به موقعیت مکانی ممکن نشد.");
            nearBtn.disabled = false;
          }
        );
      });
    }
  }
})();
