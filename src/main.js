import Vue from 'vue';

// import 'aframe';
// import 'aframe-extras';
// import 'aframe-physics-system';

// import App from './Car.vue';
// import App from './Maze.vue';
import App from './Square.vue';
// import App from './TF_1.vue';

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({ render: h => h(App) }).$mount('#app');
