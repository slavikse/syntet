import Vue from 'vue';

// import App from './Square.vue';
import App from './TicTacToe.vue';
// import App from './Checkers.vue';

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({ render: h => h(App) }).$mount('#app');
