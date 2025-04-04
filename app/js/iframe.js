export default {
  template: '<iframe :src="src" :style="style" frameborder="0" allowfullscreen></iframe>',
  props: {
    src: {
      type: String,
      required: true
    },
    width: {
      type: String,
      default: '100%'
    },
    height: {
      type: String,
      default: '100%'
    }
  },
  mounted() {
    console.log("Iframe mounted");
  },
  computed: {
    style() {
      return {
        width: this.width,
        height: this.height,
        border: 'none'
      }
    }
  }
};