// Mobile nav toggle
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });

    // Mobile dropdown toggles
    document.querySelectorAll('.nav-dropdown > a').forEach(a => {
      a.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          a.parentElement.classList.toggle('open');
        }
      });
    });

    // Close menu on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('nav')) {
        links.classList.remove('open');
        document.querySelectorAll('.nav-dropdown').forEach(d => d.classList.remove('open'));
      }
    });
  }
});

// Share the State of the Society address (used on foundation-day pages)
function shareAddress() {
  var url = window.location.href.split('#')[0] + '#state-of-the-society';
  if (navigator.share) {
    navigator.share({ title: document.title, url: url }).catch(() => {});
  } else if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => {
      window.alert('Link copied to clipboard.');
    });
  } else {
    window.prompt('Copy this link:', url);
  }
}
