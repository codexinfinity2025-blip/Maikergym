(function () {
    "use strict";

    function formatTime(totalSeconds) {
        const safeSeconds = Math.max(0, Number(totalSeconds) || 0);
        const minutes = Math.floor(safeSeconds / 60);
        const seconds = Math.floor(safeSeconds % 60);

        return (
            String(minutes).padStart(2, "0")
            + ":"
            + String(seconds).padStart(2, "0")
        );
    }

    function startRestTimer() {
        const timer = document.getElementById("restTimer");

        if (!timer) {
            return;
        }

        let remaining = Number(timer.dataset.seconds || 0);
        let reloadScheduled = false;

        const update = function () {
            timer.textContent = formatTime(remaining);

            if (remaining <= 0) {
                if (!reloadScheduled) {
                    reloadScheduled = true;
                    window.setTimeout(function () {
                        window.location.reload();
                    }, 600);
                }

                return;
            }

            remaining -= 1;
        };

        update();
        window.setInterval(update, 1000);
    }

    function startSeriesTimer() {
        const timer = document.getElementById("seriesTimer");

        if (!timer) {
            return;
        }

        const startedAt = Date.parse(timer.dataset.started);
        const durationInput = document.getElementById("durationInput");

        if (Number.isNaN(startedAt)) {
            return;
        }

        const update = function () {
            const elapsed = Math.max(
                0,
                Math.floor((Date.now() - startedAt) / 1000)
            );

            timer.textContent = formatTime(elapsed);

            if (durationInput) {
                durationInput.value = String(elapsed);
            }
        };

        update();
        window.setInterval(update, 1000);
    }

    function configureSteppers() {
        const buttons = document.querySelectorAll(
            "[data-stepper-target]"
        );

        buttons.forEach(function (button) {
            button.addEventListener("click", function () {
                const target = document.getElementById(
                    button.dataset.stepperTarget
                );

                if (!target) {
                    return;
                }

                const step = Number(button.dataset.step || 1);
                const current = Number(target.value || 0);
                const minimum = Number(target.min || 0);
                const nextValue = Math.max(minimum, current + step);

                target.value = String(nextValue);
            });
        });
    }

    function preventDoubleSubmit() {
        const forms = document.querySelectorAll(
            ".player-action-form"
        );

        forms.forEach(function (form) {
            form.addEventListener("submit", function () {
                const button = form.querySelector(
                    "button[type='submit']"
                );

                if (!button) {
                    return;
                }

                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = "Guardando...";
            });
        });
    }

    function hideMessagesLater() {
        const messages = document.querySelector(".player-messages");

        if (!messages) {
            return;
        }

        window.setTimeout(function () {
            messages.style.opacity = "0";
            messages.style.pointerEvents = "none";
        }, 4200);
    }

    document.addEventListener("DOMContentLoaded", function () {
        startRestTimer();
        startSeriesTimer();
        configureSteppers();
        preventDoubleSubmit();
        hideMessagesLater();
    });
}());
