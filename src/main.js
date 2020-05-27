import Vue from 'vue';

// import App from './Bird.vue';
// import App from './Square.vue';
import App from './TicTacToe.vue';

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({ render: (h) => h(App) }).$mount('#app');
