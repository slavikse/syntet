import Vue from 'vue';

// import App from './App.vue';
import Car from './Car.vue';
import store from './store';

Vue.config.productionTip = false;

new Vue({
  store,
  render: h => h(Car),
}).$mount('#app');
