(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  $$("[data-nav-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () { $(".dash").classList.toggle("nav-open"); });
  });
  document.addEventListener("click", function (e) {
    var dash = $(".dash.nav-open");
    if (dash && !e.target.closest(".sidebar") && !e.target.closest("[data-nav-toggle]")) dash.classList.remove("nav-open");
  });

  $$("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (e) { if (!window.confirm(f.dataset.confirm)) e.preventDefault(); });
  });

  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var src = document.getElementById(btn.dataset.copy);
      var text = src.value || src.textContent;
      var done = function () {
        var old = btn.innerHTML;
        btn.textContent = "کپی شد ✓";
        setTimeout(function () { btn.innerHTML = old; }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done);
      } else {
        src.select && src.select();
        document.execCommand("copy");
        done();
      }
    });
  });

  $$(".upload input[type=file]").forEach(function (input) {
    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      var box = input.closest(".upload").querySelector(".preview");
      if (!file || !box) return;
      var url = URL.createObjectURL(file);
      box.innerHTML = "";
      var img = new Image();
      img.src = url;
      box.appendChild(img);
    });
  });

  $$(".toasts .alert").forEach(function (el, i) {
    setTimeout(function () { el.style.transition = "opacity .4s"; el.style.opacity = "0"; }, 4200 + i * 400);
    setTimeout(function () { el.remove(); }, 4700 + i * 400);
  });

  var modal = $("#product-modal");
  if (modal) {
    var open = function (card) {
      var d = card.dataset;
      $("#m-name", modal).textContent = d.name;
      $("#m-brand", modal).textContent = d.brand || "";
      $("#m-brand", modal).classList.toggle("hidden", !d.brand);
      $("#m-desc", modal).textContent = d.desc || "";
      $("#m-cat", modal).textContent = d.cat || "";
      $("#m-cat", modal).classList.toggle("hidden", !d.cat);
      $("#m-av", modal).classList.toggle("hidden", d.available === "1");
      var box = $(".m-img", modal);
      box.innerHTML = "";
      box.classList.toggle("hidden", !d.img);
      if (d.img) { var img = new Image(); img.src = d.img; img.alt = d.name; box.appendChild(img); }
      modal.classList.add("open");
      document.body.style.overflow = "hidden";
    };
    var close = function () { modal.classList.remove("open"); document.body.style.overflow = ""; };
    $$(".product").forEach(function (c) { c.addEventListener("click", function () { open(c); }); });
    modal.addEventListener("click", function (e) { if (e.target === modal || e.target.closest(".modal-close")) close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  var chips = $$(".cat-bar .chip[data-target]");
  if (chips.length) {
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var sec = document.getElementById(chip.dataset.target);
        if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
    var sections = chips.map(function (c) { return document.getElementById(c.dataset.target); }).filter(Boolean);
    var onScroll = function () {
      var current = sections[0];
      sections.forEach(function (s) { if (s.getBoundingClientRect().top < 200) current = s; });
      chips.forEach(function (c) {
        var on = current && c.dataset.target === current.id;
        if (on && !c.classList.contains("active")) c.scrollIntoView({ block: "nearest", inline: "center" });
        c.classList.toggle("active", on);
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  var search = $("#catalog-search");
  if (search) {
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase();
      $$(".cat-section").forEach(function (sec) {
        var visible = 0;
        $$(".product", sec).forEach(function (p) {
          var hit = !q || (p.dataset.name + " " + (p.dataset.brand || "")).toLowerCase().indexOf(q) !== -1;
          p.classList.toggle("hidden", !hit);
          if (hit) visible++;
        });
        sec.classList.toggle("hidden", visible === 0);
      });
      var empty = $("#catalog-empty");
      if (empty) empty.classList.toggle("hidden", $$(".cat-section:not(.hidden)").length > 0);
    });
  }
})();
