/**
 * IEEE UP — comportamiento del sitio.
 *
 * Reemplaza tambien lo poco util que hacia `scripts.js` del tema 2019 (menu
 * movil y "volver arriba"); el resto de aquel archivo manejaba un buscador,
 * un carrusel y unos iconos sociales que este sitio no tiene.
 *
 * Responsabilidades:
 *   1. Menu movil (panel deslizante + backdrop + Escape + foco)
 *   2. Popups de evento (<dialog>)
 *   2b. Visor de fotos / lightbox (<dialog>), abierto desde el popup
 *   3. Carrusel de eventos en portada (slick)
 *   4. Revelado al hacer scroll
 *   5. Boton "volver arriba"
 */
(function () {
  "use strict";

  var prefiereMenosMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --- 1. Menu movil ------------------------------------------------------
  var nav = document.getElementById("main-nav");
  var backdrop = document.querySelector(".nav-backdrop");
  var abrirNav = document.querySelector("[data-abre-nav]");

  function cerrarNav() {
    if (!nav) return;
    nav.classList.remove("abierto");
    if (backdrop) backdrop.classList.remove("visible");
    document.body.style.overflow = "";
    if (abrirNav) {
      abrirNav.setAttribute("aria-expanded", "false");
      abrirNav.focus();
    }
  }

  if (abrirNav && nav) {
    abrirNav.addEventListener("click", function () {
      nav.classList.add("abierto");
      if (backdrop) backdrop.classList.add("visible");
      document.body.style.overflow = "hidden";
      abrirNav.setAttribute("aria-expanded", "true");
      var primero = nav.querySelector("a, button");
      if (primero) primero.focus();
    });
  }
  document.querySelectorAll("[data-cierra-nav]").forEach(function (el) {
    el.addEventListener("click", cerrarNav);
  });

  // --- 2. Popups de evento ------------------------------------------------
  document.querySelectorAll("[data-abre-modal]").forEach(function (boton) {
    var dialogo = document.getElementById(boton.dataset.abreModal);
    if (!dialogo) return;
    boton.addEventListener("click", function () {
      dialogo.showModal();
    });
  });

  // Enlace directo a un popup: pagina.html#modal-<slug>
  if (location.hash.indexOf("#modal-") === 0) {
    var destino = document.getElementById(location.hash.slice(1));
    if (destino && destino.tagName === "DIALOG") destino.showModal();
  }

  // Cerrar un <dialog> al hacer clic en su backdrop (fuera de `marco`) o en
  // su boton [data-cierra-modal]. La usan tanto el popup de evento como el
  // visor de fotos: cada uno pasa el selector de su propio contenido para
  // distinguir "clic dentro" de "clic fuera".
  function cerrarAlClicFuera(dialogo, selectorMarco) {
    dialogo.addEventListener("click", function (evento) {
      var marco = dialogo.querySelector(selectorMarco);
      if (marco && !marco.contains(evento.target)) dialogo.close();
    });
    var cerrar = dialogo.querySelector("[data-cierra-modal]");
    if (cerrar) cerrar.addEventListener("click", function () { dialogo.close(); });
  }

  document.querySelectorAll("dialog.evento-modal").forEach(function (dialogo) {
    cerrarAlClicFuera(dialogo, ".evento-modal__grid");
  });

  // --- 2b. Visor de fotos (lightbox) ---------------------------------------
  // Se abre desde la portada del popup o desde cualquier miniatura de su
  // galeria: antes esas miniaturas eran <a target="_blank"> que mandaban la
  // foto suelta a otra pestaña del navegador. Ahora la imagen se agranda en
  // la misma pagina y, si el evento tiene mas de una foto, se recorre como
  // carrusel con flechas, contador y las teclas de dirección.
  document.querySelectorAll("dialog.lightbox").forEach(function (visor) {
    var items = Array.prototype.slice.call(visor.querySelectorAll(".lightbox__item"));
    var contador = visor.querySelector("[data-lightbox-actual]");
    var indice = 0;

    function mostrar(i) {
      if (!items.length) return;
      indice = (i % items.length + items.length) % items.length;
      items.forEach(function (item, n) {
        item.classList.toggle("lightbox__item--activo", n === indice);
      });
      if (contador) contador.textContent = String(indice + 1);
    }

    visor.querySelectorAll("[data-lightbox-prev]").forEach(function (b) {
      b.addEventListener("click", function () { mostrar(indice - 1); });
    });
    visor.querySelectorAll("[data-lightbox-next]").forEach(function (b) {
      b.addEventListener("click", function () { mostrar(indice + 1); });
    });
    visor.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") mostrar(indice - 1);
      if (e.key === "ArrowRight") mostrar(indice + 1);
    });

    // El <dialog> ocupa toda la pantalla (100vw/100vh), asi que no hay
    // backdrop visible sobre el que hacer clic para cerrar: "afuera" aqui es
    // el padding oscuro alrededor de la foto (el propio .lightbox__item,
    // que con flexbox cubre ese espacio), no la <img> ni los botones. Por
    // eso NO se reutiliza cerrarAlClicFuera(): sus flechas y su boton de
    // cerrar son hermanos de .lightbox__lienzo en el marcado, y un cierre
    // basado en "contains" los habria tratado como clic afuera.
    items.forEach(function (item) {
      item.addEventListener("click", function (e) {
        if (e.target === item) visor.close();
      });
    });
    var cerrar = visor.querySelector("[data-cierra-modal]");
    if (cerrar) cerrar.addEventListener("click", function () { visor.close(); });

    visor._mostrarFoto = mostrar;
  });

  document.querySelectorAll("[data-abre-lightbox]").forEach(function (boton) {
    var visor = document.getElementById(boton.dataset.abreLightbox);
    if (!visor) return;
    boton.addEventListener("click", function () {
      var i = parseInt(boton.dataset.lightboxIndice, 10) || 0;
      if (visor._mostrarFoto) visor._mostrarFoto(i);
      visor.showModal();
    });
  });

  // Escape cierra el menu movil (los <dialog> ya lo hacen de forma nativa).
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && nav && nav.classList.contains("abierto")) cerrarNav();
  });

  // --- 3. Carrusel de eventos (portada) ------------------------------------
  if (typeof jQuery !== "undefined" && jQuery.fn.slick) {
    var $carrusel = jQuery(".eventos-carrusel");
    if ($carrusel.length) {
      $carrusel.slick({
        slidesToShow: 3,
        slidesToScroll: 1,
        infinite: true,
        autoplay: !prefiereMenosMovimiento,
        autoplaySpeed: 5000,
        pauseOnHover: true,
        speed: 550,
        cssEase: "cubic-bezier(.2,.7,.3,1)",
        dots: false,
        prevArrow: '<button type="button" class="slick-prev"><i class="fa fa-chevron-left" aria-hidden="true"></i><span class="screen-reader-text">Anterior</span></button>',
        nextArrow: '<button type="button" class="slick-next"><i class="fa fa-chevron-right" aria-hidden="true"></i><span class="screen-reader-text">Siguiente</span></button>',
        responsive: [
          { breakpoint: 1100, settings: { slidesToShow: 2 } },
          { breakpoint: 700, settings: { slidesToShow: 1 } }
        ]
      });
    }
  }

  // --- 3b. Fondo variable del hero -----------------------------------------
  // La portada rota entre las fotos de los eventos destacados. Solo cambia la
  // fotografia de fondo: el titular sigue siendo el del proximo evento, que es
  // la informacion con plazo. Sin JS (o con prefers-reduced-motion) se queda
  // la primera capa, que ya viene con `.activa` desde la plantilla.
  var heroFondos = document.querySelectorAll(".hero-foto__fondo");
  var heroPuntos = document.querySelectorAll(".hero-foto__punto");
  if (heroFondos.length > 1) {
    var heroActual = 0;
    var heroTimer = null;

    function heroMostrar(i) {
      heroActual = (i % heroFondos.length + heroFondos.length) % heroFondos.length;
      heroFondos.forEach(function (capa, n) {
        capa.classList.toggle("activa", n === heroActual);
      });
      heroPuntos.forEach(function (punto, n) {
        punto.setAttribute("aria-current", n === heroActual ? "true" : "false");
      });
    }

    function heroArranca() {
      if (prefiereMenosMovimiento || heroTimer) return;
      heroTimer = setInterval(function () { heroMostrar(heroActual + 1); }, 6000);
    }
    function heroPara() {
      if (heroTimer) { clearInterval(heroTimer); heroTimer = null; }
    }

    heroPuntos.forEach(function (punto, n) {
      punto.addEventListener("click", function () {
        heroPara();          // si el visitante elige, manda el visitante
        heroMostrar(n);
      });
    });

    // Pausa mientras el puntero esta encima o el foco esta dentro: el fondo
    // no debe cambiar bajo la mano de quien esta leyendo el titular.
    var hero = document.querySelector(".hero-foto");
    if (hero) {
      hero.addEventListener("mouseenter", heroPara);
      hero.addEventListener("mouseleave", heroArranca);
      hero.addEventListener("focusin", heroPara);
    }
    // Ni cuando la pestaña esta en segundo plano.
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) heroPara(); else heroArranca();
    });

    heroArranca();
  }

  // --- 5. Volver arriba ----------------------------------------------------
  var arriba = document.getElementById("top-link-block");
  if (arriba) {
    window.addEventListener("scroll", function () {
      arriba.classList.toggle("visible", window.scrollY > 600);
    }, { passive: true });
  }

  // --- 4. Revelado al hacer scroll ----------------------------------------
  var elementos = document.querySelectorAll(".reveal");
  if (prefiereMenosMovimiento || !("IntersectionObserver" in window) || !elementos.length) {
    return; // sin .js-anim los .reveal quedan visibles de entrada (ver CSS)
  }

  document.documentElement.classList.add("js-anim");

  var observador = new IntersectionObserver(function (entradas) {
    entradas.forEach(function (entrada) {
      if (entrada.isIntersecting) {
        entrada.target.classList.add("mostrar");
        observador.unobserve(entrada.target);
      }
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -60px 0px" });

  elementos.forEach(function (el) { observador.observe(el); });
})();
