export default {
  template: "<div><slot></slot></div>",
  mounted() {
    const initial_path = window.location.pathname;
    // Triggered when user clicks forward/back, or on JS navigate event.
    window.addEventListener("popstate", (event) => {
      this.$emit("switch_tab", event.state?.page || initial_path);
    });

    // Page initialization: once socket is available, trigger tabmanager.py
    // to navigate to the  correct page.
    const connectInterval = setInterval(async () => {
      if (window.socket.id === undefined) return;
      if (window.location.pathname === '/') {
          history.replaceState(null, '', '/p/home')
      }
      this.$emit("switch_tab", window.location.pathname);
      clearInterval(connectInterval);
    }, 10);

    document.body.addEventListener('click', event => {
      let targetLink = event.target.closest('a.soft-link');

      if (targetLink) {
          event.preventDefault();
          const path = targetLink.pathname;
          history.pushState({page: path}, "", path);

          try {
             this.$emit("switch_tab", window.location.pathname);
          } catch (error) {
              console.error("Error handling link click:", error);
              window.location.href = targetLink.href; // Fallback
          }
      }
    });

  },
  props: {},
};
