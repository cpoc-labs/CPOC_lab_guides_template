(function () {
  var AUTH_KEY = "cpoc_authenticated";

  // Derive the site's base URL from this script's own resolved <script src>,
  // so this works unchanged under any subpath (GitHub Pages project page,
  // custom domain, or local `mkdocs serve`).
  var scriptSrc = document.currentScript.src;
  var baseUrl = scriptSrc.replace(/javascripts\/auth-gate\.js.*$/, "");
  var loginUrl = baseUrl + "login/";

  var params = new URLSearchParams(window.location.search);
  if (params.get("logout") === "1") {
    localStorage.removeItem(AUTH_KEY);
  }

  var onLoginPage = window.location.href.indexOf(loginUrl) === 0;
  var authenticated = localStorage.getItem(AUTH_KEY) === "1";

  if (!onLoginPage && !authenticated) {
    var next = encodeURIComponent(window.location.href);
    window.location.replace(loginUrl + "?next=" + next);
    return;
  }

  if (!onLoginPage && authenticated) {
    document.addEventListener("DOMContentLoaded", function () {
      var container = document.querySelector(".md-footer-meta__inner");
      if (!container) return;
      var link = document.createElement("a");
      link.href = loginUrl + "?logout=1";
      link.textContent = "Log out";
      link.style.color = "inherit";
      link.style.marginLeft = "1rem";
      container.appendChild(link);
    });
  }
})();
