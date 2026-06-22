(() => {
  'use strict';
  if (window.__kozeniAnalyticsLoaded) return;
  window.__kozeniAnalyticsLoaded = true;

  const gaId = "G-V140MZBPKB";
  const clarityId = "wmurko5bi1";

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag('js', new Date());
  window.gtag('config', gaId);

  const ga = document.createElement('script');
  ga.async = true;
  ga.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(gaId)}`;
  document.head.appendChild(ga);

  window.clarity = window.clarity || function clarity() {
    (window.clarity.q = window.clarity.q || []).push(arguments);
  };
  const clarity = document.createElement('script');
  clarity.async = true;
  clarity.src = `https://www.clarity.ms/tag/${clarityId}`;
  document.head.appendChild(clarity);
})();
