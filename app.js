/* Mindboarding: small, accessible JavaScript enhancements.
   The site still works without it (forms are normal HTML forms).
   1. Popovers (notifications, user menu)   2. Mobile menu drawer
   3. "Saving…" state on forms               4. Quiz builder (add / remove questions)
   5. Time-of-day greeting on the dashboard */
(function () {
  "use strict";

  /* ---------- 1. Popovers ---------- */
  var toggles = document.querySelectorAll("[data-popover-toggle]");

  function closePopover(toggle) {
    var panel = document.getElementById(toggle.getAttribute("data-popover-toggle"));
    if (panel) { panel.hidden = true; }
    toggle.setAttribute("aria-expanded", "false");
  }

  function closeAllPopovers(except) {
    toggles.forEach(function (toggle) { if (toggle !== except) { closePopover(toggle); } });
  }

  toggles.forEach(function (toggle) {
    toggle.addEventListener("click", function () {
      var panel = document.getElementById(toggle.getAttribute("data-popover-toggle"));
      if (!panel) { return; }
      var willOpen = panel.hidden;
      closeAllPopovers(toggle);
      panel.hidden = !willOpen;
      toggle.setAttribute("aria-expanded", String(willOpen));
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest(".popover-wrap")) { closeAllPopovers(null); }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") { return; }
    toggles.forEach(function (toggle) {
      if (toggle.getAttribute("aria-expanded") === "true") { closePopover(toggle); toggle.focus(); }
    });
  });

  /* ---------- 2. Mobile drawer ---------- */
  var sidebar = document.getElementById("sidebar");
  var scrim = document.querySelector("[data-drawer-scrim]");
  var drawerToggle = document.querySelector("[data-drawer-toggle]");
  var drawerClose = document.querySelector("[data-drawer-close]");

  function drawerFocusables() {
    return sidebar.querySelectorAll("a[href], button:not([disabled])");
  }

  function openDrawer() {
    sidebar.classList.add("is-open");
    scrim.hidden = false;
    drawerToggle.setAttribute("aria-expanded", "true");
    var items = drawerFocusables();
    if (items.length) { items[0].focus(); }
  }

  function closeDrawer(returnFocus) {
    sidebar.classList.remove("is-open");
    scrim.hidden = true;
    drawerToggle.setAttribute("aria-expanded", "false");
    if (returnFocus) { drawerToggle.focus(); }
  }

  if (sidebar && scrim && drawerToggle) {
    drawerToggle.addEventListener("click", openDrawer);
    scrim.addEventListener("click", function () { closeDrawer(true); });
    if (drawerClose) { drawerClose.addEventListener("click", function () { closeDrawer(true); }); }

    document.addEventListener("keydown", function (event) {
      if (!sidebar.classList.contains("is-open")) { return; }
      if (event.key === "Escape") { closeDrawer(true); return; }
      if (event.key === "Tab") {            // keep keyboard focus inside the open drawer
        var items = drawerFocusables();
        var first = items[0];
        var last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });

    window.matchMedia("(min-width: 901px)").addEventListener("change", function (query) {
      if (query.matches) { closeDrawer(false); }
    });
  }

  /* ---------- 3. Loading state on forms ---------- */
  document.querySelectorAll("form[data-loading-form]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "true") { event.preventDefault(); return; }  // block double submits
      form.dataset.submitting = "true";
      var button = form.querySelector("button[type=submit][data-loading-text]");
      if (button) {
        button.dataset.originalText = button.textContent;
        button.textContent = button.dataset.loadingText;
        button.classList.add("is-loading");
        button.setAttribute("aria-busy", "true");
      }
    });
  });

  // If the user comes back with the Back button, undo the "Saving…" state.
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) { return; }
    document.querySelectorAll("form[data-loading-form]").forEach(function (form) {
      form.dataset.submitting = "false";
      var button = form.querySelector("button[data-original-text]");
      if (button) {
        button.textContent = button.dataset.originalText;
        button.classList.remove("is-loading");
        button.removeAttribute("aria-busy");
      }
    });
  });

  /* ---------- 4. Quiz builder ---------- */
  var list = document.getElementById("question-list");
  var template = document.getElementById("question-template");
  var addButton = document.querySelector("[data-add-question]");

  function refreshQuestionList() {
    var blocks = list.querySelectorAll("[data-question-block]");
    blocks.forEach(function (block, position) {
      block.querySelector("[data-question-label]").textContent = "Question " + (position + 1);
      block.querySelector("[data-remove-question]").hidden = blocks.length === 1;
    });
    addButton.disabled = blocks.length >= Number(list.dataset.max);
  }

  if (list && template && addButton) {
    addButton.addEventListener("click", function () {
      var index = Number(list.dataset.nextIndex);
      list.dataset.nextIndex = String(index + 1);
      // The template uses __N__ as a placeholder for the question number in field names.
      list.insertAdjacentHTML("beforeend", template.innerHTML.split("__N__").join(String(index)));
      refreshQuestionList();
      var fresh = list.querySelector("[data-question-block]:last-child input[type=text]");
      if (fresh) { fresh.focus(); }
    });

    list.addEventListener("click", function (event) {
      var remove = event.target.closest("[data-remove-question]");
      if (!remove) { return; }
      remove.closest("[data-question-block]").remove();
      refreshQuestionList();
      addButton.focus();
    });

    refreshQuestionList();
  }

  /* ---------- 5. Time-of-day greeting ---------- */
  // The server does not know the visitor's time zone, so the browser picks the greeting.
  // Without JavaScript the page simply says "Hello".
  var greeting = document.querySelector("[data-greeting]");
  if (greeting) {
    var hour = new Date().getHours();
    greeting.textContent = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  }
})();
