(() => {
    const ready = (fn) => document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", fn) : fn();
    ready(() => {
        document.body.insertAdjacentHTML("afterbegin", '<div class="mg-progress" aria-hidden="true"></div>');
        const progress = document.querySelector(".mg-progress");
        const updateProgress = () => {
            const max = document.documentElement.scrollHeight - window.innerHeight;
            progress.style.width = `${max > 0 ? (window.scrollY / max) * 100 : 0}%`;
        };
        updateProgress();
        window.addEventListener("scroll", updateProgress, { passive: true });

        document.querySelectorAll("button, .btn, a").forEach((el) => {
            el.classList.add("mg-ripple");
            el.addEventListener("click", (event) => {
                const rect = el.getBoundingClientRect();
                const wave = document.createElement("span");
                wave.className = "mg-wave";
                wave.style.left = `${event.clientX - rect.left}px`;
                wave.style.top = `${event.clientY - rect.top}px`;
                el.appendChild(wave);
                window.setTimeout(() => wave.remove(), 650);
            });
        });

        const revealTargets = document.querySelectorAll("[data-motion], .info-box, .choose-card, .price-card, .objetivo-card, .nutrition-card, .accept-card, .box, .dashboard-card, .profile-card");
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("mg-visible");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });
        revealTargets.forEach((target, index) => {
            target.style.transitionDelay = `${Math.min(index * 45, 220)}ms`;
            observer.observe(target);
        });

        document.querySelectorAll(".objetivo-card, .price-card, .choose-card").forEach((card) => {
            card.addEventListener("pointermove", (event) => {
                const rect = card.getBoundingClientRect();
                const x = (event.clientX - rect.left) / rect.width - 0.5;
                const y = (event.clientY - rect.top) / rect.height - 0.5;
                card.style.transform = `perspective(900px) rotateX(${(-y * 5.5).toFixed(2)}deg) rotateY(${(x * 5.5).toFixed(2)}deg) translateY(-7px) scale(1.015)`;
            });
            card.addEventListener("pointerleave", () => {
                card.style.transform = "";
            });
        });

        document.querySelectorAll(".price-card:nth-child(3)").forEach((card) => {
            card.addEventListener("pointerenter", () => {
                for (let i = 0; i < 9; i += 1) {
                    const spark = document.createElement("span");
                    spark.className = "spark-burst";
                    spark.style.left = `${18 + Math.random() * 72}%`;
                    spark.style.top = `${12 + Math.random() * 72}%`;
                    spark.style.setProperty("--spark-x", `${(Math.random() - 0.5) * 80}px`);
                    spark.style.setProperty("--spark-y", `${(Math.random() - 0.5) * 70}px`);
                    card.appendChild(spark);
                    window.setTimeout(() => spark.remove(), 900);
                }
            });
        });

        document.querySelectorAll("[data-count-to]").forEach((counter) => {
            const target = Number(counter.dataset.countTo || 0);
            let start = null;
            const run = (time) => {
                start ??= time;
                const pct = Math.min((time - start) / 900, 1);
                counter.textContent = Math.round(target * pct);
                if (pct < 1) requestAnimationFrame(run);
            };
            requestAnimationFrame(run);
        });

        const fileInput = document.querySelector('input[type="file"][name="foto"]');
        if (fileInput) {
            fileInput.addEventListener("change", () => {
                const file = fileInput.files && fileInput.files[0];
                const image = document.querySelector(".profile-visual img");
                if (file && image) image.src = URL.createObjectURL(file);
            });
        }
    });
})();