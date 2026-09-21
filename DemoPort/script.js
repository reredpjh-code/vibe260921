// 카드 등장 애니메이션
const revealTargets = document.querySelectorAll('.skill-card, .project-card, .link-card');

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 }
);

revealTargets.forEach((el) => {
  el.classList.add('reveal');
  revealObserver.observe(el);
});
