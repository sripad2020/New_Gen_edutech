// This is the vanilla-tilt.js library content
// You can download it from https://github.com/micku7zu/vanilla-tilt.js
// Or use CDN: https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.0/vanilla-tilt.min.js

// For this example, I'll include a basic implementation
class VanillaTilt {
    constructor(element, settings = {}) {
        this.element = element;
        this.settings = {
            max: 15,
            speed: 400,
            glare: true,
            "max-glare": 0.2,
            ...settings
        };

        this.init();
    }

    init() {
        this.width = null;
        this.height = null;
        this.left = null;
        this.top = null;
        this.transitionTimeout = null;
        this.updateCall = null;

        this.element.style.transform = "perspective(1000px)";
        this.element.style.transformStyle = "preserve-3d";
        this.element.style.backfaceVisibility = "hidden";

        this.glare = this.settings.glare;
        if (this.glare) {
            this.prepareGlare();
        }

        this.updateInitialPosition();
        this.bindEvents();
    }

    prepareGlare() {
        const glarePrerender = this.settings["glare-prerender"];

        if (!glarePrerender) {
            const jsGlare = document.createElement("div");
            jsGlare.classList.add("js-tilt-glare");

            const jsGlareInner = document.createElement("div");
            jsGlareInner.classList.add("js-tilt-glare-inner");

            jsGlare.appendChild(jsGlareInner);
            this.element.appendChild(jsGlare);
        }

        this.glareElementWrapper = this.element.querySelector(".js-tilt-glare");
        this.glareElement = this.element.querySelector(".js-tilt-glare-inner");

        if (!this.glareElementWrapper || !this.glareElement) {
            return;
        }

        this.glareElementWrapper.style.position = "absolute";
        this.glareElementWrapper.style.top = "0";
        this.glareElementWrapper.style.left = "0";
        this.glareElementWrapper.style.width = "100%";
        this.glareElementWrapper.style.height = "100%";
        this.glareElementWrapper.style.overflow = "hidden";
        this.glareElementWrapper.style.pointerEvents = "none";
        this.glareElementWrapper.style.borderRadius = "inherit";

        this.glareElement.style.position = "absolute";
        this.glareElement.style.top = "50%";
        this.glareElement.style.left = "50%";
        this.glareElement.style.transform = "translate(-50%, -50%) rotate(180deg)";
        this.glareElement.style.width = `${(this.element.offsetWidth * 2)}px`;
        this.glareElement.style.height = `${(this.element.offsetHeight * 2)}px`;
        this.glareElement.style.background = "linear-gradient(0deg, rgba(255,255,255,0) 0%, rgba(255,255,255,1) 100%)";
        this.glareElement.style.transition = `all ${this.settings.speed}ms ease-out`;
        this.glareElement.style.opacity = "0";
        this.glareElement.style.pointerEvents = "none";
    }

    updateInitialPosition() {
        const rect = this.element.getBoundingClientRect();

        this.width = this.element.offsetWidth;
        this.height = this.element.offsetHeight;
        this.left = rect.left;
        this.top = rect.top;
    }

    bindEvents() {
        this.onMouseEnter = this.onMouseEnter.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
        this.onMouseLeave = this.onMouseLeave.bind(this);
        this.onWindowResize = this.onWindowResize.bind(this);

        this.element.addEventListener("mouseenter", this.onMouseEnter);
        this.element.addEventListener("mousemove", this.onMouseMove);
        this.element.addEventListener("mouseleave", this.onMouseLeave);
        window.addEventListener("resize", this.onWindowResize);
    }

    onMouseEnter() {
        this.updateInitialPosition();
        this.element.style.willChange = "transform";
        this.setTransition();
    }

    onMouseMove(event) {
        if (this.updateCall !== null) {
            cancelAnimationFrame(this.updateCall);
        }

        this.updateCall = requestAnimationFrame(() => this.update(event));
    }

    onMouseLeave() {
        this.setTransition();

        if (this.settings.reset) {
            requestAnimationFrame(() => {
                this.element.style.transform = `perspective(${this.settings.perspective}px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;

                if (this.glare) {
                    this.glareElement.style.opacity = "0";
                }
            });
        }
    }

    onWindowResize() {
        this.updateInitialPosition();
    }

    setTransition() {
        clearTimeout(this.transitionTimeout);
        this.element.style.transition = `${this.settings.speed}ms all ease-out`;
        if (this.glare) this.glareElement.style.transition = `${this.settings.speed}ms all ease-out`;

        this.transitionTimeout = setTimeout(() => {
            this.element.style.transition = "";
            if (this.glare) this.glareElement.style.transition = "";
        }, this.settings.speed);
    }

    update(event) {
        const clientX = event.clientX || event.touches[0].clientX;
        const clientY = event.clientY || event.touches[0].clientY;

        const relativeX = clientX - this.left;
        const relativeY = clientY - this.top;

        const centerX = this.width / 2;
        const centerY = this.height / 2;

        const posX = relativeX - centerX;
        const posY = relativeY - centerY;

        const x = posX / centerX;
        const y = posY / centerY;

        this.updateTransformation(x, y);
    }

    updateTransformation(x, y) {
        const tiltX = (this.settings.max / 2 - x * this.settings.max).toFixed(2);
        const tiltY = (y * this.settings.max - this.settings.max / 2).toFixed(2);

        this.element.style.transform = `perspective(${this.settings.perspective}px) rotateX(${tiltY}deg) rotateY(${tiltX}deg) scale3d(${this.settings.scale}, ${this.settings.scale}, ${this.settings.scale})`;

        if (this.glare) {
            this.glareElement.style.transform = `translate(-50%, -50%) rotate(180deg)`;
            this.glareElement.style.opacity = `${Math.max(Math.abs(x), Math.abs(y)) * this.settings["max-glare"]}`;
        }
    }
}

// Initialize Tilt.js
document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('[data-tilt]');
    elements.forEach(element => {
        new VanillaTilt(element, {
            max: 5,
            speed: 1000,
            glare: true,
            "max-glare": 0.2,
            perspective: 1000,
            scale: 1.02
        });
    });
});
