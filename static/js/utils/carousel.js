/**
 * Reusable horizontal carousel with autoplay, drag, and correct end-offset.
 */

function getSlideStep(track, slides) {
  if (!slides.length) return 0;
  const slideWidth = slides[0].getBoundingClientRect().width;
  const gap = parseFloat(getComputedStyle(track).gap) || 0;
  return slideWidth + gap;
}

function getMaxOffset(viewport, track) {
  return Math.max(0, track.scrollWidth - viewport.clientWidth);
}

function getOffsetForIndex(index, viewport, track, slides) {
  const step = getSlideStep(track, slides);
  const raw = step * index;
  return Math.min(raw, getMaxOffset(viewport, track));
}

export function initCarousel(root) {
  const viewport = root.querySelector("[data-carousel-viewport]");
  const track = root.querySelector("[data-carousel-track]");
  const dotsContainer = root.querySelector("[data-carousel-dots]");
  const progressBar = root.querySelector("[data-carousel-progress]");
  const prevBtn = root.querySelector("[data-carousel-prev]");
  const nextBtn = root.querySelector("[data-carousel-next]");
  const slides = [...track.querySelectorAll("[data-carousel-slide]")];

  if (!viewport || !track || slides.length === 0) return null;

  const autoplayMs = Number.parseInt(root.dataset.carouselAutoplay || "4000", 10);
  const loop = root.dataset.carouselLoop !== "false";
  const highlightActive = root.dataset.carouselHighlight !== "false";

  let currentIndex = 0;
  let autoplayTimer = null;
  let progressTimer = null;
  let progressStart = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragCurrentX = 0;
  let dragBaseOffset = 0;

  function updateSlideStates() {
    if (!highlightActive) return;

    slides.forEach((slide, i) => {
      slide.classList.toggle("is-active", i === currentIndex);
      slide.classList.toggle("is-near", Math.abs(i - currentIndex) === 1);
    });
  }

  function updateDots() {
    if (!dotsContainer) return;

    dotsContainer.querySelectorAll("[data-carousel-dot]").forEach((dot, i) => {
      const isActive = i === currentIndex;
      dot.classList.toggle("is-active", isActive);
      dot.setAttribute("aria-selected", String(isActive));
    });
  }

  function applyTransform(offset, animate = true) {
    track.style.transition = animate && !isDragging
      ? ""
      : "none";
    track.style.transform = `translateX(-${offset}px)`;
  }

  function goToSlide(index, animate = true) {
    if (!slides.length) return;

    if (loop) {
      currentIndex = ((index % slides.length) + slides.length) % slides.length;
    } else {
      currentIndex = Math.max(0, Math.min(index, slides.length - 1));
    }

    const offset = getOffsetForIndex(currentIndex, viewport, track, slides);
    applyTransform(offset, animate);
    updateSlideStates();
    updateDots();
    resetProgress();
  }

  function goNext() {
    if (loop) {
      goToSlide(currentIndex + 1);
      return;
    }

    const maxOffset = getMaxOffset(viewport, track);
    const currentOffset = getOffsetForIndex(currentIndex, viewport, track, slides);
    const step = getSlideStep(track, slides);

    if (currentOffset >= maxOffset - 1) {
      goToSlide(0);
    } else {
      goToSlide(currentIndex + 1);
    }
  }

  function goPrev() {
    if (loop) {
      goToSlide(currentIndex - 1);
      return;
    }

    if (currentIndex <= 0) {
      goToSlide(slides.length - 1);
    } else {
      goToSlide(currentIndex - 1);
    }
  }

  function buildDots() {
    if (!dotsContainer) return;
    dotsContainer.innerHTML = "";

    slides.forEach((_, i) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "med-carousel__dot";
      dot.dataset.carouselDot = String(i);
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-label", `Go to slide ${i + 1}`);
      dot.addEventListener("click", () => {
        goToSlide(i);
        resetAutoplay();
      });
      dotsContainer.appendChild(dot);
    });

    updateDots();
  }

  function resetProgress() {
    if (!progressBar || !autoplayMs) return;
    if (progressTimer) cancelAnimationFrame(progressTimer);
    progressStart = performance.now();
    progressBar.style.width = "0%";

    function tick(now) {
      const elapsed = now - progressStart;
      const pct = Math.min((elapsed / autoplayMs) * 100, 100);
      progressBar.style.width = `${pct}%`;
      if (pct < 100) {
        progressTimer = requestAnimationFrame(tick);
      }
    }

    progressTimer = requestAnimationFrame(tick);
  }

  function resetAutoplay() {
    if (!autoplayMs) return;
    if (autoplayTimer) clearInterval(autoplayTimer);
    autoplayTimer = setInterval(goNext, autoplayMs);
    resetProgress();
  }

  function pauseAutoplay() {
    if (autoplayTimer) clearInterval(autoplayTimer);
    if (progressTimer) cancelAnimationFrame(progressTimer);
    autoplayTimer = null;
  }

  function onDragStart(clientX) {
    isDragging = true;
    dragStartX = clientX;
    dragCurrentX = clientX;
    dragBaseOffset = getOffsetForIndex(currentIndex, viewport, track, slides);
    root.classList.add("is-dragging");
    pauseAutoplay();
  }

  function onDragMove(clientX) {
    if (!isDragging) return;
    dragCurrentX = clientX;
    const delta = dragStartX - dragCurrentX;
    const maxOffset = getMaxOffset(viewport, track);
    const nextOffset = Math.max(0, Math.min(dragBaseOffset + delta, maxOffset));
    applyTransform(nextOffset, false);
  }

  function onDragEnd() {
    if (!isDragging) return;
    isDragging = false;
    root.classList.remove("is-dragging");

    const delta = dragStartX - dragCurrentX;
    const step = getSlideStep(track, slides);
    const threshold = step * 0.18;

    if (delta > threshold) {
      goToSlide(currentIndex + 1);
    } else if (delta < -threshold) {
      goToSlide(currentIndex - 1);
    } else {
      goToSlide(currentIndex);
    }

    resetAutoplay();
  }

  viewport.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    onDragStart(e.clientX);
  });

  window.addEventListener("mousemove", (e) => onDragMove(e.clientX));
  window.addEventListener("mouseup", onDragEnd);

  viewport.addEventListener("touchstart", (e) => {
    onDragStart(e.touches[0].clientX);
  }, { passive: true });

  viewport.addEventListener("touchmove", (e) => {
    onDragMove(e.touches[0].clientX);
  }, { passive: true });

  viewport.addEventListener("touchend", onDragEnd);

  prevBtn?.addEventListener("click", () => {
    goPrev();
    resetAutoplay();
  });

  nextBtn?.addEventListener("click", () => {
    goNext();
    resetAutoplay();
  });

  slides.forEach((slide, i) => {
    slide.addEventListener("click", () => {
      if (Math.abs(dragStartX - dragCurrentX) > 8) return;
      if (i !== currentIndex) {
        goToSlide(i);
        resetAutoplay();
      }
    });
  });

  root.addEventListener("mouseenter", pauseAutoplay);
  root.addEventListener("mouseleave", resetAutoplay);

  buildDots();
  goToSlide(0, false);
  resetAutoplay();

  let resizeTimer;
  const onResize = () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => goToSlide(currentIndex, false), 150);
  };
  window.addEventListener("resize", onResize);

  return {
    goTo: goToSlide,
    pause: pauseAutoplay,
    resume: resetAutoplay,
    destroy() {
      pauseAutoplay();
      window.removeEventListener("resize", onResize);
    },
  };
}

export function initCarousels(selector = "[data-carousel]") {
  return [...document.querySelectorAll(selector)].map((root) => initCarousel(root));
}
