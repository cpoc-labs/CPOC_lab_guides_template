/*
 * Builds a guide's PDF in the browser, on demand, from the rendered pages of
 * the site itself - no pre-built PDF file is fetched or linked.
 *
 * Any link with data-pdf-guide="<guide-dir>" (e.g. imm-ahv, unified-edge)
 * triggers it. Guide metadata and page order come from javascripts/guides.json,
 * which `python scripts/generate_pdfs.py --manifest` writes from mkdocs.yml.
 */
(function () {
  var LIBS = [
    "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"
  ];
  var PAGE_W = 612, PAGE_H = 792, MARGIN_TOP = 40, MARGIN_BOTTOM = 36;
  var baseUrl = document.currentScript.src.replace(/javascripts\/pdf-export\.js.*$/, "");
  var busy = false;

  var CSS =
    ".pdfx{width:720px;padding:0 24px;background:#fff;color:#1b1f24;font:11px/1.55 Arial,Helvetica,sans-serif}" +
    ".pdfx h1{font-size:20px;color:#0090b8;border-bottom:2px solid #00bceb;padding-bottom:6px;margin:0 0 16px}" +
    ".pdfx h2{font-size:15px;color:#0090b8;margin:22px 0 10px}" +
    ".pdfx h3{font-size:12.5px;margin:16px 0 8px}" +
    ".pdfx p{margin:0 0 10px}.pdfx ul,.pdfx ol{margin:0 0 12px;padding-left:22px}.pdfx li{margin-bottom:4px}" +
    ".pdfx table{border-collapse:collapse;width:100%;margin:0 0 16px;font-size:10px}" +
    ".pdfx th,.pdfx td{border:1px solid #c7d2db;padding:5px 8px;text-align:left;vertical-align:top}" +
    ".pdfx table,.pdfx thead,.pdfx tbody,.pdfx tr,.pdfx td{background:#fff;color:#1b1f24;box-shadow:none}" +
    ".pdfx th{background:#e6f7fc;color:#04263d}" +
    ".pdfx img{max-width:100%;display:block;margin:10px auto;border:1px solid #d7dee4}" +
    ".pdfx .admonition{border-left:4px solid #00bceb;background:#e6f7fc;padding:8px 12px;margin:0 0 14px}" +
    ".pdfx .admonition-title{font-weight:700;color:#0090b8;margin-bottom:4px}" +
    ".pdfx pre,.pdfx code{background:#f2f5f7;font:10px Consolas,monospace}.pdfx pre{padding:8px;white-space:pre-wrap}" +
    ".pdfx a{color:#0090b8;text-decoration:none}" +
    ".pdfx .toc-list{list-style:none;padding:0}.pdfx .toc-list li{padding:5px 0;border-bottom:1px solid #e3e8ec;font-size:11.5px}";

  function loadLibs() {
    return Promise.all(LIBS.map(function (src) {
      return new Promise(function (resolve, reject) {
        var s = document.createElement("script");
        s.src = src;
        s.onload = resolve;
        s.onerror = function () { reject(new Error("Could not load the PDF library")); };
        document.head.appendChild(s);
      });
    }));
  }

  function fetchOk(url, what) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("Could not load " + what + " (" + r.status + ")");
      return r;
    });
  }

  // Fetch one rendered page and return its cleaned article content.
  function loadSection(page, isIndex) {
    var pageUrl = baseUrl + page.url;
    return fetchOk(pageUrl, page.label).then(function (r) { return r.text(); }).then(function (text) {
      var doc = new DOMParser().parseFromString(text, "text/html");
      var article = doc.querySelector(".md-content__inner");
      if (!article) throw new Error("Page has no content: " + page.label);
      article.querySelectorAll(
        ".cpoc-cta, .cpoc-btn-row, .md-source-file, .headerlink, .md-content__button, nav, script"
      ).forEach(function (n) { n.remove(); });
      if (isIndex) { // the cover page already carries the title + subtitle
        var h1 = article.querySelector("h1");
        if (h1) h1.remove();
        var first = article.querySelector("p");
        if (first && /Customer Proof of Concept/i.test(first.textContent) && first.textContent.length < 80) first.remove();
      }
      article.querySelectorAll("a").forEach(function (a) { // links can't navigate inside a PDF
        a.replaceWith.apply(a, Array.prototype.slice.call(a.childNodes));
      });
      // Drop theme/site classes and inline styles so the live page's (possibly
      // dark) theme can't leak into the PDF; only the admonition look is kept.
      [article].concat(Array.prototype.slice.call(article.querySelectorAll("*"))).forEach(function (n) {
        var keep = Array.prototype.filter.call(n.classList, function (c) { return /^admonition(-title)?$/.test(c); });
        n.removeAttribute("class");
        n.removeAttribute("style");
        keep.forEach(function (c) { n.classList.add(c); });
      });
      article.querySelectorAll("img").forEach(function (img) {
        img.removeAttribute("loading");
        img.setAttribute("src", new URL(img.getAttribute("src"), pageUrl).href);
      });
      var section = document.createElement("div");
      section.className = "pdfx";
      section.appendChild(document.importNode(article, true));
      return section;
    });
  }

  function whenImagesLoaded(el) {
    return Promise.all(Array.prototype.map.call(el.querySelectorAll("img"), function (img) {
      return img.complete ? null : new Promise(function (res) { img.onload = img.onerror = res; });
    }));
  }

  function drawCover(pdf, g) {
    var w = pdf.internal.pageSize.getWidth(), h = pdf.internal.pageSize.getHeight();
    pdf.setFillColor(10, 25, 41); pdf.rect(0, 0, w, h, "F");
    pdf.setTextColor(127, 231, 255); pdf.setFontSize(10); pdf.text("CISCO CONFIDENTIAL", 48, 56);
    pdf.setFillColor(0, 188, 235); pdf.rect(48, h / 2 - 70, 80, 5, "F");
    pdf.setTextColor(169, 192, 211); pdf.setFontSize(10);
    pdf.text("CISCO GLOBAL DEMO ENGINEERING · CUSTOMER PROOF OF CONCEPT", 48, h / 2 - 40);
    pdf.setTextColor(255, 255, 255); pdf.setFontSize(28);
    pdf.text(pdf.splitTextToSize(g.title, w - 96), 48, h / 2);
    pdf.setTextColor(127, 231, 255); pdf.setFontSize(16); pdf.text(g.subtitle, 48, h / 2 + 34);
    pdf.setTextColor(169, 192, 211); pdf.setFontSize(11);
    pdf.text(g.date, 48, h - 100);
    pdf.setTextColor(232, 241, 248); pdf.text(g.author, 48, h - 84);
    pdf.setTextColor(169, 192, 211); pdf.text(g.email, 48, h - 68);
  }

  function addHeaderFooter(pdf) {
    var w = pdf.internal.pageSize.getWidth(), h = pdf.internal.pageSize.getHeight();
    for (var i = 2; i <= pdf.getNumberOfPages(); i++) { // page 1 is the cover
      pdf.setPage(i); pdf.setFontSize(8); pdf.setTextColor(122, 136, 148);
      pdf.text("Cisco Global Demo Engineering Customer Proof of Concept", w / 2, 24, { align: "center" });
      pdf.text("Cisco © 2025. All Rights Reserved.   " + (i - 1), w / 2, h - 18, { align: "center" });
    }
  }

  // Draw one part onto as many new pages as it needs. Page breaks fall between
  // top-level blocks (paragraph, image, table...) so none is cut in half unless
  // it is taller than a page by itself.
  function renderPart(pdf, part) {
    var cssW = part.offsetWidth, cssH = part.offsetHeight;
    var ptPerPx = PAGE_W / cssW;
    var pageCssH = (PAGE_H - MARGIN_TOP - MARGIN_BOTTOM) / ptPerPx;
    var top = part.getBoundingClientRect().top;
    var root = part.children.length === 1 && part.firstElementChild.tagName === "ARTICLE" ? part.firstElementChild : part;
    var breaks = [0], start = 0;
    Array.prototype.forEach.call(root.children, function (el) {
      var r = el.getBoundingClientRect();
      var y0 = r.top - top, y1 = r.bottom - top;
      if (y1 - start > pageCssH && y0 > start && r.height <= pageCssH) { breaks.push(y0); start = y0; }
      while (y1 - start > pageCssH) { start += pageCssH; breaks.push(start); }
    });
    breaks.push(cssH);
    var scale = Math.min(1.5, 28000 / cssH);
    return window.html2canvas(part, { scale: scale, useCORS: true, logging: false, backgroundColor: "#ffffff" })
      .then(function (canvas) {
        for (var i = 0; i < breaks.length - 1; i++) {
          var sy = Math.round(breaks[i] * scale), sh = Math.round((breaks[i + 1] - breaks[i]) * scale);
          if (sh < 2) continue;
          var slice = document.createElement("canvas");
          slice.width = canvas.width; slice.height = sh;
          slice.getContext("2d").drawImage(canvas, 0, sy, canvas.width, sh, 0, 0, canvas.width, sh);
          pdf.addPage();
          pdf.addImage(slice.toDataURL("image/jpeg", 0.85), "JPEG", 0, MARGIN_TOP, PAGE_W, (sh / scale) * ptPerPx);
        }
      });
  }

  function generate(guideDir, progress) {
    var holder, style;
    return fetchOk(baseUrl + "javascripts/guides.json", "guide manifest").then(function (r) { return r.json(); })
      .then(function (manifest) {
        var g = manifest[guideDir];
        if (!g) throw new Error("Unknown guide: " + guideDir);
        progress("Loading pages…");
        return Promise.all([
          (window.jspdf && window.html2canvas ? Promise.resolve() : loadLibs()),
          Promise.all(g.pages.map(function (p) { return loadSection(p, p.url === guideDir + "/"); }))
        ]).then(function (res) { return { g: g, sections: res[1] }; });
      })
      .then(function (ctx) {
        style = document.createElement("style");
        style.textContent = CSS;
        document.head.appendChild(style);
        holder = document.createElement("div");
        holder.style.cssText = "position:fixed;left:-10000px;top:0;";
        document.body.appendChild(holder);

        var toc = document.createElement("div");
        toc.className = "pdfx";
        var h = document.createElement("h1");
        h.textContent = "Contents";
        var ul = document.createElement("ul");
        ul.className = "toc-list";
        ctx.g.pages.forEach(function (p) {
          var li = document.createElement("li");
          li.textContent = p.label;
          ul.appendChild(li);
        });
        toc.appendChild(h);
        toc.appendChild(ul);
        var parts = [toc].concat(ctx.sections);
        parts.forEach(function (p) { holder.appendChild(p); });

        var pdf = new window.jspdf.jsPDF({ unit: "pt", format: "letter", orientation: "portrait" });
        pdf.deletePage(1);
        var chain = Promise.resolve();
        parts.forEach(function (part, idx) {
          chain = chain.then(function () {
            progress("Rendering " + (idx + 1) + "/" + parts.length + "…");
            return whenImagesLoaded(part);
          }).then(function () {
            return renderPart(pdf, part);
          });
        });
        return chain.then(function () {
          pdf.insertPage(1);
          pdf.setPage(1);
          drawCover(pdf, ctx.g);
          addHeaderFooter(pdf);
          pdf.save(ctx.g.pdf_name);
        });
      })
      .finally(function () {
        if (holder) holder.remove();
        if (style) style.remove();
      });
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-pdf-guide]");
    if (!a) return;
    e.preventDefault();
    if (busy) return;
    busy = true;
    var label = a.textContent;
    generate(a.getAttribute("data-pdf-guide"), function (t) { a.textContent = t; })
      .then(function () { a.textContent = label; })
      .catch(function (err) { console.error(err); a.textContent = "PDF failed - click to retry"; })
      .finally(function () { busy = false; });
  });
})();
