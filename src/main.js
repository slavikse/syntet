import Vue from 'vue';

// import 'aframe';
// import 'aframe-extras';
// import 'aframe-physics-system';

// import Car from './Car.vue';
// import Maze from './Maze.vue';
import Square from './Square.vue';

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({ render: h => h(Square) }).$mount('#app');
